"""
Gerador de Relatório PDF Mensal — ImobFlow
Usa ReportLab para criar balancetes profissionais com identidade visual premium.
"""
from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# ── Paleta de cores ImobFlow ──────────────────────────────────────────────────
GOLD       = colors.HexColor("#C9A84C")
GOLD_DARK  = colors.HexColor("#A67C2E")
GOLD_LIGHT = colors.HexColor("#F0C040")
WINE       = colors.HexColor("#9B2335")
WINE_DARK  = colors.HexColor("#6B1A2A")
BG_DARK    = colors.HexColor("#0D0A07")
SURFACE    = colors.HexColor("#1A1410")
TEXT       = colors.HexColor("#E8DCC8")
SUBTEXT    = colors.HexColor("#8A7560")
WHITE      = colors.white
SUCCESS    = colors.HexColor("#4A9B6A")
DANGER     = colors.HexColor("#C0392B")


def _estilos():
    return {
        "titulo": ParagraphStyle("titulo",
            fontName="Times-Bold", fontSize=22,
            textColor=GOLD, alignment=TA_CENTER, spaceAfter=4),
        "subtitulo": ParagraphStyle("sub",
            fontName="Times-Italic", fontSize=11,
            textColor=SUBTEXT, alignment=TA_CENTER, spaceAfter=2),
        "h2": ParagraphStyle("h2",
            fontName="Times-Bold", fontSize=13,
            textColor=GOLD_DARK, spaceBefore=16, spaceAfter=8),
        "body": ParagraphStyle("body",
            fontName="Helvetica", fontSize=9,
            textColor=colors.HexColor("#C8B898"), leading=14),
        "body_bold": ParagraphStyle("body_bold",
            fontName="Helvetica-Bold", fontSize=9,
            textColor=TEXT),
        "total": ParagraphStyle("total",
            fontName="Times-Bold", fontSize=14,
            textColor=GOLD, alignment=TA_RIGHT),
        "footer": ParagraphStyle("footer",
            fontName="Helvetica", fontSize=7,
            textColor=SUBTEXT, alignment=TA_CENTER),
        "kpi_label": ParagraphStyle("kpi_label",
            fontName="Helvetica", fontSize=7,
            textColor=SUBTEXT, alignment=TA_CENTER),
        "kpi_value": ParagraphStyle("kpi_value",
            fontName="Times-Bold", fontSize=18,
            textColor=GOLD, alignment=TA_CENTER),
    }


