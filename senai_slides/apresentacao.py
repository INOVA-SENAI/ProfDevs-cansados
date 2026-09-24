import colorsys
import math
import re
import unicodedata
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ASSETS = Path(__file__).resolve().parent / "assets"

LARGURA, ALTURA = 1920, 1080
AZUL = (0x16, 0x41, 0x93)
AZUL_CLARO = (0x00, 0x8A, 0xD1)
LARANJA = (0xE8, 0x49, 0x0F)
VERDE = (0x52, 0xAE, 0x32)
BRANCO = (255, 255, 255)

MAX_TOPICOS = 6
MAX_ITENS = 6
ENTRELINHA = 1.2

# Diagrama: círculo central com os itens em volta. As formas são desenhadas em escala 2x e
# reduzidas no fim, para as bordas saírem suaves.
ESCALA = 2
CENTRO = (995, 565)
RAIO_CENTRO, RAIO_ANEL, RAIO_NUMERO = 205, 370, 64
CARTAO_LARGURA, CARTAO_ALTURA, CARTAO_MARGEM = 490, 180, 52
LARGURA_FAIXA = 46
# Distância vertical de cada item ao centro, conforme quantos itens há de cada lado.
DESLOCAMENTOS = {1: [0], 2: [-150, 150], 3: [-265, 0, 265]}
# Laranja, verde e os azuis são da paleta oficial; âmbar e turquesa completam as 6 cores.
CORES_DIAGRAMA = [LARANJA, (0xF0, 0x8A, 0x00), VERDE, (0x00, 0x9E, 0x96), AZUL_CLARO, AZUL]

# Century Gothic é a fonte do modelo; as demais são alternativas para quem não a tem.
_FONTES = {
    False: ["GOTHIC.TTF", "Century Gothic.ttf", "arial.ttf", "Arial.ttf", "DejaVuSans.ttf"],
    True: [
        "GOTHICB.TTF",
        "Century Gothic Bold.ttf",
        "arialbd.ttf",
        "Arial Bold.ttf",
        "DejaVuSans-Bold.ttf",
    ],
}

CONTATOS = [
    ("Rodovia Admar Gonzaga, 2765 | Itacorubi", BRANCO, False),
    ("88034-001 | Florianópolis - SC", BRANCO, False),
    None,
    ("sc.senai.br/", LARANJA, True),
    ("faleconosco@fiesc.com.br", BRANCO, False),
    None,
    ("(48) 3231 4100", BRANCO, False),
    ("0800 048 1212", BRANCO, False),
]


class TextoLongoDemais(ValueError):
    pass


@lru_cache
def _fonte(tamanho: int, negrito: bool = False) -> ImageFont.FreeTypeFont:
    for nome in _FONTES[negrito]:
        try:
            return ImageFont.truetype(nome, tamanho)
        except OSError:
            continue
    return ImageFont.load_default(tamanho)


def _quebrar(texto: str, fonte: ImageFont.FreeTypeFont, largura_max: int) -> list[str]:
    linhas: list[str] = []
    atual = ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if not atual or fonte.getlength(tentativa) <= largura_max:
            atual = tentativa
        else:
            linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


def _ajustar(
    texto: str,
    tamanho_max: int,
    tamanho_min: int,
    largura_max: int,
    max_linhas: int,
    negrito: bool = False,
) -> tuple[ImageFont.FreeTypeFont, list[str]]:
    for tamanho in range(tamanho_max, tamanho_min - 1, -2):
        fonte = _fonte(tamanho, negrito)
        linhas = _quebrar(texto, fonte, largura_max)
        if len(linhas) <= max_linhas and all(fonte.getlength(li) <= largura_max for li in linhas):
            return fonte, linhas
    raise TextoLongoDemais(f'Texto longo demais para caber no slide: "{texto}". Encurte-o.')


def _altura_linha(fonte: ImageFont.FreeTypeFont) -> int:
    return round(fonte.size * ENTRELINHA)


def _texto_obrigatorio(valor: object, campo: str) -> str:
    if not isinstance(valor, str) or not valor.strip():
        raise ValueError(f"{campo} precisa ser um texto não vazio.")
    return " ".join(valor.split())


