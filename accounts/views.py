from django.shortcuts import render

# Create your views here.
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User, Group
from django.shortcuts import render, redirect


def asignar_grupo_por_defecto(user):
    admin_group, _ = Group.objects.get_or_create(name="Admin")
    usuario_group, _ = Group.objects.get_or_create(name="Usuario")

    if user.is_superuser or user.is_staff:
        user.groups.add(admin_group)
    elif not user.groups.exists():
        user.groups.add(usuario_group)

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user:
            asignar_grupo_por_defecto(user)
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'core/login.html', {'error': 'Credenciales inválidas'})

    return render(request, 'core/login.html')


def register_view(request):
    if request.method == "POST":

        username = request.POST["username"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if User.objects.filter(username=username).exists():
            return render(request, "core/register.html", {
                "error": "Ese usuario ya existe."
            })

        if password1 != password2:
            return render(request, "core/register.html", {
                "error": "Las contraseñas no coinciden."
            })

        user = User.objects.create_user(
            username=username,
            password=password1
        )

        asignar_grupo_por_defecto(user)

        return redirect("login")

    return render(request, "core/register.html")


def logout_view(request):
    logout(request)
    return redirect('login')