from django.db import models
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.http import JsonResponse
from django.db.models import Min, Max, Avg, Count
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import timedelta, datetime
from core.models import Actividad, ActividadProgreso, DailyMood, Profile
import json


@login_required
def marcar_scratch(request):

    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "POST required"})

    profile, _ = Profile.objects.get_or_create(user=request.user)

    profile.last_scratch_date = timezone.now().date()
    profile.save()

    return JsonResponse({"ok": True})

@login_required
def eliminar_actividad_ajax(request, id):

    if request.method == "POST":

        actividad = get_object_or_404(
            Actividad,
            id=id,
            usuario=request.user 
        )

        actividad.delete()

        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False})

def ruleta(request):

    if request.user.is_staff:
        return HttpResponseForbidden("No tienes acceso a la ruleta")

    actividades = Actividad.objects.filter(
        usuario=request.user,
        estado__in=["PENDIENTE", "PROGRESO"]
    ).values("id", "titulo")

    data = list(actividades)

    return render(request, "core/ruleta.html", {
        "actividades_json": json.dumps(data)
    })

def normalizar_estado(valor):
    if not valor:
        return ""
    return str(valor).strip().upper()


MESES_ES = [
    "enero",
    "febrero",
    "marzo",
    "abril",
    "mayo",
    "junio",
    "julio",
    "agosto",
    "septiembre",
    "octubre",
    "noviembre",
    "diciembre",
]


def formatear_fecha_es(fecha):
    return f"{fecha.day} de {MESES_ES[fecha.month - 1]}"


def obtener_inicio_semana(fecha):
    return fecha - timedelta(days=fecha.weekday())


def construir_opciones_semanales(user):
    mood_queryset = DailyMood.objects.all() if usuario_es_admin(user) else DailyMood.objects.filter(user=user)
    limites = mood_queryset.aggregate(
        inicio=Min("date"),
        fin=Max("date"),
    )

    inicio = limites["inicio"]
    fin = limites["fin"]

    if not inicio or not fin:
        hoy = timezone.localdate()
        inicio = obtener_inicio_semana(hoy)
        fin = inicio

    semana_actual = obtener_inicio_semana(inicio)
    ultima_semana = obtener_inicio_semana(fin)
    opciones = []

    while semana_actual <= ultima_semana:
        fin_semana = semana_actual + timedelta(days=6)
        opciones.append({
            "start": semana_actual,
            "end": fin_semana,
            "start_iso": semana_actual.isoformat(),
            "end_iso": fin_semana.isoformat(),
            "label": f"Semana del {formatear_fecha_es(semana_actual)} al {formatear_fecha_es(fin_semana)}",
        })
        semana_actual += timedelta(days=7)

    return opciones or [{
        "start": inicio,
        "end": inicio + timedelta(days=6),
        "start_iso": inicio.isoformat(),
        "end_iso": (inicio + timedelta(days=6)).isoformat(),
        "label": f"Semana del {formatear_fecha_es(inicio)} al {formatear_fecha_es(inicio + timedelta(days=6))}",
    }]


def obtener_semana_actual(reference_date=None):
    today = reference_date or timezone.localdate()
    inicio = obtener_inicio_semana(today)
    return [inicio + timedelta(days=i) for i in range(7)]


def construir_tracking_semanal(user, reference_date=None):
    week_dates = obtener_semana_actual(reference_date)
    weekday_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    mood_queryset = DailyMood.objects.all() if usuario_es_admin(user) else DailyMood.objects.filter(user=user)
    mood_by_date = {
        item["date"]: item["average_stress"]
        for item in mood_queryset.filter(date__range=(week_dates[0], week_dates[-1]))
            .values("date")
            .annotate(average_stress=Avg("stress_level"))
    }

    week_days = []
    values = []

    for day in week_dates:
        stars = round(mood_by_date.get(day, 0) or 0, 1)
        values.append(stars)

        week_days.append({
            "date": day,
            "iso": day.isoformat(),
            "label": weekday_labels[day.weekday()],
            "display": day.strftime("%d/%m"),
            "stars": stars,
        })

    filled_values = [value for value in values if value > 0]
    average = round(sum(filled_values) / len(filled_values), 1) if filled_values else 0

    if average >= 4:
        summary = "Semana muy ocupada"
    elif average >= 2.5:
        summary = "Semana moderada"
    elif average > 0:
        summary = "Semana ligera"
    else:
        summary = "Sin tracking todavía"

    return week_days, average, summary


