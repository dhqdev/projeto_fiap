"""
Análise exploratória do Brazilian E-Commerce Public Dataset by Olist.

Gera as métricas citadas no relatório executivo (dados/metricas.json) e as
figuras do capítulo 3 (relatorio/figuras/*.svg).

Uso:
    python analise/analise_olist.py <pasta_com_os_csv>

Os CSVs podem ser obtidos no Kaggle (olistbr/brazilian-ecommerce) ou no
repositório público github.com/olist/work-at-olist-data (pasta datasets/).
"""
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

RAIZ = Path(__file__).resolve().parent.parent
FIG = RAIZ / "relatorio" / "figuras"
SAIDA = RAIZ / "analise" / "metricas.json"

# Paleta (validada com o validador de paleta: CVD e separação normal >= 15)
AZUL = "#2a78d6"
AZUL_ESCURO = "#1c5cab"
TINTA = "#1d2433"
TINTA_2 = "#52514e"
MUTED = "#898781"
GRADE = "#e1e0d9"
BASE = "#c3c2b7"
DIVERGENTE = ["#a8302f", "#e8706c", "#e6e5df", "#6da7ec", "#1c5cab"]  # notas 1..5

MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def configurar_fontes():
    for f in (RAIZ / "relatorio" / "fontes").glob("Inter-*.otf"):
        font_manager.fontManager.addfont(str(f))
    plt.rcParams.update({
        "font.family": "Inter",
        "font.size": 8,
        "svg.fonttype": "path",
        "axes.edgecolor": BASE,
        "axes.linewidth": 0.8,
        "axes.labelcolor": TINTA_2,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "xtick.labelcolor": TINTA_2,
        "ytick.labelcolor": TINTA_2,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": False,
        "figure.dpi": 150,
    })


def pct(x, casas=1):
    return f"{x * 100:.{casas}f}".replace(".", ",") + "%"


def carregar(pasta):
    ler = lambda nome: pd.read_csv(Path(pasta) / f"{nome}.csv")
    t = {
        "orders": ler("olist_orders_dataset"),
        "customers": ler("olist_customers_dataset"),
        "items": ler("olist_order_items_dataset"),
        "payments": ler("olist_order_payments_dataset"),
        "reviews": ler("olist_order_reviews_dataset"),
        "products": ler("olist_products_dataset"),
        "sellers": ler("olist_sellers_dataset"),
    }
    o = t["orders"]
    for col in ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
                "order_delivered_customer_date", "order_estimated_delivery_date"]:
        o[col] = pd.to_datetime(o[col])
    t["items"]["shipping_limit_date"] = pd.to_datetime(t["items"]["shipping_limit_date"])
    return t


