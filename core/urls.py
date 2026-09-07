from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('crear/', views.crear_actividad, name='crear'),
    path('toggle/<int:id>/', views.toggle_actividad, name='toggle'),
    path('eliminar/<int:id>/', views.eliminar_actividad, name='eliminar'),
    path('mover/', views.mover_actividad, name='mover'),
    path("api/tablero/", views.api_tablero, name="api_tablero"),
    path('api/carga-semanal/', views.api_carga_semanal, name='carga_semanal'),
    path('tracking/guardar/', views.guardar_tracking_semanal, name='guardar_tracking_semanal'),
    path('api/actividad/progreso/', views.actualizar_progreso_actividad, name='actualizar_progreso_actividad'),
    path('api/estadisticas/semanales/', views.api_estadisticas_semanales, name='api_estadisticas_semanales'),
    path('actividades/', views.actividades, name='actividades'),
    path('actividades/<int:id>/', views.actividad_detalle, name='actividad_detalle'),
    path('seguimiento/', views.seguimiento, name='seguimiento'),
    path('estadisticas/', views.estadisticas, name='estadisticas'),
   
    path("scratch/marcar/", views.marcar_scratch),
    path("ruleta/", views.ruleta, name="ruleta"),
    path("actividad/eliminar-ajax/<int:id>/", views.eliminar_actividad_ajax, name="eliminar_ajax"),
]