def _colar_logo(slide: Image.Image, arquivo: str, x: int, y: int, largura: int) -> None:
    logo = Image.open(ASSETS / arquivo).convert("RGBA")
    logo = logo.crop(logo.getbbox())
    altura = round(logo.height * largura / logo.width)
    slide.alpha_composite(logo.resize((largura, altura), Image.Resampling.LANCZOS), (x, y))


def _base_interna() -> Image.Image:
    slide = Image.new("RGBA", (LARGURA, ALTURA), BRANCO)
    barra = Image.open(ASSETS / "barra_lateral.png").convert("RGBA")
    largura = round(barra.width * ALTURA / barra.height)
    slide.alpha_composite(barra.resize((largura, ALTURA), Image.Resampling.LANCZOS), (0, 0))
    _colar_logo(slide, "logo_senai_azul.png", x=1639, y=95, largura=178)
    return slide


def _escrever_de_baixo(draw, linhas, fonte, x, base, cor) -> None:
    passo = _altura_linha(fonte)
    for i, linha in enumerate(reversed(linhas)):
        draw.text((x, base - i * passo), linha, font=fonte, fill=cor, anchor="ls")


def _desenhar_capa(titulo: str) -> Image.Image:
    slide = Image.new("RGBA", (LARGURA, ALTURA), AZUL)
    _colar_logo(slide, "logo_senai_branco.png", x=195, y=112, largura=560)
    fonte, linhas = _ajustar(titulo.upper(), 140, 72, 1570, 3)
    _escrever_de_baixo(ImageDraw.Draw(slide), linhas, fonte, x=175, base=910, cor=BRANCO)
    return slide


def _desenhar_divisoria(titulo: str) -> Image.Image:
    slide = _base_interna()
    fonte, linhas = _ajustar(titulo.upper(), 100, 60, 1570, 2)
    _escrever_de_baixo(ImageDraw.Draw(slide), linhas, fonte, x=175, base=891, cor=AZUL)
    return slide


def _medir_topicos(topicos, tamanho, largura_max):
    fonte = _fonte(tamanho)
    blocos = [_quebrar(t, fonte, largura_max) for t in topicos]
    if any(fonte.getlength(li) > largura_max for b in blocos for li in b):
        return fonte, blocos, None
    passo = _altura_linha(fonte)
    altura = sum(len(b) * passo for b in blocos) + (len(blocos) - 1) * round(tamanho * 0.45)
    return fonte, blocos, altura


def _desenhar_conteudo(titulo: str, topicos: list[str], destaque: str | None) -> Image.Image:
    slide = _base_interna()
    draw = ImageDraw.Draw(slide)

    fonte_t, linhas_t = _ajustar(titulo, 76, 50, 1420, 2)
    for i, linha in enumerate(linhas_t):
        draw.text((156, 95 + i * _altura_linha(fonte_t)), linha, font=fonte_t, fill=AZUL)
    topo_topicos = max(310, 95 + len(linhas_t) * _altura_linha(fonte_t) + 90)

    limite_inferior = 1000
    if destaque:
        fonte_d, linhas_d = _ajustar(destaque, 56, 40, 1300, 3)
        topo_destaque = 936 - (len(linhas_d) - 1) * _altura_linha(fonte_d) - fonte_d.size
        limite_inferior = topo_destaque - 70
        _escrever_destaque(draw, linhas_d, fonte_d)

    x_texto, largura_texto = 233, 1300
    for tamanho in range(44, 29, -2):
        fonte, blocos, altura = _medir_topicos(topicos, tamanho, largura_texto)
        if altura is not None and topo_topicos + altura <= limite_inferior:
            break
    else:
        raise TextoLongoDemais(
            f'Os tópicos do slide "{titulo}" não cabem. Use menos tópicos ou frases mais curtas.'
        )

    passo = _altura_linha(fonte)
    y = topo_topicos
    raio = max(6, round(fonte.size * 0.15))
    for bloco in blocos:
        centro = y + round(fonte.size * 0.62)
        draw.ellipse((194 - raio, centro - raio, 194 + raio, centro + raio), fill=LARANJA)
        for linha in bloco:
            draw.text((x_texto, y), linha, font=fonte, fill=AZUL)
            y += passo
        y += round(fonte.size * 0.45)
    return slide


