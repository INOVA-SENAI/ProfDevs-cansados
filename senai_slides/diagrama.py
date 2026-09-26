"""Fundo do layout `diagrama`: círculo central com os itens em volta.

Segue o modelo `.kiro/steering/referencias/diagrama.png`. Faixas, cartões, anel pontilhado,
sombras e círculos viram uma imagem transparente do tamanho do slide; textos e ícones entram
por cima como elementos do PowerPoint, para continuarem editáveis. As medidas estão em pixels
de um slide de 1920x1080 (144 px por polegada); o desenho sai em 2x, para as bordas ficarem
suaves.
"""

import colorsys
import math

from PIL import Image, ImageDraw, ImageFilter, ImageOps

PX_POR_POL = 144
ESCALA = 2
LARGURA, ALTURA = 1920, 1080
CENTRO = (995, 565)
RAIO_CENTRO, RAIO_ANEL, RAIO_ICONE = 205, 370, 64
CARTAO_LARGURA, CARTAO_ALTURA, CARTAO_MARGEM = 490, 180, 64
LARGURA_FAIXA = 46
# Distância vertical de cada item ao centro, conforme quantos itens há de cada lado.
DESLOCAMENTOS = {1: [0], 2: [-150, 150], 3: [-265, 0, 265]}
# Laranja, verde e os azuis são da marca; âmbar e turquesa completam as 6 cores.
CORES = ["#E84910", "#F08A00", "#52AE32", "#009E96", "#008AD1", "#164194"]


def posicoes(n: int) -> list[tuple[int, int, int]]:
    """(x, y, lado) do círculo de cada item: a primeira metade à esquerda, o resto à direita."""
    cx, cy = CENTRO
    esquerda = (n + 1) // 2
    resultado = []
    for lado, quantidade in ((-1, esquerda), (1, n - esquerda)):
        for dy in DESLOCAMENTOS[quantidade]:
            dx = math.sqrt(RAIO_ANEL**2 - dy**2)
            resultado.append((round(cx + lado * dx), cy + dy, lado))
    return resultado


def cores(n: int) -> list[str]:
    # Espalha os itens pela paleta, para o laranja e o azul aparecerem mesmo com poucos itens.
    ultima = len(CORES) - 1
    return [CORES[round(i * ultima / (n - 1))] for i in range(n)]


def _rgb(hexa: str) -> tuple[int, int, int]:
    return tuple(int(hexa[i : i + 2], 16) for i in (1, 3, 5))


def _circulo(x: float, y: float, raio: float) -> tuple[float, ...]:
    e = ESCALA
    return (e * (x - raio), e * (y - raio), e * (x + raio), e * (y + raio))


def _misturar(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    """Mistura em HSV: do laranja ao verde passa pelo amarelo, e não por um marrom."""
    ha, sa, va = colorsys.rgb_to_hsv(*(c / 255 for c in a))
    hb, sb, vb = colorsys.rgb_to_hsv(*(c / 255 for c in b))
    matiz = ha + ((hb - ha + 0.5) % 1 - 0.5) * t
    rgb = colorsys.hsv_to_rgb(matiz % 1, sa + (sb - sa) * t, va + (vb - va) * t)
    return tuple(round(c * 255) for c in rgb)


def _faixa(camada: Image.Image, lado: int, paradas: list[tuple[int, tuple]]) -> None:
    """Trecho do anel que liga os círculos de um lado, em degradê entre as cores dos itens."""
    e = ESCALA
    (y_inicio, _), (y_fim, _) = paradas[0], paradas[-1]
    coluna = Image.new("RGB", (1, (y_fim - y_inicio) * e))
    for py in range(coluna.height):
        y = y_inicio + py / e
        k = max(i for i in range(len(paradas) - 1) if paradas[i][0] <= y)
        (ya, cor_a), (yb, cor_b) = paradas[k], paradas[k + 1]
        coluna.putpixel((0, py), _misturar(cor_a, cor_b, (y - ya) / (yb - ya)))

    cx, cy = CENTRO
    mascara = Image.new("L", camada.size, 0)
    draw = ImageDraw.Draw(mascara)
    draw.ellipse(_circulo(cx, cy, RAIO_ANEL + LARGURA_FAIXA / 2), fill=255)
    draw.ellipse(_circulo(cx, cy, RAIO_ANEL - LARGURA_FAIXA / 2), fill=0)
    x0, x1 = (0, cx * e) if lado < 0 else (cx * e, camada.width)
    caixa = (x0, y_inicio * e, x1, y_fim * e)
    camada.paste(coluna.resize((x1 - x0, coluna.height)), caixa[:2], mascara.crop(caixa))


def _esfera(diametro: int) -> Image.Image:
    """Círculo branco com sombreado suave e o brilho no alto, à esquerda."""
    brilho = Image.radial_gradient("L").resize((diametro * 2, diametro * 2))
    x, y = round(diametro * 0.62), round(diametro * 0.70)
    brilho = brilho.crop((x, y, x + diametro, y + diametro))
    esfera = ImageOps.colorize(brilho, black="#FFFFFF", white=(196, 204, 218), mid=(240, 243, 247))
    mascara = Image.new("L", (diametro, diametro), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, diametro - 1, diametro - 1), fill=255)
    esfera.putalpha(mascara)
    return esfera


def fundo(n: int) -> Image.Image:
    """Imagem RGBA transparente, em 2x, com tudo o que não é texto nem ícone."""
    e = ESCALA
    cx, cy = CENTRO
    lista = posicoes(n)
    paleta = [_rgb(c) for c in cores(n)]
    camada = Image.new("RGBA", (LARGURA * e, ALTURA * e), (0, 0, 0, 0))

    for lado in (-1, 1):
        paradas = [
            (y, cor) for (_, y, lado_), cor in zip(lista, paleta, strict=True) if lado_ == lado
        ]
        if len(paradas) > 1:
            _faixa(camada, lado, paradas)
    draw = ImageDraw.Draw(camada)
    meia = CARTAO_ALTURA / 2
    for (x, y, lado), cor in zip(lista, paleta, strict=True):
        x0, x1 = (x - CARTAO_LARGURA, x) if lado < 0 else (x, x + CARTAO_LARGURA)
        draw.rounded_rectangle(
            (x0 * e, (y - meia) * e, x1 * e, (y + meia) * e), radius=meia * e, fill=cor
        )
    for k in range(44):
        angulo = 2 * math.pi * k / 44
        x = cx + (RAIO_CENTRO + 50) * math.cos(angulo)
        y = cy + (RAIO_CENTRO + 50) * math.sin(angulo)
        draw.ellipse(_circulo(x, y, 3.5), fill=(180, 188, 200))

    sombra = Image.new("L", camada.size, 0)
    draw = ImageDraw.Draw(sombra)
    draw.ellipse(_circulo(cx + 10, cy + 20, RAIO_CENTRO), fill=110)
    for x, y, _ in lista:
        draw.ellipse(_circulo(x + 5, y + 10, RAIO_ICONE), fill=120)
    escura = Image.new("RGBA", camada.size, (20, 30, 50, 0))
    escura.putalpha(sombra.filter(ImageFilter.GaussianBlur(16 * e)))
    camada.alpha_composite(escura)

    canto = ((cx - RAIO_CENTRO) * e, (cy - RAIO_CENTRO) * e)
    camada.alpha_composite(_esfera(2 * RAIO_CENTRO * e), canto)
    esfera = _esfera(2 * RAIO_ICONE * e)
    for x, y, _ in lista:
        camada.alpha_composite(esfera, ((x - RAIO_ICONE) * e, (y - RAIO_ICONE) * e))
    return camada