def gerar_relatorio_pdf(condominio, lancamentos: list, mes: int, ano: int) -> bytes:
    """
    Gera PDF do balancete mensal.
    Retorna bytes do PDF pronto para download.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=2*cm,
        title=f"Balancete {mes:02d}/{ano} — {condominio.nome}",
        author="ImobFlow",
    )

    estilos = _estilos()
    story = []
    W = A4[0] - 4*cm  # largura útil

    # ── Cabeçalho ─────────────────────────────────────────────────────────────
    story.append(Paragraph("IMOBFLOW", estilos["titulo"]))
    story.append(Paragraph("Gestão Condominial Premium", estilos["subtitulo"]))
    story.append(HRFlowable(width=W, thickness=0.5, color=GOLD_DARK, spaceAfter=6))

    MESES = ["","Janeiro","Fevereiro","Março","Abril","Maio","Junho",
             "Julho","Agosto","Setembro","Outubro","Novembro","Dezembro"]
    story.append(Paragraph(
        f"BALANCETE MENSAL — {MESES[mes].upper()} {ano}",
        ParagraphStyle("bal", fontName="Helvetica-Bold", fontSize=10,
                       textColor=TEXT, alignment=TA_CENTER, spaceBefore=8, spaceAfter=2)
    ))
    story.append(Paragraph(condominio.nome, estilos["subtitulo"]))
    if condominio.endereco:
        story.append(Paragraph(
            f"{condominio.endereco} · {condominio.cidade or ''}",
            estilos["footer"]
        ))
    story.append(Spacer(1, 16))

    # ── KPIs em tabela ─────────────────────────────────────────────────────────
    lans_mes = [l for l in lancamentos
                if l.data.month == mes and l.data.year == ano]
    receitas = sum(l.valor for l in lans_mes if l.tipo == "receita")
    despesas = sum(l.valor for l in lans_mes if l.tipo == "despesa")
    saldo = receitas - despesas

    kpi_data = [[
        Paragraph("RECEITAS", estilos["kpi_label"]),
        Paragraph("DESPESAS", estilos["kpi_label"]),
        Paragraph("SALDO", estilos["kpi_label"]),
    ],[
        Paragraph(f"R$ {receitas:,.2f}", ParagraphStyle("kv_r", fontName="Times-Bold", fontSize=16, textColor=SUCCESS, alignment=TA_CENTER)),
        Paragraph(f"R$ {despesas:,.2f}", ParagraphStyle("kv_d", fontName="Times-Bold", fontSize=16, textColor=DANGER, alignment=TA_CENTER)),
        Paragraph(f"R$ {saldo:,.2f}", ParagraphStyle("kv_s", fontName="Times-Bold", fontSize=16, textColor=GOLD if saldo >= 0 else DANGER, alignment=TA_CENTER)),
    ]]

    kpi_table = Table(kpi_data, colWidths=[W/3]*3)
    kpi_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), SURFACE),
        ("ROWBACKGROUNDS", (0,0), (-1,-1), [SURFACE, SURFACE]),
        ("BOX", (0,0), (-1,-1), 0.5, GOLD_DARK),
        ("LINEAFTER", (0,0), (1,-1), 0.5, GOLD_DARK),
        ("TOPPADDING", (0,0), (-1,-1), 12),
        ("BOTTOMPADDING", (0,0), (-1,-1), 12),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 20))

    # ── Tabela de lançamentos ──────────────────────────────────────────────────
    story.append(Paragraph("Lançamentos do Período", estilos["h2"]))

    if lans_mes:
        headers = ["Data", "Descrição", "Categoria", "Tipo", "Valor"]
        rows = [headers]

        for l in sorted(lans_mes, key=lambda x: x.data):
            sinal = "+" if l.tipo == "receita" else "−"
            rows.append([
                l.data.strftime("%d/%m"),
                l.descricao[:40],
                l.categoria,
                l.tipo.capitalize(),
                f"{sinal} R$ {l.valor:,.2f}",
            ])

        # Linha de totais
        rows.append(["", "TOTAL DO MÊS", "", "",
                      f"R$ {saldo:,.2f}" if saldo >= 0 else f"−R$ {abs(saldo):,.2f}"])

        col_w = [1.5*cm, 7*cm, 3.5*cm, 2.2*cm, 3.3*cm]
        lan_table = Table(rows, colWidths=col_w, repeatRows=1)

        ts = TableStyle([
            # Cabeçalho
            ("BACKGROUND", (0,0), (-1,0), WINE_DARK),
            ("TEXTCOLOR", (0,0), (-1,0), GOLD),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 8),
            ("ALIGN", (0,0), (-1,0), "CENTER"),
            # Corpo
            ("FONTNAME", (0,1), (-1,-2), "Helvetica"),
            ("FONTSIZE", (0,1), (-1,-2), 8),
            ("TEXTCOLOR", (0,1), (-1,-2), colors.HexColor("#C8B898")),
            ("ROWBACKGROUNDS", (0,1), (-1,-2), [SURFACE, colors.HexColor("#1F1810")]),
            ("ALIGN", (4,1), (4,-1), "RIGHT"),
            # Total
            ("BACKGROUND", (0,-1), (-1,-1), colors.HexColor("#251E17")),
            ("TEXTCOLOR", (0,-1), (-1,-1), GOLD),
            ("FONTNAME", (0,-1), (-1,-1), "Times-Bold"),
            ("FONTSIZE", (0,-1), (-1,-1), 10),
            # Bordas
            ("GRID", (0,0), (-1,-2), 0.25, colors.HexColor("#3A2E24")),
            ("LINEABOVE", (0,-1), (-1,-1), 1, GOLD_DARK),
            # Padding
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ])

        # Colore valores de receita em verde e despesa em vermelho
        for i, l in enumerate(lans_mes, start=1):
            cor = SUCCESS if l.tipo == "receita" else DANGER
            ts.add("TEXTCOLOR", (4,i), (4,i), cor)
            ts.add("FONTNAME", (4,i), (4,i), "Helvetica-Bold")

        lan_table.setStyle(ts)
        story.append(lan_table)
    else:
        story.append(Paragraph("Nenhum lançamento neste período.", estilos["body"]))

    # ── Distribuição por categoria ─────────────────────────────────────────────
    story.append(Spacer(1, 20))
    story.append(Paragraph("Distribuição por Categoria", estilos["h2"]))

    cats: dict[str, float] = {}
    for l in lans_mes:
        if l.tipo == "despesa":
            cats[l.categoria] = cats.get(l.categoria, 0) + l.valor

    if cats and despesas > 0:
        cat_data = [["Categoria", "Valor", "% do Total"]]
        for cat, val in sorted(cats.items(), key=lambda x: -x[1]):
            pct = val / despesas * 100
            cat_data.append([cat, f"R$ {val:,.2f}", f"{pct:.1f}%"])

        cat_table = Table(cat_data, colWidths=[8*cm, 4*cm, 3*cm])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), WINE_DARK),
            ("TEXTCOLOR", (0,0), (-1,0), GOLD),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,0), 8),
            ("FONTNAME", (0,1), (-1,-1), "Helvetica"),
            ("FONTSIZE", (0,1), (-1,-1), 8),
            ("TEXTCOLOR", (0,1), (-1,-1), colors.HexColor("#C8B898")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [SURFACE, colors.HexColor("#1F1810")]),
            ("GRID", (0,0), (-1,-1), 0.25, colors.HexColor("#3A2E24")),
            ("ALIGN", (1,0), (-1,-1), "RIGHT"),
            ("TOPPADDING", (0,0), (-1,-1), 6),
            ("BOTTOMPADDING", (0,0), (-1,-1), 6),
            ("LEFTPADDING", (0,0), (-1,-1), 8),
            ("RIGHTPADDING", (0,0), (-1,-1), 8),
        ]))
        story.append(cat_table)

    # ── Rodapé ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width=W, thickness=0.5, color=GOLD_DARK))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        f"Documento gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M')} · "
        f"ImobFlow — Gestão Condominial Premium · imobflow.com.br",
        estilos["footer"]
    ))
    story.append(Paragraph(
        "Este documento tem caráter informativo. Guarde-o para sua prestação de contas.",
        estilos["footer"]
    ))

    doc.build(story)
    return buffer.getvalue()
