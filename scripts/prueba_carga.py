"""
Prueba de carga básica de Idearia (RNF-01: búsquedas en 2 segundos o menos).

Simula N usuarios concurrentes. Cada uno inicia sesión y realiza M búsquedas
con filtros aleatorios en el catálogo. Mide el tiempo de cada respuesta y
guarda un CSV con el detalle y un resumen en Markdown.

Solo usa la biblioteca estándar de Python (sin instalar nada).

Uso (con el servidor corriendo en otra terminal):
    .\\.venv\\Scripts\\python.exe scripts\\prueba_carga.py --usuarios 10 --peticiones 20
    .\\.venv\\Scripts\\python.exe scripts\\prueba_carga.py --url http://127.0.0.1:8001 --usuarios 25 --peticiones 20

La contraseña se toma de DEMO_PASSWORD (archivo .env) o de --clave.
"""

import argparse
import csv
import http.cookiejar
import os
import random
import re
import statistics
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

UMBRAL_SEGUNDOS = 2.0  # RNF-01

FILTROS_POSIBLES = [
    {},
    {"q": "naturaleza"},
    {"q": "emociones"},
    {"nivel": "NIVEL_MEDIO"},
    {"nivel": "KINDER", "edad": "5-6"},
    {"duracion": "corta"},
    {"duracion": "media", "orden": "valoradas"},
    {"nivel": "PREKINDER", "duracion": "media"},
    {"materiales": "8"},
    {"q": "juego", "orden": "titulo"},
    {"edad": "3-4", "duracion": "larga"},
    {"categoria": "4", "page": "1"},
]


def leer_env(ruta=".env"):
    """Lee DEMO_PASSWORD del .env sin depender de python-dotenv."""
    if not Path(ruta).exists():
        return {}
    valores = {}
    for linea in Path(ruta).read_text(encoding="utf-8").splitlines():
        if "=" in linea and not linea.strip().startswith("#"):
            clave, valor = linea.split("=", 1)
            valores[clave.strip()] = valor.strip().strip('"')
    return valores


def crear_sesion(base, correo, clave):
    """Inicia sesión como lo haría un navegador (obtiene el token CSRF y envía el formulario)."""
    galletas = http.cookiejar.CookieJar()
    abridor = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(galletas))
    html = abridor.open(f"{base}/ingresar/", timeout=30).read().decode("utf-8")
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', html).group(1)
    datos = urllib.parse.urlencode({"csrfmiddlewaretoken": token, "username": correo, "password": clave}).encode()
    peticion = urllib.request.Request(f"{base}/ingresar/", data=datos, headers={"Referer": f"{base}/ingresar/"})
    respuesta = abridor.open(peticion, timeout=30)
    if "/ingresar/" in respuesta.geturl():
        raise RuntimeError("No se pudo iniciar sesión: revisa el correo y la contraseña.")
    return abridor


def usuario_virtual(numero, base, correo, clave, peticiones, resultados, candado):
    abridor = crear_sesion(base, correo, clave)
    for indice in range(peticiones):
        filtros = random.choice(FILTROS_POSIBLES)
        url = f"{base}/ideas/?{urllib.parse.urlencode(filtros)}"
        inicio = time.perf_counter()
        try:
            respuesta = abridor.open(url, timeout=30)
            cuerpo = respuesta.read()
            estado, tamano = respuesta.status, len(cuerpo)
        except urllib.error.HTTPError as error:
            estado, tamano = error.code, 0
        except Exception:  # timeout o conexión rechazada
            estado, tamano = 0, 0
        duracion = time.perf_counter() - inicio
        with candado:
            resultados.append({
                "usuario": numero, "peticion": indice + 1, "url": url.replace(base, ""),
                "estado": estado, "segundos": round(duracion, 4), "bytes": tamano,
            })


def percentil(valores, p):
    ordenados = sorted(valores)
    k = (len(ordenados) - 1) * p / 100
    inferior = int(k)
    superior = min(inferior + 1, len(ordenados) - 1)
    return ordenados[inferior] + (ordenados[superior] - ordenados[inferior]) * (k - inferior)


def main():
    env = leer_env()
    parser = argparse.ArgumentParser(description="Prueba de carga básica de búsquedas en Idearia")
    parser.add_argument("--url", default="http://127.0.0.1:8001")
    parser.add_argument("--correo", default="educadora@idearia.test")
    parser.add_argument("--clave", default=os.getenv("DEMO_PASSWORD") or env.get("DEMO_PASSWORD"))
    parser.add_argument("--usuarios", type=int, default=10, help="usuarios concurrentes")
    parser.add_argument("--peticiones", type=int, default=20, help="búsquedas por usuario")
    parser.add_argument("--salida", default="docs/evidencias")
    args = parser.parse_args()
    if not args.clave:
        parser.error("Falta la contraseña: define DEMO_PASSWORD en .env o usa --clave")

    resultados, candado = [], threading.Lock()
    print(f"Prueba de carga: {args.usuarios} usuarios x {args.peticiones} búsquedas contra {args.url}")
    inicio = time.perf_counter()
    with ThreadPoolExecutor(max_workers=args.usuarios) as ejecutor:
        tareas = [
            ejecutor.submit(usuario_virtual, n + 1, args.url, args.correo, args.clave, args.peticiones, resultados, candado)
            for n in range(args.usuarios)
        ]
        for tarea in tareas:
            tarea.result()
    total_segundos = time.perf_counter() - inicio

    tiempos = [r["segundos"] for r in resultados if r["estado"] == 200]
    errores = [r for r in resultados if r["estado"] != 200]
    sobre_umbral = [t for t in tiempos if t > UMBRAL_SEGUNDOS]
    resumen = {
        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "url": args.url,
        "usuarios concurrentes": args.usuarios,
        "búsquedas por usuario": args.peticiones,
        "total de peticiones": len(resultados),
        "respuestas 200": len(tiempos),
        "errores": len(errores),
        "tiempo promedio (s)": round(statistics.mean(tiempos), 3) if tiempos else None,
        "mediana (s)": round(statistics.median(tiempos), 3) if tiempos else None,
        "percentil 95 (s)": round(percentil(tiempos, 95), 3) if tiempos else None,
        "máximo (s)": round(max(tiempos), 3) if tiempos else None,
        "peticiones sobre 2 s": len(sobre_umbral),
        "rendimiento (peticiones/s)": round(len(resultados) / total_segundos, 2),
        "duración total (s)": round(total_segundos, 2),
    }
    cumple = bool(tiempos) and not errores and percentil(tiempos, 95) <= UMBRAL_SEGUNDOS
    resumen["resultado RNF-01 (p95 <= 2 s, sin errores)"] = "OK" if cumple else "NO OK"

    carpeta = Path(args.salida)
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre = f"carga_{args.usuarios}u_{args.peticiones}p_{marca}"
    with open(carpeta / f"{nombre}.csv", "w", newline="", encoding="utf-8") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=list(resultados[0].keys()))
        escritor.writeheader()
        escritor.writerows(resultados)
    lineas = ["# Resultado de prueba de carga", "", "| Indicador | Valor |", "|---|---|"]
    lineas += [f"| {clave} | {valor} |" for clave, valor in resumen.items()]
    (carpeta / f"{nombre}.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

    print()
    for clave, valor in resumen.items():
        print(f"  {clave:<45} {valor}")
    print(f"\nDetalle guardado en {carpeta / (nombre + '.csv')}")


if __name__ == "__main__":
    main()
