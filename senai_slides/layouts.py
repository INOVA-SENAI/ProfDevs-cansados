"""Layouts dos slides de conteúdo.

Os nove primeiros (topicos a tabela) vêm do gerador de slides do repositório icrcode/teste-kiro
(licença MIT; ver LICENSES/teste-kiro.txt). `ilustracao` (com a imagem gerada pela Amazon
Bedrock) e `diagrama` (círculo central, modelo em .kiro/steering/referencias/) são deste
projeto.
"""

import io
import math

import numpy as np
from matplotlib.ticker import FuncFormatter
from PIL import Image

from senai_slides import diagrama as dg
from senai_slides import tema as t
from senai_slides.tema import (
    AZUL,
    AZUL_BG,
    AZUL_TXT,
    BRANCO,
    CINZA,
    H_AZUL,
    H_BRANCO,
    H_CINZA,
    H_LARANJA,
    H_SERIE_1,
    H_SERIE_2,
    H_SERIE_3,
    H_TINTA,
    LAR_BG,
    LARANJA,
    SUPERF,
    TINTA,
    X0,
    X1,
    Y0,
    Y1,
    I,
    rgb,
)

# Gráficos


def _num(v) -> str:
    """Formato pt-BR: 1.234, 12,5, 7."""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return ""
    if abs(v) >= 1000:
        return f"{v:,.0f}".replace(",", ".")
    if float(v).is_integer():
        return str(int(v))
    return f"{v:.1f}".replace(".", ",")


def _cores_series(n: int) -> list[str]:
    return {1: [H_SERIE_2], 2: [H_SERIE_2, H_SERIE_3]}.get(n, [H_SERIE_1, H_SERIE_2, H_SERIE_3])


def _matriz(g: dict):
    categorias = g["categorias"][:12]
    series = []
    for s in g["series"][:3]:
        valores = list(s["valores"][: len(categorias)])
        valores += [np.nan] * (len(categorias) - len(valores))
        series.append((s["nome"], np.array(valores, float)))
    return categorias, series


def _girar_rotulos(ax, categorias) -> None:
    if max(len(c) for c in categorias) * len(categorias) > 70:
        for rotulo in ax.get_xticklabels():
            rotulo.set_rotation(25)
            rotulo.set_ha("right")


def g_barras(w, h, g, horizontal=False):
    categorias, series = _matriz(g)
    cores = _cores_series(len(series))
    fig, ax = t.figura(w, h)
    n = len(series)
    largura = 0.8 / n
    pos = np.arange(len(categorias))
    rotular = len(categorias) * n <= 16
    for i, ((nome, valores), cor) in enumerate(zip(series, cores, strict=False)):
        deslocado = pos + (i - (n - 1) / 2) * largura
        if horizontal:
            barras = ax.barh(deslocado, valores, largura * 0.95, label=nome, color=cor, zorder=3)
        else:
            barras = ax.bar(
                deslocado,
                valores,
                largura,
                label=nome,
                color=cor,
                edgecolor=H_BRANCO,
                linewidth=1.5,
                zorder=3,
            )
        if rotular:
            ax.bar_label(
                barras,
                labels=[_num(v) for v in valores],
                padding=3,
                fontsize=9.5,
                color=H_TINTA,
                fontweight="semibold",
            )
    formato = FuncFormatter(lambda v, _: _num(v))
    if horizontal:
        ax.set_yticks(pos, categorias, color=H_TINTA)
        ax.invert_yaxis()
        ax.xaxis.set_major_formatter(formato)
        ax.xaxis.grid(True)
        ax.spines["left"].set_visible(True)
        if g.get("eixo_y"):
            ax.set_xlabel(g["eixo_y"])
        ax.margins(x=0.12)
    else:
        ax.set_xticks(pos, categorias)
        _girar_rotulos(ax, categorias)
        ax.yaxis.set_major_formatter(formato)
        ax.yaxis.grid(True)
        if g.get("eixo_y"):
            ax.set_ylabel(g["eixo_y"])
        ax.margins(y=0.14)
    ax.set_axisbelow(True)
    if n > 1:
        ax.legend(loc="upper right", ncols=n, handlelength=1.1)
    return t.png(fig)