def _escrever_destaque(draw, linhas, fonte) -> None:
    passo = _altura_linha(fonte)
    base = 936 - (len(linhas) - 1) * passo
    for i, linha in enumerate(linhas):
        y = base + i * passo
        ultima = i == len(linhas) - 1
        # No modelo, o ponto final da frase de destaque é verde.
        if ultima and linha.endswith("."):
            draw.text((189, y), linha[:-1], font=fonte, fill=LARANJA, anchor="ls")
            x_ponto = 189 + fonte.getlength(linha[:-1])
            draw.text((x_ponto, y), ".", font=fonte, fill=VERDE, anchor="ls")
        else:
            draw.text((189, y), linha, font=fonte, fill=LARANJA, anchor="ls")


def _desenhar_encerramento() -> Image.Image:
    slide = Image.new("RGBA", (LARGURA, ALTURA), AZUL)
    _colar_logo(slide, "logo_senai_branco.png", x=283, y=490, largura=554)
    draw = ImageDraw.Draw(slide)
    draw.line((912, 377, 912, 700), fill=BRANCO, width=2)

    y = 412
    for item in CONTATOS:
        if item is None:
            y += 37
            continue
        texto, cor, destaque = item
        fonte = _fonte(30, negrito=destaque)
        draw.text((955, y), texto, font=fonte, fill=cor, anchor="ls")
        if destaque:
            draw.line((955, y + 5, 955 + fonte.getlength(texto), y + 5), fill=cor, width=2)
        y += 33
    return slide


def _circulo(x: float, y: float, raio: float, escala: int = 1) -> tuple[float, ...]:
    return tuple(v * escala for v in (x - raio, y - raio, x + raio, y + raio))


def _posicoes_diagrama(n: int) -> list[tuple[int, int, int]]:
    """(x, y, lado) do círculo de cada item: a primeira metade à esquerda, o resto à direita."""
    cx, cy = CENTRO
    esquerda = (n + 1) // 2
    posicoes = []
    for lado, quantidade in ((-1, esquerda), (1, n - esquerda)):
        for dy in DESLOCAMENTOS[quantidade]:
            dx = math.sqrt(RAIO_ANEL**2 - dy**2)
            posicoes.append((round(cx + lado * dx), cy + dy, lado))
    return posicoes


def _cores_diagrama(n: int) -> list[tuple[int, int, int]]:
    # Espalha os itens pela paleta, para o laranja e o azul aparecerem mesmo com poucos itens.
    ultima = len(CORES_DIAGRAMA) - 1
    return [CORES_DIAGRAMA[round(i * ultima / (n - 1))] for i in range(n)]


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
    draw.ellipse(_circulo(cx, cy, RAIO_ANEL + LARGURA_FAIXA / 2, e), fill=255)
    draw.ellipse(_circulo(cx, cy, RAIO_ANEL - LARGURA_FAIXA / 2, e), fill=0)
    x0, x1 = (0, cx * e) if lado < 0 else (cx * e, camada.width)
    caixa = (x0, y_inicio * e, x1, y_fim * e)
    camada.paste(coluna.resize((x1 - x0, coluna.height)), caixa[:2], mascara.crop(caixa))


def _esfera(diametro: int) -> Image.Image:
    """Círculo branco com sombreado suave e o brilho no alto, à esquerda."""
    brilho = Image.radial_gradient("L").resize((diametro * 2, diametro * 2))
    x, y = round(diametro * 0.62), round(diametro * 0.70)
    brilho = brilho.crop((x, y, x + diametro, y + diametro))
    esfera = ImageOps.colorize(brilho, black=BRANCO, white=(196, 204, 218), mid=(240, 243, 247))
    mascara = Image.new("L", (diametro, diametro), 0)
    ImageDraw.Draw(mascara).ellipse((0, 0, diametro - 1, diametro - 1), fill=255)
    esfera.putalpha(mascara)
    return esfera


