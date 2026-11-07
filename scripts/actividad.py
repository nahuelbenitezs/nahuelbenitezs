"""Dibuja el gráfico de contribuciones públicas como un SVG animado, sin dependencias."""

import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

CONSULTA = """
query ($usuario: String!) {
  user(login: $usuario) {
    contributionsCollection {
      contributionCalendar { weeks { contributionDays { date contributionLevel } } }
    }
  }
}
"""
NIVELES = {
    "NONE": 0,
    "FIRST_QUARTILE": 1,
    "SECOND_QUARTILE": 2,
    "THIRD_QUARTILE": 3,
    "FOURTH_QUARTILE": 4,
}
CELDA, PASO = 12, 15


def pedir_semanas(usuario: str, token: str) -> list[list[dict]]:
    pedido = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CONSULTA, "variables": {"usuario": usuario}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as respuesta:
        cuerpo = json.load(respuesta)
    if "errors" in cuerpo:
        raise RuntimeError(cuerpo["errors"])
    calendario = cuerpo["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    return [semana["contributionDays"] for semana in calendario["weeks"]]


def dibujar(semanas: list[list[dict]]) -> str:
    celdas = []
    for x, semana in enumerate(semanas):
        for dia in semana:
            nivel = NIVELES[dia["contributionLevel"]]
            y = _dia_semana(dia["date"]) * PASO
            celdas.append(
                f'<rect class="n{nivel}" style="animation-delay:{x * 0.018:.2f}s" '
                f'x="{x * PASO}" y="{y}" width="{CELDA}" height="{CELDA}" rx="3"/>'
            )
    ancho, alto = len(semanas) * PASO - 3, 7 * PASO - 3
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" role="img">
<title>Contribuciones públicas del último año</title>
<style>
rect{{transform-box:fill-box;transform-origin:center;animation:a .5s cubic-bezier(.16,1,.3,1) both}}
@keyframes a{{from{{opacity:0;transform:scale(.3)}}}}
.n0{{fill:#231e52}}.n1{{fill:#6b4f1d}}.n2{{fill:#a8761f}}.n3{{fill:#e09a25}}.n4{{fill:#ffb52e}}
@media (prefers-reduced-motion:reduce){{rect{{animation:none}}}}
</style>
{"".join(celdas)}
</svg>
"""


def _dia_semana(fecha: str) -> int:
    """Domingo es 0, como en el gráfico de GitHub."""
    return (date.fromisoformat(fecha).weekday() + 1) % 7


def main() -> None:
    usuario, salida = sys.argv[1], Path(sys.argv[2])
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(dibujar(pedir_semanas(usuario, os.environ["GITHUB_TOKEN"])), "utf-8")


if __name__ == "__main__":
    main()