def g_linhas(w, h, g):
    categorias, series = _matriz(g)
    cores = _cores_series(len(series))
    x = np.arange(len(categorias), dtype=float)
    fig, ax = t.figura(w, h)
    for (nome, valores), cor in zip(series, cores, strict=False):
        ax.plot(*t.suave(x, valores), color=cor, lw=2.4, label=nome, zorder=3)
        ax.scatter(x, valores, s=40, color=cor, edgecolor=H_BRANCO, lw=1.5, zorder=4)
        validos = np.where(~np.isnan(valores))[0]
        if len(validos) and len(series) == 1:  # com várias séries, a legenda identifica
            k = validos[-1]
            ax.annotate(
                _num(valores[k]),
                (x[k], valores[k]),
                xytext=(0, 9),
                textcoords="offset points",
                ha="center",
                fontsize=10,
                color=H_TINTA,
                fontweight="semibold",
            )
    ax.set_xticks(x, categorias)
    _girar_rotulos(ax, categorias)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: _num(v)))
    ax.yaxis.grid(True)
    ax.set_axisbelow(True)
    ax.margins(y=0.15)
    if g.get("eixo_y"):
        ax.set_ylabel(g["eixo_y"])
    if len(series) > 1:
        ax.legend(loc="upper left")
    return t.png(fig)


def g_pizza(w, h, g):
    categorias, series = _matriz(g)
    valores = np.nan_to_num(series[0][1])
    pares = sorted(zip(categorias, valores, strict=True), key=lambda p: -p[1])
    if len(pares) > 4:  # agrupa a cauda em "Outros"
        pares = pares[:3] + [("Outros", sum(v for _, v in pares[3:]))]
    rotulos, valores = zip(*pares, strict=True)
    total = sum(valores) or 1
    cores = [H_SERIE_2, H_SERIE_3, H_SERIE_1, "#B8C4D9"][: len(valores)]
    fig, ax = t.figura(w, h)
    fatias, _ = ax.pie(
        valores,
        colors=cores,
        startangle=90,
        counterclock=False,
        wedgeprops={"width": 0.34, "edgecolor": H_BRANCO, "linewidth": 3},
    )
    for fatia, rotulo, v in zip(fatias, rotulos, valores, strict=True):
        angulo = np.deg2rad((fatia.theta1 + fatia.theta2) / 2)
        ax.text(
            np.cos(angulo) * 1.36,
            np.sin(angulo) * 1.3,
            f"{v / total:.0%}\n{rotulo}",
            ha="center",
            va="center",
            fontsize=10.5,
            color=H_TINTA,
            fontweight="semibold",
            linespacing=1.15,
        )
    ax.text(
        0,
        0.06,
        f"{valores[0] / total:.0%}",
        ha="center",
        va="center",
        fontsize=22,
        fontweight="bold",
        color=H_AZUL,
    )
    ax.text(0, -0.24, rotulos[0][:18].lower(), ha="center", va="center", fontsize=10, color=H_CINZA)
    ax.set_xlim(-1.8, 1.8)
    ax.set_ylim(-1.6, 1.6)
    ax.set_aspect("equal")
    return t.png(fig)


GRAFICOS = {
    "barras": g_barras,
    "barras_horizontais": lambda w, h, g: g_barras(w, h, g, horizontal=True),
    "linhas": g_linhas,
    "pizza": g_pizza,
}


# Layouts


def l_topicos(ctx, sl, s, _imagem=None):
    itens = s["itens"][:6]
    if not itens:
        return l_destaque(ctx, sl, s)
    n = len(itens)
    colunas = 1 if n <= 3 else 2
    linhas = math.ceil(n / colunas)
    gap = 0.22
    cw = (X1 - X0 - 0.3 * (colunas - 1)) / colunas
    area = Y1 - Y0 - (0.95 if s["destaque"] else 0)
    rh = min(1.8, (area - gap * (linhas - 1)) / linhas)
    for i, item in enumerate(itens):
        c, r = divmod(i, linhas)
        _cartao_de_item(sl, item, i, X0 + c * (cw + 0.3), Y0 + r * (rh + gap), cw, rh)
    if s["destaque"]:
        t.faixa_destaque(sl, s["destaque"], Y1 - 0.7)