def analisar(t):
    o, c, it, p, rv, pr, s = (t[k] for k in ["orders", "customers", "items", "payments", "reviews", "products", "sellers"])
    m = {}
    m["pedidos"] = len(o)
    m["clientes_unicos"] = int(c.customer_unique_id.nunique())
    m["vendedores"] = int(s.seller_id.nunique())
    m["produtos"] = int(pr.product_id.nunique())
    m["categorias"] = int(pr.product_category_name.nunique())
    m["periodo"] = [str(o.order_purchase_timestamp.min().date()), str(o.order_purchase_timestamp.max().date())]
    m["status"] = o.order_status.value_counts(normalize=True).round(4).to_dict()
    m["gmv_pagamentos"] = round(float(p.payment_value.sum()), 2)
    ticket = p.groupby("order_id").payment_value.sum()
    m["ticket_medio"] = round(float(ticket.mean()), 2)
    m["ticket_mediano"] = round(float(ticket.median()), 2)
    m["pagamento_tipo"] = p.payment_type.value_counts(normalize=True).round(4).to_dict()
    m["frete_sobre_preco"] = round(float(it.freight_value.sum() / it.price.sum()), 4)

    # Entregas: atraso = entregue em data posterior à data estimada
    d = o[(o.order_status == "delivered") & o.order_delivered_customer_date.notna()].copy()
    d["atraso"] = d.order_delivered_customer_date.dt.normalize() > d.order_estimated_delivery_date.dt.normalize()
    d["dias_real"] = (d.order_delivered_customer_date - d.order_purchase_timestamp).dt.total_seconds() / 86400
    d["dias_prometido"] = (d.order_estimated_delivery_date - d.order_purchase_timestamp).dt.total_seconds() / 86400
    d["dias_atraso"] = (d.order_delivered_customer_date - d.order_estimated_delivery_date).dt.total_seconds() / 86400
    m["entregues"] = len(d)
    m["taxa_atraso"] = round(float(d.atraso.mean()), 4)
    m["prazo_real_mediano"] = round(float(d.dias_real.median()), 1)
    m["prazo_prometido_mediano"] = round(float(d.dias_prometido.median()), 1)
    m["atraso_mediano_dias"] = round(float(d.loc[d.atraso, "dias_atraso"].median()), 1)

    d = d.merge(c, on="customer_id")
    uf = d.groupby("customer_state").agg(pedidos=("order_id", "size"), atraso=("atraso", "mean"),
                                         prazo_mediano=("dias_real", "median"))
    m["atraso_por_uf"] = uf.sort_values("atraso", ascending=False).round(4).to_dict(orient="index")

    d["mes"] = d.order_purchase_timestamp.dt.to_period("M")
    mes = d.groupby("mes").atraso.mean()
    m["atraso_por_mes"] = {str(k): round(float(v), 4) for k, v in mes.items()}

    # Despacho do vendedor após o prazo-limite de postagem
    limite = it.groupby("order_id").shipping_limit_date.max()
    d = d.join(limite, on="order_id")
    d["vendedor_atrasou"] = d.order_delivered_carrier_date > d.shipping_limit_date
    m["despacho_fora_prazo"] = round(float(d.vendedor_atrasou.mean()), 4)
    m["p_atraso_se_vendedor_atrasou"] = round(float(d[d.vendedor_atrasou].atraso.mean()), 4)
    m["p_atraso_se_vendedor_no_prazo"] = round(float(d[~d.vendedor_atrasou].atraso.mean()), 4)
    m["atrasados_com_despacho_fora_prazo"] = round(float(d[d.atraso].vendedor_atrasou.mean()), 4)

    # Avaliações
    rv1 = rv.drop_duplicates("order_id")
    m["avaliacoes"] = len(rv)
    m["avaliacoes_com_comentario"] = round(float(rv.review_comment_message.notna().mean()), 4)
    m["dist_notas"] = rv.review_score.value_counts(normalize=True).sort_index().round(4).to_dict()
    a = o.merge(rv1[["order_id", "review_score", "review_comment_message"]], on="order_id")
    a = a.merge(d[["order_id", "atraso"]], on="order_id", how="left")
    a["situacao"] = np.where(a.order_status != "delivered", "Não entregue",
                             np.where(a.atraso == True, "Entregue com atraso", "Entregue no prazo"))  # noqa: E712
    m["nota_media_por_situacao"] = a.groupby("situacao").review_score.mean().round(2).to_dict()
    m["pedidos_por_situacao"] = a.situacao.value_counts().to_dict()
    m["notas_baixas_por_situacao"] = a.groupby("situacao").review_score.apply(lambda x: (x <= 2).mean()).round(4).to_dict()
    dist = a.groupby("situacao").review_score.value_counts(normalize=True).unstack().fillna(0)
    baixas = a[a.review_score <= 2]
    m["notas_baixas_total"] = len(baixas)
    m["composicao_notas_baixas"] = baixas.situacao.value_counts(normalize=True).round(4).to_dict()
    m["notas_baixas_com_comentario"] = round(float(baixas.review_comment_message.notna().mean()), 4)

    # Temas nos comentários negativos (classificação por palavras-chave, multirrótulo)
    texto = baixas.review_comment_message.dropna().str.lower()
    temas = {
        "Entrega atrasada ou não recebida": r"n[aã]o (?:recebi|chegou|foi entregue|entregue|veio)|atras|prazo|ainda n[aã]o|aguardando|demor|entrega",
        "Produto errado, diferente ou incompleto": r"errad|diferente|outro produto|trocad|faltando|falta|incomplet|veio s[oó]|apenas um|somente um|s[oó] (?:um|uma|1)|n[aã]o (?:era|é) o",
        "Falta de retorno do atendimento": r"atendimento|contato|resposta|retorno|ningu[eé]m|sac|reclama|email|e-mail|telefone",
        "Reembolso, troca ou cancelamento": r"reembols|estorno|devolu|devolv|cancel|dinheiro de volta|troca",
        "Defeito, avaria ou baixa qualidade": r"defeit|quebrad|danific|avari|qualidade|n[aã]o funciona|parou de|rasgad|amassad|estragad",
    }
    m["comentarios_negativos_analisados"] = int(len(texto))
    m["temas_comentarios_negativos"] = {k: round(float(texto.str.contains(v, regex=True).mean()), 4) for k, v in temas.items()}

    # Pedidos com mais de um item / mais de um vendedor
    n_itens = it.groupby("order_id").size()
    n_vend = it.groupby("order_id").seller_id.nunique()
    a = a.join(n_itens.rename("n_itens"), on="order_id").join(n_vend.rename("n_vend"), on="order_id")
    m["pedidos_multi_item"] = round(float((a.n_itens > 1).mean()), 4)
    m["notas_baixas_multi_item"] = round(float((a[a.n_itens > 1].review_score <= 2).mean()), 4)
    m["notas_baixas_item_unico"] = round(float((a[a.n_itens == 1].review_score <= 2).mean()), 4)
    m["pedidos_multi_vendedor"] = round(float((a.n_vend > 1).mean()), 4)
    m["notas_baixas_multi_vendedor"] = round(float((a[a.n_vend > 1].review_score <= 2).mean()), 4)

    # Recompra
    oc = o.merge(c, on="customer_id")
    n_ped = oc.groupby("customer_unique_id").order_id.nunique()
    m["clientes_recompra"] = round(float((n_ped > 1).mean()), 4)
    oc = oc.merge(d[["order_id", "atraso"]], on="order_id", how="left").sort_values("order_purchase_timestamp")
    primeiro = oc.groupby("customer_unique_id").head(1).copy()
    primeiro["recomprou"] = primeiro.customer_unique_id.map(n_ped) > 1
    # só clientes com ao menos ~6 meses de janela para voltar a comprar
    janela = primeiro[primeiro.order_purchase_timestamp < "2018-03-01"]
    m["recompra_janela_6m"] = round(float(janela.recomprou.mean()), 4)
    m["recompra_primeiro_no_prazo"] = round(float(janela[janela.atraso == False].recomprou.mean()), 4)  # noqa: E712
    m["recompra_primeiro_atrasado"] = round(float(janela[janela.atraso == True].recomprou.mean()), 4)  # noqa: E712

    # Vendedores e catálogo
    receita = it.groupby("seller_id").price.sum().sort_values(ascending=False)
    m["receita_top10pct_vendedores"] = round(float(receita.head(int(len(receita) * 0.1)).sum() / receita.sum()), 4)
    m["vendedores_sp"] = round(float((s.seller_state == "SP").mean()), 4)
    m["produtos_sem_categoria"] = round(float(pr.product_category_name.isna().mean()), 4)
    cat = it.merge(pr[["product_id", "product_category_name"]], on="product_id").drop_duplicates(
        ["order_id", "product_category_name"]).merge(rv1[["order_id", "review_score"]], on="order_id")
    cg = cat.groupby("product_category_name").agg(pedidos=("order_id", "size"), nota=("review_score", "mean"),
                                                  baixas=("review_score", lambda x: (x <= 2).mean()))
    m["categorias_mais_vendidas"] = cg.sort_values("pedidos", ascending=False).head(5).round(4).to_dict(orient="index")
    m["categorias_mais_criticadas"] = cg[cg.pedidos >= 500].sort_values("baixas", ascending=False).head(5).round(4).to_dict(orient="index")

    return m, d, dist