def _texto_do_cartao(draw, x: int, y: int, lado: int, item: dict) -> None:
    largura = CARTAO_LARGURA - CARTAO_MARGEM - RAIO_NUMERO - 22
    fonte_t, linhas_t = _ajustar(item["titulo"].upper(), 30, 22, largura, 1, negrito=True)
    fonte, linhas = _ajustar(item["texto"], 26, 20, largura, 3)
    passo = _altura_linha(fonte)
    topo = y - (fonte_t.size + 12 + len(linhas) * passo) / 2
    # À direita do círculo central, o texto é alinhado pela direita, como no modelo.
    if lado < 0:
        x_texto, ancora = x - CARTAO_LARGURA + CARTAO_MARGEM, "la"
    else:
        x_texto, ancora = x + CARTAO_LARGURA - CARTAO_MARGEM, "ra"
    draw.text((x_texto, topo), linhas_t[0], font=fonte_t, fill=BRANCO, anchor=ancora)
    for i, linha in enumerate(linhas):
        y_linha = topo + fonte_t.size + 12 + i * passo
        draw.text((x_texto, y_linha), linha, font=fonte, fill=BRANCO, anchor=ancora)


def _texto_do_centro(draw, titulo: str, cores: list[tuple]) -> None:
    fonte, linhas = _ajustar(titulo.upper(), 52, 30, 320, 3, negrito=True)
    passo = _altura_linha(fonte)
    cx, cy = CENTRO
    topo = cy - (len(linhas) * passo + 42) / 2
    for i, linha in enumerate(linhas):
        draw.text((cx, topo + i * passo), linha, font=fonte, fill=AZUL, anchor="ma")
    # Uma bolinha por item, na cor do cartão.
    y = topo + len(linhas) * passo + 34
    x0 = cx - 15 * (len(cores) - 1)
    for i, cor in enumerate(cores):
        draw.ellipse(_circulo(x0 + 30 * i, y, 8), fill=cor)


def _desenhar_diagrama(titulo: str, itens: list[dict]) -> Image.Image:
    slide = _base_interna()
    posicoes = _posicoes_diagrama(len(itens))
    cores = _cores_diagrama(len(itens))
    cx, cy = CENTRO
    e = ESCALA

    fundo = Image.new("RGBA", (LARGURA * e, ALTURA * e), (0, 0, 0, 0))
    for lado in (-1, 1):
        paradas = [
            (y, cor) for (_, y, lado_), cor in zip(posicoes, cores, strict=True) if lado_ == lado
        ]
        if len(paradas) > 1:
            _faixa(fundo, lado, paradas)
    draw = ImageDraw.Draw(fundo)
    meia = CARTAO_ALTURA / 2
    for (x, y, lado), cor in zip(posicoes, cores, strict=True):
        x0, x1 = (x - CARTAO_LARGURA, x) if lado < 0 else (x, x + CARTAO_LARGURA)
        caixa = (x0 * e, (y - meia) * e, x1 * e, (y + meia) * e)
        draw.rounded_rectangle(caixa, radius=meia * e, fill=cor)
    for k in range(44):
        angulo = 2 * math.pi * k / 44
        x = cx + (RAIO_CENTRO + 50) * math.cos(angulo)
        y = cy + (RAIO_CENTRO + 50) * math.sin(angulo)
        draw.ellipse(_circulo(x, y, 3.5, e), fill=(180, 188, 200))
    slide.alpha_composite(fundo.resize((LARGURA, ALTURA), Image.Resampling.LANCZOS))

    sombra = Image.new("L", (LARGURA, ALTURA), 0)
    draw = ImageDraw.Draw(sombra)
    draw.ellipse(_circulo(cx + 10, cy + 20, RAIO_CENTRO), fill=110)
    for x, y, _ in posicoes:
        draw.ellipse(_circulo(x + 5, y + 10, RAIO_NUMERO), fill=120)
    camada = Image.new("RGBA", (LARGURA, ALTURA), (20, 30, 50, 0))
    camada.putalpha(sombra.filter(ImageFilter.GaussianBlur(16)))
    slide.alpha_composite(camada)

    frente = Image.new("RGBA", (LARGURA * e, ALTURA * e), (0, 0, 0, 0))
    canto = ((cx - RAIO_CENTRO) * e, (cy - RAIO_CENTRO) * e)
    frente.alpha_composite(_esfera(2 * RAIO_CENTRO * e), canto)
    esfera = _esfera(2 * RAIO_NUMERO * e)
    for x, y, _ in posicoes:
        frente.alpha_composite(esfera, ((x - RAIO_NUMERO) * e, (y - RAIO_NUMERO) * e))
    slide.alpha_composite(frente.resize((LARGURA, ALTURA), Image.Resampling.LANCZOS))

    draw = ImageDraw.Draw(slide)
    for numero, ((x, y, lado), cor, item) in enumerate(zip(posicoes, cores, itens, strict=True), 1):
        _texto_do_cartao(draw, x, y, lado, item)
        draw.text((x, y), f"{numero:02d}", font=_fonte(40, negrito=True), fill=cor, anchor="mm")
    _texto_do_centro(draw, titulo, cores)
    return slide


