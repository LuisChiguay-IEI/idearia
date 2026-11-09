from django.urls import path

from . import views

app_name = "interacciones"

urlpatterns = [
    path("favoritos/", views.mis_favoritos, name="mis_favoritos"),
    path("ideas/<int:pk>/favorito/", views.favorito, name="favorito"),
    path("ideas/<int:pk>/valorar/", views.valorar, name="valorar"),
    path("ideas/<int:pk>/comentar/", views.comentar, name="comentar"),
    path("comentarios/<int:pk>/moderar/", views.moderar_comentario, name="moderar_comentario"),
]
