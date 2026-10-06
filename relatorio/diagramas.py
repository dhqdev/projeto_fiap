"""Gera o diagrama da arquitetura conceitual (figuras/arquitetura.svg)."""
from pathlib import Path

SAIDA = Path(__file__).resolve().parent / "figuras" / "arquitetura.svg"

TINTA = "#14213d"
TINTA_2 = "#4a5468"
AZUL = "#2a78d6"
AZUL_ESCURO = "#1c5cab"
SETA = "#7b8496"
FUNDO_1 = "#f4f6f9"
FUNDO_2 = "#eef4fc"
FUNDO_3 = "#f4f6f9"
BORDA = "#d5dbe5"

W = 600
el = []


def rect(x, y, w, h, fill="#fff", stroke=BORDA, rx=6, sw=1):
    el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def text(x, y, s, size=8, weight=400, fill=TINTA_2, anchor="start", spacing=0):
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    el.append(f'<text x="{x}" y="{y}" font-family="Inter" font-size="{size}" font-weight="{weight}" '
              f'fill="{fill}" text-anchor="{anchor}"{ls}>{s}</text>')


def seta(x1, y1, x2, y2, cor=SETA, sw=1.1):
    el.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{cor}" stroke-width="{sw}" marker-end="url(#ponta)"/>')


def caminho(d, cor=SETA, sw=1.1):
    el.append(f'<path d="{d}" fill="none" stroke="{cor}" stroke-width="{sw}" marker-end="url(#ponta)"/>')


def selo(cx, cy, letra):
    el.append(f'<circle cx="{cx}" cy="{cy}" r="7" fill="{AZUL_ESCURO}"/>')
    text(cx, cy + 3, letra, size=8, weight=700, fill="#fff", anchor="middle")


def faixa(y, h, numero, titulo, fundo):
    rect(0, y, W, h, fill=fundo, stroke="none", rx=8)
    cx, cy = 15, y + h / 2
    el.append(f'<text x="{cx}" y="{cy}" transform="rotate(-90 {cx} {cy})" font-family="Inter" font-size="7.6" '
              f'font-weight="700" fill="{AZUL_ESCURO}" text-anchor="middle" dominant-baseline="central" '
              f'letter-spacing="0.9">{numero}  {titulo}</text>')


def caixa(x, y, w, h, titulo, linhas, destaque=False):
    rect(x, y, w, h, fill="#fff", stroke=BORDA)
    if destaque:
        el.append(f'<rect x="{x}" y="{y}" width="{w}" height="3" fill="{AZUL}"/>')
    text(x + 9, y + 18, titulo, size=8.8, weight=600, fill=TINTA)
    for i, l in enumerate(linhas):
        text(x + 9, y + 33 + i * 11.5, l, size=8.1)


# grade de cinco colunas (margem esquerda maior para o rótulo vertical da faixa)
M = 30
MR = 12
GAP = 8
LW = W - M - MR
CW = (LW - 4 * GAP) / 5
cols = [M + i * (CW + GAP) for i in range(5)]

# 1. Fontes de dados ---------------------------------------------------------
y1 = 0
faixa(y1, 96, "1", "FONTES", FUNDO_1)
fontes = [
    ("Base transacional", ["pedidos e itens", "pagamentos e clientes", "vendedores e produtos"]),
    ("Avaliações", ["nota de 1 a 5", "título e comentário", "data da resposta"]),
    ("Rastreamento", ["eventos das", "transportadoras", "e dos Correios"]),
    ("Atendimento", ["chat no site", "WhatsApp", "e-mail"]),
    ("Políticas e regras", ["trocas e devoluções", "CDC e LGPD", "perguntas frequentes"]),
]
for x, (t, ls) in zip(cols, fontes):
    caixa(x, y1 + 12, CW, 72, t, ls)

# 2. Camada de agentes -------------------------------------------------------
y2 = 108
H2 = 286
faixa(y2, H2, "2", "CAMADA DE AGENTES", FUNDO_2)
for x in cols:
    seta(x + CW / 2, y1 + 84, x + CW / 2, y2 + 14)

# orquestrador
oy = y2 + 16
rect(M, oy, LW, 30, fill=TINTA, stroke="none")
text(M + LW / 2, oy + 19, "Orquestrador  ·  recebe cada evento, aciona o agente responsável e registra a decisão",
     size=8.8, weight=500, fill="#fff", anchor="middle")

# agentes
AG = 3
AGAP = 36
AW = (LW - (AG - 1) * AGAP) / AG
ay = oy + 48
AH = 100
agentes = [
    ("AGENTE 01", "Analista de Reviews", ["classifica cada avaliação", "por sentimento e causa e", "aponta padrões por", "vendedor e categoria"]),
    ("AGENTE 02", "Guardião Logístico", ["acompanha pedidos em", "trânsito, estima o risco", "de atraso e avisa o cliente", "antes do prazo vencer"]),
    ("AGENTE 03", "SAC Agêntico", ["atende no chat, conduz", "trocas e devoluções", "dentro da política e", "escala as exceções"]),
]
ax = [M + i * (AW + AGAP) for i in range(AG)]
for x, (n, t, ls) in zip(ax, agentes):
    seta(x + AW / 2, oy + 30, x + AW / 2, ay)
    rect(x, ay, AW, AH, fill="#fff", stroke=BORDA)
    el.append(f'<rect x="{x}" y="{ay}" width="{AW}" height="3" fill="{AZUL}"/>')
    text(x + 10, ay + 17, n, size=7, weight=700, fill=AZUL_ESCURO, spacing=0.8)
    text(x + 10, ay + 32, t, size=10.2, weight=650, fill=TINTA)
    for i, l in enumerate(ls):
        text(x + 10, ay + 48 + i * 11.5, l, size=8.4)

# interações entre agentes
ym = ay + AH / 2
seta(ax[0] + AW + 3, ym, ax[1] - 4, ym, cor=AZUL_ESCURO, sw=1.3)
selo((ax[0] + AW + ax[1]) / 2, ym - 12, "a")
seta(ax[1] + AW + 3, ym, ax[2] - 4, ym, cor=AZUL_ESCURO, sw=1.3)
selo((ax[1] + AW + ax[2]) / 2, ym - 12, "b")
yb = ay + AH + 14
caminho(f"M {ax[2] + AW / 2} {ay + AH} L {ax[2] + AW / 2} {yb} L {ax[0] + AW / 2} {yb} L {ax[0] + AW / 2} {ay + AH + 3}",
        cor=AZUL_ESCURO, sw=1.3)
selo(M + LW / 2, yb, "c")

# memória e controles
my = yb + 16
half = (LW - GAP) / 2
rect(M, my, half, 34, fill="#fff", stroke=AZUL, sw=1)
text(M + 10, my + 14, "Memória compartilhada", size=8.4, weight=600, fill=TINTA)
text(M + 10, my + 26, "histórico de eventos de cada cliente e pedido", size=8.1)
rect(M + half + GAP, my, half, 34, fill="#fff", stroke=AZUL, sw=1)
text(M + half + GAP + 10, my + 14, "Controles comuns", size=8.4, weight=600, fill=TINTA)
text(M + half + GAP + 10, my + 26, "filtro de dados pessoais, limites de autonomia, auditoria", size=8.1)

# legenda das interações
ly = my + 52
legenda = [
    ("a", "avaliações que citam atraso viram sinal de risco por rota e vendedor"),
    ("b", "pedidos em risco e avisos já enviados ficam disponíveis no atendimento"),
    ("c", "motivos de contato no atendimento complementam a análise de causas"),
]
for i, (l, s) in enumerate(legenda):
    yy = ly + i * 12.5
    text(M + 2, yy, f"{l})", size=8, weight=700, fill=AZUL_ESCURO)
    text(M + 15, yy, s, size=8)

# 3. Saídas e usuários -------------------------------------------------------
y3 = y2 + H2 + 12
faixa(y3, 96, "3", "SAÍDAS", FUNDO_3)
for x in cols:
    seta(x + CW / 2, y2 + H2 + 1, x + CW / 2, y3 + 11)
saidas = [
    ("Clientes", ["avisos de atraso,", "respostas e etiquetas", "de devolução"]),
    ("Atendimento humano", ["fila de exceções", "com resumo do caso"]),
    ("Vendedores", ["alertas de postagem", "e de qualidade", "dos anúncios"]),
    ("Operações logísticas", ["tratativas com as", "transportadoras"]),
    ("Gestão e diretoria", ["painel de indicadores", "e relatório semanal"]),
]
for x, (t, ls) in zip(cols, saidas):
    caixa(x, y3 + 12, CW, 72, t, ls)

H = y3 + 96
defs = (f'<defs><marker id="ponta" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
        f'orient="auto-start-reverse"><path d="M0,1 L9,5 L0,9 z" fill="{SETA}"/></marker></defs>')
svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" class="diagrama">'
       + defs + "".join(el) + "</svg>")
SAIDA.parent.mkdir(parents=True, exist_ok=True)
SAIDA.write_text(svg, encoding="utf-8")
print(SAIDA, W, H)
