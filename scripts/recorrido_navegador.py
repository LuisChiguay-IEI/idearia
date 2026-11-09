"""
Recorrido automatizado en un navegador real (OPCIONAL - evidencia de interfaces, CP-060).

Abre Microsoft Edge en modo invisible, inicia sesión con cada perfil de
demostración, recorre las pantallas principales, guarda capturas y reporta
errores de JavaScript, de la política CSP o respuestas HTTP >= 400.

Requisitos (no forman parte de requirements.txt):
    .\\.venv\\Scripts\\python.exe -m pip install playwright
    (usa el Microsoft Edge instalado en Windows; no descarga navegadores)

Uso, con el servidor corriendo y los datos de demostración cargados:
    .\\.venv\\Scripts\\python.exe scripts\\recorrido_navegador.py
"""

import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright


def leer_clave():
    if os.getenv("DEMO_PASSWORD"):
        return os.getenv("DEMO_PASSWORD")
    for linea in Path(".env").read_text(encoding="utf-8").splitlines():
        if linea.startswith("DEMO_PASSWORD="):
            return linea.split("=", 1)[1].strip().strip('"')
    raise SystemExit("Define DEMO_PASSWORD en .env")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8001")
    parser.add_argument("--salida", default="docs/evidencias/capturas")
    args = parser.parse_args()
    base, salida, clave = args.url, Path(args.salida), leer_clave()
    salida.mkdir(parents=True, exist_ok=True)
    problemas = []

    def vigilar(pagina, perfil):
        pagina.on("pageerror", lambda e: problemas.append(f"[{perfil}] Error JS: {e}"))
        pagina.on("console", lambda m: problemas.append(f"[{perfil}] Consola: {m.text[:160]}") if m.type == "error" else None)
        pagina.on("response", lambda r: problemas.append(f"[{perfil}] HTTP {r.status} {r.url}") if r.status >= 400 else None)

    def ingresar(pagina, correo):
        pagina.goto(f"{base}/ingresar/")
        pagina.fill("input[name=username]", correo)
        pagina.fill("input[name=password]", clave)
        pagina.click("button[type=submit]")
        pagina.wait_for_load_state("networkidle")

    def captura(pagina, ruta, nombre):
        pagina.goto(base + ruta)
        pagina.wait_for_load_state("networkidle")
        pagina.screenshot(path=str(salida / f"{nombre}.png"), full_page=True)

    with sync_playwright() as p:
        navegador = p.chromium.launch(channel="msedge", headless=True)

        contexto = navegador.new_context(viewport={"width": 1366, "height": 900})
        pagina = contexto.new_page()
        vigilar(pagina, "anónimo")
        captura(pagina, "/ingresar/", "01_login")
        captura(pagina, "/registro/", "02_registro")

        vigilar(pagina, "educadora")
        ingresar(pagina, "educadora@idearia.test")
        captura(pagina, "/ideas/", "03_catalogo")
        captura(pagina, "/ideas/?nivel=NIVEL_MEDIO&duracion=media&orden=valoradas", "04_filtros")
        detalle = pagina.locator(".tarjeta-idea h3 a").first.get_attribute("href")
        captura(pagina, detalle, "05_detalle")
        captura(pagina, detalle + "planificacion/", "06_visor")
        if pagina.locator("#visor-pdf").count():
            pagina.wait_for_selector("#visor-pdf canvas", timeout=15000)
            pagina.screenshot(path=str(salida / "06_visor.png"), full_page=True)
        captura(pagina, "/favoritos/", "07_favoritos")
        captura(pagina, "/colaborador/acreditacion/nueva/", "08_solicitud")
        pagina.goto(f"{base}/administracion/")  # debe responder 403 (acceso denegado esperado)
        pagina.screenshot(path=str(salida / "18_error_403_educador.png"), full_page=True)
        problemas[:] = [x for x in problemas if "/administracion/" not in x and "403" not in x]
        contexto.close()

        contexto = navegador.new_context(viewport={"width": 1366, "height": 900})
        pagina = contexto.new_page()
        vigilar(pagina, "colaboradora")
        ingresar(pagina, "colaboradora@idearia.test")
        captura(pagina, "/colaborador/", "09_panel_colaborador")
        captura(pagina, "/colaborador/propuestas/nueva/", "10_propuesta_form")
        captura(pagina, "/colaborador/propuestas/", "12_estado_propuestas")
        contexto.close()

        contexto = navegador.new_context(viewport={"width": 1366, "height": 900})
        pagina = contexto.new_page()
        vigilar(pagina, "administradora")
        ingresar(pagina, "administradora@idearia.test")
        captura(pagina, "/administracion/", "13_panel_admin")
        captura(pagina, "/administracion/solicitudes/", "14a_solicitudes")
        captura(pagina, "/administracion/propuestas/", "15_revision_propuestas")
        captura(pagina, "/administracion/usuarios/", "16_usuarios")
        contexto.close()

        contexto = navegador.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, device_scale_factor=2)
        pagina = contexto.new_page()
        vigilar(pagina, "móvil")
        ingresar(pagina, "educadora@idearia.test")
        pagina.screenshot(path=str(salida / "17_movil_catalogo.png"))
        ancho = pagina.evaluate("document.documentElement.scrollWidth")
        if ancho > 390:
            problemas.append(f"[móvil] Desplazamiento horizontal: ancho {ancho}px > 390px")
        contexto.close()
        navegador.close()

    print(f"Capturas guardadas en {salida}")
    if problemas:
        print("Problemas detectados:")
        for problema in problemas:
            print("  -", problema)
    else:
        print("Sin errores de JavaScript, CSP ni HTTP >= 400. Sin desplazamiento horizontal en móvil.")


if __name__ == "__main__":
    main()