def construir_datos_tracking_semanal(user, reference_date=None):
    week_days, average, summary = construir_tracking_semanal(user, reference_date)

    return {
        "week_days": week_days,
        "labels": [day["label"] for day in week_days],
        "data": [day["stars"] for day in week_days],
        "average": average,
        "summary": summary,
        "week_start": week_days[0]["date"],
        "week_end": week_days[-1]["date"],
        "week_label": f"Semana del {formatear_fecha_es(week_days[0]['date'])} al {formatear_fecha_es(week_days[-1]['date'])}",
    }


def obtener_actividad_con_progreso(actividad, user):
    progreso_obj = ActividadProgreso.objects.filter(actividad=actividad, usuario=user).first()

    return {
        "actividad": actividad,
        "progreso": progreso_obj.progreso if progreso_obj else 0,
        "nota": progreso_obj.nota if progreso_obj else "",
        "actualizado_en": progreso_obj.actualizado_en if progreso_obj else None,
    }


def usuario_es_admin(user):
    return bool(user.is_authenticated and (user.is_superuser or user.groups.filter(name="Admin").exists()))


def obtener_queryset_actividades(user):
    actividades = Actividad.objects.select_related("usuario")

    if not usuario_es_admin(user):
        actividades = actividades.filter(usuario=user)

    return actividades.order_by("-created_at", "-fecha")


def serializar_actividad(actividad, incluir_propietario=False):
    try:
        progreso_obj = actividad.progreso_privado
    except ActividadProgreso.DoesNotExist:
        progreso_obj = None

    actividad_dict = {
        "id": actividad.id,
        "titulo": actividad.titulo,
        "tipo": actividad.tipo,
        "estado": normalizar_estado(actividad.estado),
        "progreso": progreso_obj.progreso if progreso_obj else 0,
    }

    if incluir_propietario:
        actividad_dict["propietario"] = actividad.usuario.get_full_name() or actividad.usuario.username

    return actividad_dict


def construir_contexto_tablero(request):
    es_admin = usuario_es_admin(request.user)

    actividades = obtener_queryset_actividades(request.user).select_related("categoria")

    pendientes = actividades.filter(estado="PENDIENTE")
    progreso = actividades.filter(estado="PROGRESO")
    completadas = actividades.filter(estado="COMPLETADO")

    total = actividades.count()
    pendientes_count = pendientes.count()
    completadas_count = completadas.count()
    porcentaje = round((completadas_count / total) * 100) if total > 0 else 0

    return {
        "es_admin": es_admin,
        "rol_label": "Admin" if es_admin else "Usuario",
        "tareas_total": total,
        "pendientes_tareas": pendientes,
        "progreso_tareas": progreso,
        "completadas_tareas": completadas,
        "solo_lectura": es_admin,
        "puede_crear": not es_admin,
        "stats": {
            "total": total,
            "pendientes": pendientes_count,
            "completadas": completadas_count,
        },
        "porcentaje": porcentaje,
    }


# ======================
# LANDING
# ======================
def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'core/landing.html')


# ======================
# CRUD ACTIVIDADES
# ======================
@login_required
def crear_actividad(request):
    if usuario_es_admin(request.user):
        return HttpResponseForbidden("Los administradores no pueden crear tareas desde esta vista.")

    if request.method == 'POST':
        titulo = request.POST.get('titulo', '').strip()
        tipo = request.POST.get('tipo', '').strip()

        if titulo and tipo:
            Actividad.objects.create(
                usuario=request.user,
                titulo=titulo,
                tipo=tipo,
                estado="PENDIENTE",
                fecha=timezone.localdate(),
            )

    return redirect('actividades')