def _nome_de_pasta(nome: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")
    if not slug:
        raise ValueError("O nome da apresentação precisa ter letras ou números.")
    return slug


class Apresentacao:
    def __init__(self, nome: str, pasta: str | Path = "outputs"):
        self.nome = _nome_de_pasta(_texto_obrigatorio(nome, "O nome da apresentação"))
        self.pasta = Path(pasta) / self.nome
        self.slides: list[Image.Image] = []

    def capa(self, titulo: str) -> None:
        self.slides.append(_desenhar_capa(_texto_obrigatorio(titulo, "O título da capa")))

    def divisoria(self, titulo: str) -> None:
        titulo = _texto_obrigatorio(titulo, "O título da divisória")
        self.slides.append(_desenhar_divisoria(titulo))

    def conteudo(self, titulo: str, topicos: list[str], destaque: str | None = None) -> None:
        titulo = _texto_obrigatorio(titulo, "O título do slide de conteúdo")
        if not isinstance(topicos, (list, tuple)) or not 1 <= len(topicos) <= MAX_TOPICOS:
            raise ValueError(
                f'O slide "{titulo}" precisa de uma lista com 1 a {MAX_TOPICOS} tópicos.'
            )
        topicos = [_texto_obrigatorio(t, f'Cada tópico do slide "{titulo}"') for t in topicos]
        if destaque is not None:
            destaque = _texto_obrigatorio(destaque, f'O destaque do slide "{titulo}"')
        self.slides.append(_desenhar_conteudo(titulo, topicos, destaque))

    def diagrama(self, titulo: str, itens: list[dict]) -> None:
        """Círculo com o `titulo` e os itens em volta; cada item tem `titulo` e `texto`."""
        titulo = _texto_obrigatorio(titulo, "O título do diagrama")
        if not isinstance(itens, (list, tuple)) or not 2 <= len(itens) <= MAX_ITENS:
            raise ValueError(
                f'O diagrama "{titulo}" precisa de uma lista com 2 a {MAX_ITENS} itens.'
            )
        limpos = []
        for i, item in enumerate(itens, start=1):
            if not isinstance(item, dict):
                raise ValueError(f'O item {i} do diagrama "{titulo}" precisa ter título e texto.')
            onde = f'do item {i} do diagrama "{titulo}"'
            limpos.append(
                {
                    "titulo": _texto_obrigatorio(item.get("titulo"), f"O título {onde}"),
                    "texto": _texto_obrigatorio(item.get("texto"), f"O texto {onde}"),
                }
            )
        self.slides.append(_desenhar_diagrama(titulo, limpos))

    def encerramento(self) -> None:
        self.slides.append(_desenhar_encerramento())

    def salvar(self) -> Path:
        if not self.slides:
            raise ValueError("A apresentação não tem nenhum slide para salvar.")

        self.pasta.mkdir(parents=True, exist_ok=True)
        for antigo in self.pasta.glob("slide_*.png"):
            antigo.unlink()

        imagens = [s.convert("RGB") for s in self.slides]
        for i, imagem in enumerate(imagens, start=1):
            imagem.save(self.pasta / f"slide_{i:02d}.png")
        pdf = self.pasta / f"{self.nome}.pdf"
        # 144 dpi deixa a página em 13,33 x 7,5 polegadas, o tamanho padrão de slide 16:9.
        imagens[0].save(pdf, save_all=True, append_images=imagens[1:], resolution=144)

        print(f"{len(imagens)} slides salvos em: {self.pasta.resolve()}")
        print(f"PDF gerado em: {pdf.resolve()}")
        return self.pasta
