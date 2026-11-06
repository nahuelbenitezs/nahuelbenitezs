"""Dibuja una ficha estilo terminal con datos reales y públicos de GitHub."""

import json
import os
import sys
import urllib.request
from datetime import date
from html import escape
from pathlib import Path

DESTACADOS = ["canasta-uy", "Anime-Clash-3D", "valopedia", "Ritmo", "Proyecto-Obligatorio"]
NOMBRES = {"Proyecto-Obligatorio": "eMercado", "canasta-uy": "Canasta UY", "Anime-Clash-3D": "Anime Clash 3D"}
CONSULTA = """
query ($usuario: String!) {
  user(login: $usuario) {
    createdAt
    repositories(privacy: PUBLIC, ownerAffiliations: OWNER, isFork: false) { totalCount }
    contributionsCollection { contributionCalendar { totalContributions } }
    %s
  }
}
"""


def pedir(usuario: str, token: str) -> dict:
    alias = " ".join(
        f'r{i}: repository(name: "{nombre}") {{ name pushedAt }}'
        for i, nombre in enumerate(DESTACADOS)
    )
    pedido = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": CONSULTA % alias, "variables": {"usuario": usuario}}).encode(),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(pedido, timeout=30) as respuesta:
        cuerpo = json.load(respuesta)
    if "errors" in cuerpo:
        raise RuntimeError(cuerpo["errors"])
    return cuerpo["data"]["user"]


def filas(datos: dict, hoy: date) -> list[tuple[str, str]]:
    repos = [datos[f"r{i}"] for i in range(len(DESTACADOS)) if datos.get(f"r{i}")]
    repos.sort(key=lambda r: r["pushedAt"], reverse=True)
    ultimo = repos[0]
    dias = (hoy - date.fromisoformat(ultimo["pushedAt"][:10])).days
    cuando = "hoy" if dias == 0 else "ayer" if dias == 1 else f"hace {dias} días"
    return [
        ("en GitHub desde", datos["createdAt"][:4]),
        ("repos públicos", str(datos["repositories"]["totalCount"])),
        (
            "contribuciones públicas",
            f'{datos["contributionsCollection"]["contributionCalendar"]["totalContributions"]} en el último año',
        ),
        ("último proyecto tocado", f'{NOMBRES.get(ultimo["name"], ultimo["name"])}, {cuando}'),
    ]


def dibujar(lineas: list[tuple[str, str]]) -> str:
    alto = 74 + len(lineas) * 30
    texto = "".join(
        f'<g class="f" style="animation-delay:{0.25 + i * 0.22:.2f}s">'
        f'<text x="28" y="{84 + i * 30}" class="k">{escape(clave)}</text>'
        f'<text x="320" y="{84 + i * 30}" class="v">{escape(valor)}</text></g>'
        for i, (clave, valor) in enumerate(lineas)
    )
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 860 {alto}" role="img">
<title>Datos públicos de Nahuel Benítez en GitHub</title>
<style>
text{{font:16px ui-monospace,SFMono-Regular,Consolas,Menlo,monospace}}
.p{{fill:#fbfaf4}}.b{{fill:#ffd21f}}.t{{fill:#14140f;font-weight:700}}.k{{fill:#4d4c42}}.v{{fill:#14140f;font-weight:600}}
.f{{animation:a .5s cubic-bezier(.16,1,.3,1) both}}
@keyframes a{{from{{opacity:0;transform:translateX(-10px)}}}}
@media (prefers-color-scheme:dark){{.p{{fill:#161b22}}.k{{fill:#9da5ae}}.v{{fill:#ffd21f}}}}
@media (prefers-reduced-motion:reduce){{.f{{animation:none}}}}
</style>
<rect class="p" width="860" height="{alto}" rx="14"/>
<path class="b" d="M14 0h832a14 14 0 0 1 14 14v26H0V14A14 14 0 0 1 14 0z"/>
<text x="28" y="26" class="t">nahuel@github ~ $ ficha --en-vivo</text>
{texto}
</svg>
"""


def main() -> None:
    usuario, salida = sys.argv[1], Path(sys.argv[2])
    salida.parent.mkdir(parents=True, exist_ok=True)
    datos = pedir(usuario, os.environ["GITHUB_TOKEN"])
    salida.write_text(dibujar(filas(datos, date.today())), "utf-8")


if __name__ == "__main__":
    main()