def _cartao_de_item(sl, item, i, x, y, cw, rh):
    """Cartão com ícone à esquerda, título e texto (usado em topicos e ilustracao)."""
    t.cartao(sl, x, y, cw, rh)
    d = min(0.72, rh - 0.36)
    fundo, cor = t.cores_badge(i)
    t.icone_badge(sl, item["icone"], x + 0.25, y + (rh - d) / 2, d, fundo, cor)
    tx = x + 0.25 + d + 0.28
    largura = cw - (tx - x) - 0.25
    if item["texto"]:
        t.txt_fit(sl, item["titulo"], tx, y + 0.15, largura, 0.42, 17, bold=True)
        t.txt_fit(sl, item["texto"], tx, y + 0.6, largura, rh - 0.72, 13.5, cor=CINZA, espaco=1.1)
    else:
        t.txt_fit(sl, item["titulo"], tx, y + 0.1, largura, rh - 0.2, 17, bold=True, anchor="m")


def l_cartoes(ctx, sl, s, _imagem=None):
    itens = s["itens"][:4]
    if len(itens) < 2:
        return l_topicos(ctx, sl, s)
    n = len(itens)
    cw = (X1 - X0 - (n - 1) * 0.3) / n
    ch = Y1 - Y0 - (1.05 if s["destaque"] else 0)
    for i, item in enumerate(itens):
        x = X0 + i * (cw + 0.3)
        t.cartao(sl, x, Y0, cw, ch)
        fundo, cor = t.cores_badge(i)
        t.icone_badge(sl, item["icone"], x + 0.3, Y0 + 0.32, 0.9, fundo, cor)
        t.txt_fit(sl, item["titulo"], x + 0.3, Y0 + 1.42, cw - 0.55, 0.75, 18, bold=True)
        t.txt_fit(
            sl,
            item["texto"],
            x + 0.3,
            Y0 + 2.25,
            cw - 0.55,
            ch - 2.45,
            13.5,
            cor=CINZA,
            espaco=1.15,
        )
    if s["destaque"]:
        t.faixa_destaque(sl, s["destaque"], Y1 - 0.7)


def l_numeros(ctx, sl, s, _imagem=None):
    itens = s["itens"][:4]
    if not itens:
        return l_destaque(ctx, sl, s)
    n = len(itens)
    kw = (X1 - X0 - (n - 1) * 0.3) / n
    kh = min(3.2, Y1 - Y0 - (1.05 if s["destaque"] else 0))
    for i, item in enumerate(itens):
        x = X0 + i * (kw + 0.3)
        t.cartao(sl, x, Y0, kw, kh)
        fundo, cor = (LAR_BG, H_LARANJA) if i == 0 else (AZUL_BG, H_AZUL)
        t.icone_badge(sl, item["icone"], x + 0.28, Y0 + 0.28, 0.7, fundo, cor)
        t.txt_fit(
            sl,
            item["valor"] or "—",
            x + 0.28,
            Y0 + 1.12,
            kw - 0.5,
            0.8,
            38,
            bold=True,
            cor=LARANJA if i == 0 else AZUL,
        )
        t.txt_fit(sl, item["titulo"], x + 0.28, Y0 + 1.95, kw - 0.5, 0.42, 14, bold=True)
        if item["texto"]:
            t.txt_fit(
                sl,
                item["texto"],
                x + 0.28,
                Y0 + 2.4,
                kw - 0.5,
                kh - 2.55,
                12,
                cor=CINZA,
                espaco=1.1,
            )
    if s["destaque"]:
        t.faixa_destaque(sl, s["destaque"], Y1 - 0.7, icone_nome="insights")