@login_required
def toggle_actividad(request, id):
    if usuario_es_admin(request.user):
        return HttpResponseForbidden("Los administradores no pueden modificar tareas.")

    actividad = get_object_or_404(Actividad, id=id, usuario=request.user)

    if actividad.estado == "PENDIENTE":
        actividad.estado = "PROGRESO"
    elif actividad.estado == "PROGRESO":
        actividad.estado = "COMPLETADO"
    else:
        actividad.estado = "PENDIENTE"

    actividad.save(update_fields=["estado"])

    return redirect('dashboard')


@login_required
def eliminar_actividad(request, id):
    if usuario_es_admin(request.user):
        return HttpResponseForbidden("Los administradores no pueden modificar tareas.")

    actividad = get_object_or_404(Actividad, id=id, usuario=request.user)
    actividad.delete()

    return redirect('dashboard')

def obtener_contexto_dashboard(request):
    es_admin = usuario_es_admin(request.user)
    actividades = [
        serializar_actividad(actividad, incluir_propietario=es_admin)
        for actividad in obtener_queryset_actividades(request.user)
    ]

    pendientes = [a for a in actividades if a["estado"] == "PENDIENTE"]
    progreso = [a for a in actividades if a["estado"] == "PROGRESO"]
    completadas = [a for a in actividades if a["estado"] == "COMPLETADO"]

    week_days, _, _ = construir_tracking_semanal(request.user)

    total = len(actividades)
    pendientes_count = len(pendientes)
    completadas_count = len(completadas)

    porcentaje = round((completadas_count / total) * 100) if total > 0 else 0

    return {
        "es_admin": es_admin,
        "rol_label": "Admin" if es_admin else "Usuario",
        "solo_lectura": es_admin,
        "puede_crear": not es_admin,
        "pendientes": pendientes,
        "progreso": progreso,
        "completadas": completadas,
        "stats": {
            "total": total,
            "pendientes": pendientes_count,
            "completadas": completadas_count,
        },
        "porcentaje": porcentaje,
        "week_days": week_days,
        "star_range": [1, 2, 3, 4, 5],
    }


# ======================
# DASHBOARD
# ======================

@login_required
def dashboard(request):

    contexto = construir_contexto_tablero(request)

    profile, _ = Profile.objects.get_or_create(user=request.user)

    hoy = timezone.now().date()

    contexto["mostrar_scratch"] = profile.last_scratch_date != hoy

    return render(request, "core/dashboard.html", contexto)


# ======================
# MOVER ACTIVIDAD (DRAG & DROP)
# ======================
@login_required
def mover_actividad(request):
    if request.method == "POST":
        if usuario_es_admin(request.user):
            return JsonResponse({"status": "error", "message": "Los administradores no pueden modificar tareas."}, status=403)

        actividad_id = request.POST.get("id")
        nuevo_estado = normalizar_estado(request.POST.get("estado"))

        actividad = get_object_or_404(Actividad, id=actividad_id, usuario=request.user)
        estados_validos = {estado for estado, _ in Actividad.ESTADOS}

        if nuevo_estado not in estados_validos:
            return JsonResponse({"status": "error", "message": "Estado inválido"}, status=400)

        actividad.estado = nuevo_estado
        actividad.save(update_fields=["estado"])

        return JsonResponse({"status": "ok"})


# ======================
# API TABLERO (FRONTEND DRAG & GRAPH READY)
# ======================
@login_required
def api_tablero(request):
    es_admin = usuario_es_admin(request.user)
    actividades = [
        serializar_actividad(actividad, incluir_propietario=es_admin)
        for actividad in obtener_queryset_actividades(request.user)
    ]

    pendientes = [actividad for actividad in actividades if actividad["estado"] == "PENDIENTE"]
    progreso = [actividad for actividad in actividades if actividad["estado"] == "PROGRESO"]
    completadas = [actividad for actividad in actividades if actividad["estado"] == "COMPLETADO"]

    total = len(actividades)
    completadas_count = len(completadas)
    pendientes_count = len(pendientes)
    porcentaje = round((completadas_count / total) * 100) if total > 0 else 0

    response = JsonResponse({
        "pendientes": pendientes,
        "progreso": progreso,
        "completadas": completadas,
        "solo_lectura": es_admin,
        "stats": {
            "total": total,
            "pendientes": pendientes_count,
            "completadas": completadas_count,
            "porcentaje": porcentaje
        }
    })

    # evita cache (IMPORTANTE para drag & drop)
    response["Cache-Control"] = "no-store"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"

    return response