def fig_volume_atraso(t, d):
    o = t["orders"]
    ini, fim = pd.Period("2017-01", "M"), pd.Period("2018-08", "M")
    vol = o.groupby(o.order_purchase_timestamp.dt.to_period("M")).size()
    vol = vol[(vol.index >= ini) & (vol.index <= fim)]
    atr = d.groupby("mes").atraso.mean()
    atr = atr[(atr.index >= ini) & (atr.index <= fim)]
    rot = [f"{MESES[p.month - 1]}\n{str(p.year)[2:]}" if p.month in (1, 4, 7, 10) else "" for p in vol.index]
    x = np.arange(len(vol))
    media = d.atraso.mean()

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(6.3, 3.9), sharex=True, gridspec_kw={"hspace": 0.45})
    ax1.bar(x, vol.values, width=0.62, color=AZUL, zorder=2)
    ax1.set_title("Pedidos por mês", loc="left", fontsize=9, color=TINTA, fontweight="semibold", pad=6)
    ax1.yaxis.grid(True, color=GRADE, linewidth=0.6, zorder=0)
    ax1.set_yticks([0, 2000, 4000, 6000, 8000])
    ax1.set_yticklabels(["0", "2.000", "4.000", "6.000", "8.000"])
    ax1.tick_params(axis="both", length=0)
    i_nov = list(vol.index).index(pd.Period("2017-11", "M"))
    ax1.annotate("Black Friday\n7.544 pedidos", (x[i_nov], vol.iloc[i_nov]), xytext=(-46, -2),
                 textcoords="offset points", fontsize=7.6, color=TINTA_2, ha="right", va="top",
                 arrowprops=dict(arrowstyle="-", color=MUTED, lw=0.6))

    ax2.plot(x, atr.values * 100, color=AZUL_ESCURO, lw=1.6, solid_capstyle="round", zorder=3)
    ax2.axhline(media * 100, color=MUTED, lw=0.7, zorder=1)
    ax2.text(x[-1] + 0.4, media * 100 + 0.6, f"média {pct(media)}", fontsize=7.6, color=TINTA_2, ha="right", va="bottom")
    ax2.set_title("Entregas com atraso (% dos pedidos entregues)", loc="left", fontsize=9, color=TINTA,
                  fontweight="semibold", pad=6)
    ax2.yaxis.grid(True, color=GRADE, linewidth=0.6, zorder=0)
    ax2.set_yticks([0, 5, 10, 15, 20])
    ax2.set_yticklabels(["0%", "5%", "10%", "15%", "20%"])
    ax2.set_ylim(0, 22)
    ax2.tick_params(axis="both", length=0)
    for per, dx in [("2017-11", -6), ("2018-03", 6)]:
        i = list(atr.index).index(pd.Period(per, "M"))
        ax2.scatter([x[i]], [atr.iloc[i] * 100], s=22, color=AZUL_ESCURO, edgecolor="white", linewidth=1.2, zorder=4)
        ax2.text(x[i] + (dx / 10), atr.iloc[i] * 100 + 0.2, pct(atr.iloc[i]), fontsize=7.6, color=TINTA,
                 ha="right" if dx < 0 else "left", va="bottom")
    ax2.set_xticks(x)
    ax2.set_xticklabels(rot, fontsize=7.6)
    fig.savefig(FIG / "fig_volume_atraso.svg", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def fig_atraso_uf(m):
    uf = pd.DataFrame(m["atraso_por_uf"]).T.sort_values("atraso", ascending=False)
    media = m["taxa_atraso"]
    x = np.arange(len(uf))
    fig, ax = plt.subplots(figsize=(6.3, 2.35))
    ax.bar(x, uf.atraso * 100, width=0.62, color=AZUL, zorder=2)
    ax.axhline(media * 100, color=MUTED, lw=0.7, zorder=3)
    ax.text(len(uf) - 0.6, media * 100 + 0.5, f"média nacional {pct(media)}", fontsize=7.6, color=TINTA_2, ha="right", va="bottom")
    destaque = {"AL", "MA", "SE", "RJ", "SP"}
    for i, (sigla, row) in enumerate(uf.iterrows()):
        if sigla in destaque:
            ax.text(i, row.atraso * 100 + 0.5, pct(row.atraso, 0) if row.atraso >= 0.1 else pct(row.atraso),
                    fontsize=7, color=TINTA, ha="center", va="bottom")
    ax.set_xticks(x)
    ax.set_xticklabels(uf.index, fontsize=7.3)
    ax.set_yticks([0, 5, 10, 15, 20])
    ax.set_yticklabels(["0%", "5%", "10%", "15%", "20%"])
    ax.set_ylim(0, 24)
    ax.yaxis.grid(True, color=GRADE, linewidth=0.6, zorder=0)
    ax.tick_params(axis="both", length=0)
    fig.savefig(FIG / "fig_atraso_uf.svg", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def fig_notas(m, dist):
    ordem = ["Entregue no prazo", "Entregue com atraso", "Não entregue"]
    dist = dist.loc[ordem]
    fig, ax = plt.subplots(figsize=(6.3, 1.9))
    y = np.arange(len(ordem))[::-1]
    gap = 0.004
    for j, nota in enumerate([1, 2, 3, 4, 5]):
        esquerda = dist[[n for n in [1, 2, 3, 4, 5] if n < nota]].sum(axis=1).values
        larg = dist[nota].values
        ax.barh(y, larg - gap, left=esquerda + gap / 2, height=0.5, color=DIVERGENTE[j], zorder=2)
        for yi, l, w in zip(y, esquerda, larg):
            if w >= 0.06:
                cor = "white" if j in (0, 4) else TINTA
                ax.text(l + w / 2, yi, pct(w, 0), ha="center", va="center", fontsize=7.3, color=cor)
    for yi, sit in zip(y, ordem):
        media = m["nota_media_por_situacao"][sit]
        n = m["pedidos_por_situacao"][sit]
        ax.text(1.02, yi, f"nota média {str(media).replace('.', ',')}", va="center", fontsize=7.6, color=TINTA)
        ax.text(1.02, yi - 0.3, f"{n:,} pedidos".replace(",", "."), va="center", fontsize=6.9, color=MUTED)
    ax.set_yticks(y)
    ax.set_yticklabels(ordem, fontsize=8, color=TINTA)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.spines[["bottom", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    hs = [plt.Rectangle((0, 0), 1, 1, color=c) for c in DIVERGENTE]
    ax.legend(hs, ["1 estrela", "2", "3", "4", "5 estrelas"], ncol=5, loc="lower left", bbox_to_anchor=(0, 1.0),
              frameon=False, fontsize=7.6, handlelength=1.0, handleheight=0.8, columnspacing=1.2, borderaxespad=0.2)
    fig.savefig(FIG / "fig_notas_situacao.svg", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def fig_temas(m):
    temas = pd.Series(m["temas_comentarios_negativos"]).sort_values()
    fig, ax = plt.subplots(figsize=(6.3, 1.85))
    y = np.arange(len(temas))
    ax.barh(y, temas.values * 100, height=0.55, color=AZUL, zorder=2)
    for yi, v in zip(y, temas.values):
        ax.text(v * 100 + 0.8, yi, pct(v, 0), va="center", fontsize=7.6, color=TINTA)
    ax.set_yticks(y)
    ax.set_yticklabels(temas.index, fontsize=8, color=TINTA)
    ax.set_xlim(0, 55)
    ax.set_xticks([0, 10, 20, 30, 40, 50])
    ax.set_xticklabels(["0%", "10%", "20%", "30%", "40%", "50%"])
    ax.xaxis.grid(True, color=GRADE, linewidth=0.6, zorder=0)
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="both", length=0)
    fig.savefig(FIG / "fig_temas_reclamacoes.svg", bbox_inches="tight", pad_inches=0.04)
    plt.close(fig)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    FIG.mkdir(parents=True, exist_ok=True)
    configurar_fontes()
    t = carregar(sys.argv[1])
    m, d, dist = analisar(t)
    fig_volume_atraso(t, d)
    fig_atraso_uf(m)
    fig_notas(m, dist)
    fig_temas(m)
    SAIDA.write_text(json.dumps(m, ensure_ascii=False, indent=2, default=str))
    print(json.dumps({k: v for k, v in m.items() if not isinstance(v, dict)}, ensure_ascii=False, indent=1))
    for k in ["nota_media_por_situacao", "notas_baixas_por_situacao", "composicao_notas_baixas",
              "temas_comentarios_negativos", "categorias_mais_criticadas"]:
        print(k, json.dumps(m[k], ensure_ascii=False))


if __name__ == "__main__":
    main()
