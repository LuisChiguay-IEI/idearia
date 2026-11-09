def notificaciones_no_leidas(request):
    """Agrega a todas las plantillas la cantidad de notificaciones sin leer."""
    if request.user.is_authenticated:
        return {"notificaciones_sin_leer": request.user.notificaciones.filter(leida=False).count()}
    return {}