@login_required
def tareas_filtradas(request, tipo):
    es_admin = usuario_es_admin(request.user)
    data = [
        serializar_actividad(actividad, incluir_propietario=es_admin)
        for actividad in obtener_queryset_actividades(request.user)
    ]

    if tipo == "total":
        resultado = data

    elif tipo == "pendientes":
        resultado = [x for x in data if x["estado"] == "PENDIENTE"]

    elif tipo == "completadas":
        resultado = [x for x in data if x["estado"] == "COMPLETADO"]

    else:
        resultado = []

    return JsonResponse(resultado, safe=False)


@login_required
@require_POST
def guardar_tracking_semanal(request):
    if usuario_es_admin(request.user):
        return HttpResponseForbidden("Los administradores no pueden modificar el seguimiento.")

    for key, value in request.POST.items():
        if not key.startswith("stars_") or not value:
            continue

        fecha_texto = key.replace("stars_", "", 1)

        try:
            fecha = datetime.fromisoformat(fecha_texto).date()
            estrellas = max(1, min(5, int(value)))
        except (ValueError, TypeError):
            continue

        DailyMood.objects.update_or_create(
            user=request.user,
            date=fecha,
            defaults={"stress_level": estrellas}
        )

    if request.headers.get("x-requested-with") == "XMLHttpRequest" or request.headers.get("accept", "").startswith("application/json"):
        week_data = construir_datos_tracking_semanal(request.user)
        return JsonResponse({
            "status": "ok",
            "summary": week_data["summary"],
            "average": week_data["average"],
            "labels": week_data["labels"],
            "data": week_data["data"],
            "week_days": week_data["week_days"],
        })

    return redirect("seguimiento")


@login_required
def api_carga_semanal(request):
    week_days = obtener_semana_actual()
    weekday_labels = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    mood_queryset = DailyMood.objects.all() if usuario_es_admin(request.user) else DailyMood.objects.filter(user=request.user)
    mood_by_date = {
        item["date"]: item["average_stress"]
        for item in mood_queryset.filter(date__range=(week_days[0], week_days[-1]))
            .values("date")
            .annotate(average_stress=Avg("stress_level"))
    }

    labels = []
    data = []

    for day in week_days:
        labels.append(weekday_labels[day.weekday()])
        data.append(round(mood_by_date.get(day, 0) or 0, 1))

    filled_values = [value for value in data if value > 0]
    average = round(sum(filled_values) / len(filled_values), 1) if filled_values else 0

    if average >= 4:
        summary = "Semana muy ocupada"
    elif average >= 2.5:
        summary = "Semana moderada"
    elif average > 0:
        summary = "Semana ligera"
    else:
        summary = "Sin tracking todavía"

    return JsonResponse({
        "labels": labels,
        "data": data,
        "average": average,
        "summary": summary,
    })


@login_required
def dia_mas_pesado(request):
    worst = DailyMood.objects.filter(user=request.user).order_by("-stress_level").first()

    if not worst:
        return JsonResponse({"date": None, "stress": 0})

    return JsonResponse({
        "date": worst.date,
        "stress": worst.stress_level
    })


@login_required
def racha(request):
    moods = DailyMood.objects.filter(user=request.user).order_by("-date")

    streak = 0

    for m in moods:
        if m.stress_level <= 2:
            streak += 1
        else:
            break

    return JsonResponse({"streak": streak})


@login_required
def actividad_por_tipo(request):
    queryset = Actividad.objects.all() if usuario_es_admin(request.user) else Actividad.objects.filter(usuario=request.user)
    data = queryset.values("tipo").annotate(total=Count("id"))

    return JsonResponse(list(data), safe=False)