def l_processo(ctx, sl, s, _imagem=None):
    itens = s["itens"][:6]
    if len(itens) < 2:
        return l_topicos(ctx, sl, s)
    n, gap = len(itens), 0.3
    nw = (X1 - X0 - (n - 1) * gap) / n
    ny, nh = Y0 + 0.3, 2.05
    for i, item in enumerate(itens):
        x = X0 + i * (nw + gap)
        fundo, cor = t.cores_badge(i)
        t.cartao(sl, x, ny, nw, nh)
        t.icone_badge(sl, item["icone"], x + (nw - 0.8) / 2, ny + 0.3, 0.8, fundo, cor)
        t.txt_fit(
            sl,
            item["titulo"],
            x + 0.1,
            ny + 1.22,
            nw - 0.2,
            0.7,
            14.5,
            bold=True,
            align="c",
            anchor="m",
        )
        t.numero(sl, i + 1, x + nw - 0.32, ny - 0.14, 0.4, LARANJA if i % 2 else AZUL)
        altura = 1.0 if s["destaque"] else 1.3
        t.txt_fit(
            sl, item["texto"], x, ny + nh + 0.15, nw, altura, 12.5, cor=CINZA, align="c", espaco=1.1
        )
        if i < n - 1:
            t.icone(
                sl, "arrow_forward", x + nw + (gap - 0.26) / 2, ny + nh / 2 - 0.13, 0.26, H_CINZA
            )
    if s["destaque"]:
        t.faixa_destaque(sl, s["destaque"], Y1 - 0.7, icone_nome="bolt")


def l_linha_do_tempo(ctx, sl, s, _imagem=None):
    itens = s["itens"][:5]
    if len(itens) < 2:
        return l_topicos(ctx, sl, s)
    n = len(itens)
    cw = (X1 - X0 - (n - 1) * 0.3) / n
    ly = Y0 + 1.0
    t.rect(sl, X0 + cw / 2, ly - 0.015, (X1 - X0) - cw, 0.03, fill=t.LINHA)
    for i, item in enumerate(itens):
        x = X0 + i * (cw + 0.3)
        cx = x + cw / 2
        t.txt_fit(
            sl,
            (item["valor"] or f"Etapa {i + 1}").upper(),
            x,
            Y0,
            cw,
            0.35,
            12,
            bold=True,
            cor=LARANJA,
            align="c",
        )
        t.circulo(sl, cx - 0.45, ly - 0.45, 0.9, BRANCO)
        fundo, cor = (LAR_BG, H_LARANJA) if i == 0 else (AZUL_BG, H_AZUL)
        t.icone_badge(sl, item["icone"], cx - 0.4, ly - 0.4, 0.8, fundo, cor)
        topo = ly + 0.75
        t.cartao(sl, x, topo, cw, Y1 - topo)
        t.txt_fit(sl, item["titulo"], x + 0.25, topo + 0.2, cw - 0.5, 0.75, 17, bold=True)
        t.txt_fit(
            sl,
            item["texto"],
            x + 0.25,
            topo + 1.0,
            cw - 0.5,
            Y1 - topo - 1.2,
            13,
            cor=CINZA,
            espaco=1.15,
        )


def l_comparacao(ctx, sl, s, _imagem=None):
    colunas = s["colunas"][:2]
    if len(colunas) < 2:
        return l_topicos(ctx, sl, s)
    cw = (X1 - X0 - 0.4) / 2
    base = Y1 - (0.95 if s["destaque"] else 0)
    for i, coluna in enumerate(colunas):
        x = X0 + i * (cw + 0.4)
        t.rect(sl, x, Y0, cw, 0.7, fill=AZUL if i == 0 else LARANJA, raio=0.15)
        t.txt_fit(
            sl,
            coluna["titulo"],
            x + 0.3,
            Y0 + 0.08,
            cw - 0.6,
            0.54,
            18,
            bold=True,
            cor=BRANCO,
            anchor="m",
        )
        topo = Y0 + 0.85
        t.cartao(sl, x, topo, cw, base - topo)
        itens = coluna["itens"][:6]
        passo = min(0.8, (base - topo - 0.3) / max(len(itens), 1))
        for k, texto in enumerate(itens):
            y = topo + 0.2 + k * passo
            t.icone(sl, "check_circle", x + 0.3, y + 0.04, 0.3, H_AZUL if i == 0 else H_LARANJA)
            t.txt_fit(sl, texto, x + 0.78, y, cw - 1.05, passo - 0.08, 14, cor=TINTA, espaco=1.1)
    if s["destaque"]:
        t.faixa_destaque(sl, s["destaque"], Y1 - 0.7, icone_nome="compare_arrows")


