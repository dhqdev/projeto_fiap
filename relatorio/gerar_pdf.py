"""
Monta o relatório executivo em PDF.

Uso:
    python relatorio/gerar_pdf.py

Pré-requisitos: weasyprint. As figuras dos dados são geradas antes por
analise/analise_olist.py; o diagrama de arquitetura, por relatorio/diagramas.py.
"""
import math
import re
import subprocess
import sys
from pathlib import Path

from weasyprint import HTML

AQUI = Path(__file__).resolve().parent
SAIDA = AQUI / "Relatorio_Executivo_Olist_Fase1.pdf"


def arte_capa():
    """Arcos concêntricos sutis no canto inferior direito da capa."""
    partes = ['<svg class="arte" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 210 297" preserveAspectRatio="none">']
    cx, cy = 196, 262
    for i in range(34):
        r = 18 + i * 6.2
        t = i / 33
        # do azul ao verde-azulado, desaparecendo nas bordas
        cor = (int(42 + (25 - 42) * t), int(120 + (179 - 120) * t), int(214 + (166 - 214) * t))
        op = 0.38 * math.sin(math.pi * (0.15 + 0.8 * t)) + 0.04
        partes.append(f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="rgb{cor}" '
                      f'stroke-width="0.32" stroke-opacity="{op:.2f}"/>')
    for i in range(16):
        r = 10 + i * 5.5
        partes.append(f'<circle cx="-18" cy="40" r="{r:.1f}" fill="none" stroke="#2a78d6" '
                      f'stroke-width="0.25" stroke-opacity="{0.05 + 0.012 * i:.3f}"/>')
    partes.append("</svg>")
    return "".join(partes)


def recuo_pendente(html):
    """Quebra cada linha dos blocos <pre> em um bloco com recuo pendente, para que
    linhas longas (strings do JSON) continuem alinhadas ao quebrar."""
    def linhas(m):
        abre, corpo = m.group(1), m.group(2)
        partes = []
        for ln in corpo.split("\n"):
            n = len(ln) - len(ln.lstrip(" "))
            conteudo = ln.lstrip(" ") or "&#160;"
            partes.append(f'<span class="l" style="padding-left:{n + 2}ch;text-indent:-2ch">{conteudo}</span>')
        return abre + "".join(partes) + "</pre>"
    return re.sub(r"(<pre[^>]*>)(.*?)</pre>", linhas, html, flags=re.S)


def main():
    subprocess.run([sys.executable, str(AQUI / "diagramas.py")], check=True)
    html = (AQUI / "relatorio.html").read_text(encoding="utf-8")
    svg = (AQUI / "figuras" / "arquitetura.svg").read_text(encoding="utf-8")
    html = html.replace("<!--SVG_ARQUITETURA-->", svg).replace("<!--ARTE_CAPA-->", arte_capa())
    html = recuo_pendente(html)
    HTML(string=html, base_url=str(AQUI)).write_pdf(SAIDA)
    print(SAIDA)


if __name__ == "__main__":
    main()