@login_required
@require_POST
def actualizar_progreso_actividad(request):
    if usuario_es_admin(request.user):
        return JsonResponse({"status": "error", "message": "Los administradores no pueden modificar tareas."}, status=403)

    actividad_id = request.POST.get("actividad_id")
    progreso = request.POST.get("progreso")

    if not actividad_id or progreso is None:
        return JsonResponse({"status": "error", "message": "Datos incompletos"}, status=400)

    try:
        progreso_numero = max(0, min(100, int(progreso)))
    except ValueError:
        return JsonResponse({"status": "error", "message": "Progreso inválido"}, status=400)

    actividad = Actividad.objects.filter(id=actividad_id, usuario=request.user).first()

    if not actividad:
        return JsonResponse({"status": "error", "message": "Actividad no encontrada"}, status=404)

    ActividadProgreso.objects.update_or_create(
        actividad=actividad,
        defaults={
            "usuario": request.user,
            "progreso": progreso_numero,
        }
    )

    return JsonResponse({"status": "ok", "progreso": progreso_numero})


@login_required
def actividad_detalle(request, id):
    es_admin = usuario_es_admin(request.user)
    actividad_qs = Actividad.objects.select_related("usuario").all()

    if not es_admin:
        actividad_qs = actividad_qs.filter(usuario=request.user)

    actividad = get_object_or_404(actividad_qs, id=id)
    detalle = obtener_actividad_con_progreso(actividad, request.user)

    if request.method == "POST":
        if es_admin:
            return HttpResponseForbidden("Los administradores no pueden modificar tareas.")

        progreso_texto = request.POST.get("progreso", detalle["progreso"])
        nota = request.POST.get("nota", "").strip()

        try:
            progreso_numero = max(0, min(100, int(progreso_texto)))
        except (TypeError, ValueError):
            progreso_numero = detalle["progreso"]

        ActividadProgreso.objects.update_or_create(
            actividad=actividad,
            defaults={
                "usuario": request.user,
                "progreso": progreso_numero,
                "nota": nota,
            },
        )

        return redirect("actividad_detalle", id=actividad.id)

    return render(
        request,
        "core/actividad_detalle.html",
        {
            "actividad": actividad,
            "progreso": detalle["progreso"],
            "nota": detalle["nota"],
            "actualizado_en": detalle["actualizado_en"],
            "es_admin": es_admin,
        },
    )

@login_required
def actividades(request):
    return render(
        request,
        "core/actividades.html",
        obtener_contexto_dashboard(request)
    )


@login_required
def seguimiento(request):
    return render(
        request,
        "core/seguimiento.html",
        obtener_contexto_dashboard(request)
    )


@login_required
def estadisticas(request):
    weeks = construir_opciones_semanales(request.user)
    selected_week = request.GET.get("week")
    selected_start = None

    if selected_week:
        try:
            selected_start = datetime.fromisoformat(selected_week).date()
        except ValueError:
            selected_start = None

    if not selected_start:
        selected_start = weeks[-1]["start"]

    weekly_data = construir_datos_tracking_semanal(request.user, selected_start)

    return render(
        request,
        "core/estadisticas.html",
        {
            **obtener_contexto_dashboard(request),
            "weeks": weeks,
            "selected_week": weekly_data,
            "selected_week_start": selected_start.isoformat(),
        },
    )


@login_required
def api_estadisticas_semanales(request):
    week = request.GET.get("week")
    selected_start = None

    if week:
        try:
            selected_start = datetime.fromisoformat(week).date()
        except ValueError:
            selected_start = None

    if not selected_start:
        weeks = construir_opciones_semanales(request.user)
        selected_start = weeks[-1]["start"]

    data = construir_datos_tracking_semanal(request.user, selected_start)

    return JsonResponse({
        "labels": data["labels"],
        "data": data["data"],
        "average": data["average"],
        "summary": data["summary"],
        "week_label": data["week_label"],
        "week_start": data["week_start"].isoformat(),
        "week_end": data["week_end"].isoformat(),
    })