def l_grafico(ctx, sl, s, _imagem=None):
    g = s["grafico"]
    if not g:
        return l_topicos(ctx, sl, s)
    itens = s["itens"][:3]
    gw = 7.9 if itens else X1 - X0
    t.grafico(ctx, sl, GRAFICOS[g["tipo"]], X0, Y0 - 0.1, gw, 4.45, g)
    if g.get("fonte"):
        t.txt_fit(sl, f"Fonte: {g['fonte']}", X0, 6.45, gw, 0.3, 10.5, italic=True, cor=CINZA)
    if itens:
        dx = X0 + gw + 0.25
        t.cartao(sl, dx, Y0, X1 - dx, Y1 - Y0)
        passo = (Y1 - Y0 - 0.3) / len(itens)
        for i, item in enumerate(itens):
            y = Y0 + 0.25 + i * passo
            t.icone(sl, item["icone"], dx + 0.25, y + 0.02, 0.36, H_LARANJA if i == 0 else H_AZUL)
            t.txt_fit(sl, item["titulo"], dx + 0.75, y, X1 - dx - 1.0, 0.4, 14, bold=True)
            t.txt_fit(
                sl,
                item["texto"],
                dx + 0.75,
                y + 0.42,
                X1 - dx - 1.0,
                passo - 0.55,
                12,
                cor=CINZA,
                espaco=1.1,
            )


def l_destaque(ctx, sl, s, _imagem=None):
    texto = s["destaque"] or (s["itens"][0]["texto"] if s["itens"] else s["titulo"])
    t.rect(sl, X0, Y0, X1 - X0, Y1 - Y0, fill=AZUL, raio=0.05)
    t.icone(sl, "format_quote", X0 + 0.55, Y0 + 0.45, 0.9, H_LARANJA)
    t.txt_fit(
        sl, texto, X0 + 0.6, Y0 + 1.45, X1 - X0 - 1.2, 2.3, 32, bold=True, cor=BRANCO, espaco=1.1
    )
    if s["itens"] and s["destaque"]:
        item = s["itens"][0]
        t.rect(sl, X0 + 0.6, Y1 - 1.05, 0.9, 0.06, fill=LARANJA)
        rotulo = f"{item['titulo']}  ·  {item['texto']}" if item["texto"] else item["titulo"]
        t.txt_fit(sl, rotulo, X0 + 0.6, Y1 - 0.9, X1 - X0 - 1.2, 0.5, 15, cor=AZUL_TXT)


def l_tabela(ctx, sl, s, _imagem=None):
    tabela = s["tabela"]
    if not tabela:
        return l_topicos(ctx, sl, s)
    cabecalho = tabela["cabecalho"][:5]
    linhas = [(linha + [""] * len(cabecalho))[: len(cabecalho)] for linha in tabela["linhas"][:8]]
    pesos = [1.35] + [1] * (len(cabecalho) - 1)
    larguras = [(X1 - X0) * p / sum(pesos) for p in pesos]
    hh = 0.58
    rh = min(0.8, (Y1 - Y0 - hh - 0.06) / len(linhas))
    t.rect(sl, X0, Y0, X1 - X0, hh, fill=AZUL, raio=0.12)
    x = X0
    for titulo, w in zip(cabecalho, larguras, strict=True):
        t.txt_fit(
            sl,
            titulo,
            x + 0.2,
            Y0 + 0.06,
            w - 0.3,
            hh - 0.12,
            13,
            bold=True,
            cor=BRANCO,
            anchor="m",
        )
        x += w
    for r, linha in enumerate(linhas):
        y = Y0 + hh + 0.06 + r * rh
        if r % 2 == 0:
            t.rect(sl, X0, y, X1 - X0, rh - 0.04, fill=SUPERF, raio=0.1)
        x = X0
        for c, (celula, w) in enumerate(zip(linha, larguras, strict=True)):
            t.txt_fit(
                sl,
                celula,
                x + 0.2,
                y + 0.04,
                w - 0.3,
                rh - 0.12,
                14,
                bold=c == 0,
                cor=AZUL if c == 0 else TINTA,
                anchor="m",
            )
            x += w


