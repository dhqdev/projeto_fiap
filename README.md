# Olist Intelligent Marketplace – Tech Challenge Fase 1

Relatório executivo da Fase 1 do Tech Challenge (FIAP Pós Tech – Agentes de IA).

**Entregável:** [`relatorio/Relatorio_Executivo_Olist_Fase1.pdf`](relatorio/Relatorio_Executivo_Olist_Fase1.pdf)

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `analise/analise_olist.py` | análise do dataset da Olist; gera `analise/metricas.json` e os gráficos |
| `relatorio/relatorio.html` | texto do relatório |
| `relatorio/estilo.css` | diagramação (A4, padrão ABNT para figuras, quadros e referências) |
| `relatorio/diagramas.py` | diagrama da arquitetura conceitual (Figura 6) |
| `relatorio/gerar_pdf.py` | monta o PDF final |
| `relatorio/figuras/` | gráficos e diagrama gerados |
| `relatorio/fontes/` | fontes Source Serif 4, Inter e IBM Plex Mono (SIL Open Font License) |

## Como regenerar

```bash
pip install pandas matplotlib weasyprint

# 1. baixar os CSVs do dataset (Kaggle olistbr/brazilian-ecommerce
#    ou github.com/olist/work-at-olist-data, pasta datasets/) para uma pasta, ex.: dados/
python analise/analise_olist.py dados/

# 2. montar o PDF
python relatorio/gerar_pdf.py
```

Antes de entregar, preencher na capa os nomes e RMs dos integrantes e, no capítulo 10, o link do vídeo.