def l_ilustracao(ctx, sl, s, imagem: Image.Image | None = None):
    """Itens à esquerda e a ilustração gerada pela Bedrock à direita. Sem imagem (gerado com
    --sem-imagens), vira um slide de tópicos."""
    if imagem is None:
        return l_topicos(ctx, sl, s)
    lado = Y1 - Y0 - (0.95 if s["destaque"] else 0)
    x_imagem = X1 - lado
    t.ilustracao(sl, imagem, x_imagem, Y0, lado)
    itens = s["itens"][:5]
    gap = 0.2
    cw = x_imagem - 0.35 - X0
    rh = min(1.5, (lado - gap * (len(itens) - 1)) / len(itens))
    for i, item in enumerate(itens):
        _cartao_de_item(sl, item, i, X0, Y0 + i * (rh + gap), cw, rh)
    if s["destaque"]:
        t.faixa_destaque(sl, s["destaque"], Y1 - 0.7)


def _pol(px: float) -> float:
    return px / dg.PX_POR_POL


def l_diagrama(ctx, sl, s, _imagem=None):
    """Título no círculo central e os itens em cartões coloridos em volta, com o ícone de cada
    item no círculo branco. Textos e ícones continuam editáveis no PowerPoint."""
    itens = s["itens"][:6]
    fundo = io.BytesIO()
    dg.fundo(len(itens)).save(fundo, "PNG", optimize=True)
    fundo.seek(0)
    sl.shapes.add_picture(fundo, 0, 0, I(t.W), I(t.H))

    largura = dg.CARTAO_LARGURA - dg.CARTAO_MARGEM - dg.RAIO_ICONE - 22
    for (x, y, lado), cor, item in zip(
        dg.posicoes(len(itens)), dg.cores(len(itens)), itens, strict=True
    ):
        if lado < 0:
            x_texto, alinhamento = x - dg.CARTAO_LARGURA + dg.CARTAO_MARGEM, "l"
        else:
            x_texto, alinhamento = x + dg.CARTAO_LARGURA - dg.CARTAO_MARGEM - largura, "r"
        t.txt_fit(
            sl,
            item["titulo"].upper(),
            _pol(x_texto),
            _pol(y - 62),
            _pol(largura),
            _pol(36),
            14,
            bold=True,
            cor=BRANCO,
            align=alinhamento,
            anchor="b",
        )
        t.txt_fit(
            sl,
            item["texto"],
            _pol(x_texto),
            _pol(y - 22),
            _pol(largura),
            _pol(88),
            12,
            cor=BRANCO,
            align=alinhamento,
            espaco=1.05,
        )
        tamanho = _pol(dg.RAIO_ICONE * 1.05)
        t.icone(sl, item["icone"], _pol(x) - tamanho / 2, _pol(y) - tamanho / 2, tamanho, cor)

    cx, cy = dg.CENTRO
    t.txt_fit(
        sl,
        s["titulo"].upper(),
        _pol(cx - 160),
        _pol(cy - 125),
        _pol(320),
        _pol(165),
        26,
        bold=True,
        cor=AZUL,
        align="c",
        anchor="m",
    )
    cores = dg.cores(len(itens))
    x0 = cx - 15 * (len(cores) - 1)
    for i, cor in enumerate(cores):
        t.circulo(sl, _pol(x0 + 30 * i - 8), _pol(cy + 62), _pol(16), rgb(cor))
    t.moldura_interna(ctx, sl)


LAYOUTS = {
    "topicos": l_topicos,
    "cartoes": l_cartoes,
    "numeros": l_numeros,
    "processo": l_processo,
    "linha_do_tempo": l_linha_do_tempo,
    "comparacao": l_comparacao,
    "grafico": l_grafico,
    "destaque": l_destaque,
    "tabela": l_tabela,
    "ilustracao": l_ilustracao,
    "diagrama": l_diagrama,
}


def slide_conteudo(ctx, s: dict, imagem: Image.Image | None = None) -> None:
    sl = t.novo_slide(ctx, s["notas"])
    if s["layout"] != "diagrama":  # o diagrama leva o título no círculo central
        t.cabecalho(ctx, sl, s["titulo"], s["subtitulo"])
    LAYOUTS[s["layout"]](ctx, sl, s, imagem)
    t.finalizar(ctx, sl)
