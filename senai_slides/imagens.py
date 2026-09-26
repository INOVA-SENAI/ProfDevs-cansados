"""Imagens dos slides: fotos reais do Wikimedia Commons ou imagens fotográficas criadas por IA.

- `foto`: busca uma foto real, de licença livre, no Wikimedia Commons. Não custa nada; o crédito
  (autor e licença) vai no slide, como a licença pede.
- `gerar`: cria uma imagem fotográfica com o Style Guide da Stability AI na Amazon Bedrock, a
  partir do gerador de imagens da branch prof/joao-borges. Cerca de US$ 0,07 por imagem; o
  slide leva a legenda "Imagem gerada por IA".

Cada imagem fica em cache, para que salvar o deck de novo não busque nem cobre outra vez.
"""

import base64
import hashlib
import io
import json
import os
import re
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from dotenv import dotenv_values
from PIL import Image, ImageOps

MODOS = ("foto", "gerar")

# O perfil "us." roteia entre us-east-1, us-east-2 e us-west-2. Em set/2026, os modelos de texto
# para imagem da Bedrock (Nova Canvas, SD3.5, Stable Image Core) estão em Legacy ou saíram;
# o Style Guide está Active e gera a partir de uma imagem de referência de estilo.
STYLE_GUIDE = "us.stability.stable-image-style-guide-v1:0"
CUSTO_POR_IMAGEM = 0.07  # US$, preço de set/2026
# Chamadas simultâneas à Bedrock. Com 3, a conta do projeto já deu ThrottlingException (24/09/2026).
PARALELO = 2
DESCRICAO = "professional photograph, natural light, realistic, sharp focus, high detail"
# Com 0,3 a imagem já puxava o degradê da referência e saía lavada (teste de 25/09/2026).
FIDELIDADE = 0.1
NEGATIVO = (
    "text, letters, words, watermark, logo, signature, cartoon, illustration, painting, "
    "drawing, pixel art, 3d render, blurry, deformed"
)
CREDITO_IA = "Imagem gerada por IA"

COMMONS = "https://commons.wikimedia.org/w/api.php"
# A política do Wikimedia pede um User-Agent que identifique o programa.
AGENTE_HTTP = (
    "ProfDevs-cansados/0.5 (gerador de slides do SENAI; "
    "https://github.com/INOVA-SENAI/ProfDevs-cansados)"
)
LADO_MINIMO = 800  # px; fotos menores ficam borradas no slide
LICENCAS_LIVRES = ("CC0", "Public domain", "CC BY")  # inclui CC BY-SA

_CREDENCIAL = (
    " Falta uma credencial AWS válida: defina AWS_BEARER_TOKEN_BEDROCK no .env do projeto ou"
    " rode `aws login` (README, seção Imagens e custos). Para gerar só com as fotos reais,"
    " rode sem --aceitar-custo."
)
_DICAS = {
    "UnrecognizedClientException": _CREDENCIAL,
    "IncompleteSignatureException": _CREDENCIAL,
    "ExpiredTokenException": _CREDENCIAL,
    "AccessDeniedException": " Confira se a conta AWS já foi verificada e se os modelos da"
    " Stability AI estão ativos (README, seção Imagens e custos).",
    "ThrottlingException": " A conta tem um limite de imagens por minuto. Rode de novo daqui a"
    " pouco: as imagens que já foram geradas ficam no cache e não são cobradas outra vez.",
}


@dataclass(frozen=True)
class Ilustracao:
    imagem: Image.Image
    credito: str  # vai em letra pequena abaixo da imagem


@dataclass(frozen=True)
class Estimativa:
    fotos: int  # fotos a buscar no Commons (grátis)
    geradas: int  # imagens a criar por IA (pagas)
    em_cache: int  # já prontas

    @property
    def custo(self) -> float:
        return self.geradas * CUSTO_POR_IMAGEM

    def __str__(self) -> str:
        partes = []
        if self.fotos:
            fotos = "1 foto real" if self.fotos == 1 else f"{self.fotos} fotos reais"
            partes.append(f"{fotos} a buscar (grátis)")
        if self.geradas:
            geradas = "1 imagem" if self.geradas == 1 else f"{self.geradas} imagens"
            partes.append(f"{geradas} a criar por IA (cerca de {dolares(self.custo)})")
        if self.em_cache:
            prontas = "1 pronta" if self.em_cache == 1 else f"{self.em_cache} prontas"
            partes.append(f"{prontas} no cache (sem custo)")
        if not partes:
            return "nenhuma"
        return ", ".join(partes[:-1]) + " e " + partes[-1] if len(partes) > 1 else partes[0]


def dolares(valor: float) -> str:
    return f"US$ {valor:.2f}".replace(".", ",")


def pedido(valor: str | dict) -> tuple[str, str]:
    """(modo, texto) de um campo `imagem` do deck. Texto sozinho é `gerar`."""
    if isinstance(valor, str):
        return "gerar", " ".join(valor.split())
    (modo, texto), *_ = valor.items()
    return modo, " ".join(texto.split())


def pedidos_do_deck(deck: dict) -> tuple[tuple[str, str] | None, list[tuple[str, str] | None]]:
    """O pedido da capa e o de cada slide de conteúdo, na ordem (None em quem não tem imagem).
    Com `imagens: false` no deck, nenhum."""
    slides = deck["slides"]
    if deck.get("imagens") is False:
        return None, [None] * len(slides)
    capa = pedido(deck["imagem"]) if deck.get("imagem") else None
    return capa, [
        pedido(s["imagem"]) if s.get("layout") == "ilustracao" and s.get("imagem") else None
        for s in slides
    ]


def nome_de_pasta(nome: str) -> str:
    """Nome da pasta da aula em outputs/, onde fica também o cache das imagens."""
    sem_acento = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", sem_acento.lower()).strip("_")
    if not slug:
        raise ValueError("O nome da apresentação precisa ter letras ou números.")
    return slug


def pasta_da_aula(deck: dict, saida: str | Path) -> Path:
    return Path(saida) / nome_de_pasta(deck.get("nome") or deck["titulo"])


# Criar com a Bedrock


def carregar_env(caminho: Path) -> None:
    """Completa o ambiente com o .env sem sobrescrever o que já veio preenchido.

    Valores vazios são ignorados. Um AWS_BEARER_TOKEN_BEDROCK vazio faria o boto3 tentar um
    token vazio em vez do `aws login` (IncompleteSignatureException).
    """
    for chave, valor in dotenv_values(caminho).items():
        if valor and not os.environ.get(chave):
            os.environ[chave] = valor
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip():
        os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)


@cache
def _bedrock():
    # Importados só aqui: validar um deck não precisa da AWS.
    import boto3
    from botocore.config import Config

    carregar_env(Path.cwd() / ".env")
    # Credenciais: AWS_BEARER_TOKEN_BEDROCK (chave de API da Bedrock) ou a cadeia padrão da AWS.
    # O modo "adaptive" espera e tenta de novo quando a Bedrock responde ThrottlingException.
    return boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=Config(read_timeout=300, retries={"mode": "adaptive", "max_attempts": 10}),
    )


@cache
def _referencia() -> str:
    """Imagem de estilo neutra: luz natural quente em cima e sombra fria embaixo, sem nenhum
    objeto nem pessoa. O Style Guide exige uma referência; com fidelidade baixa, a cena vem do
    texto e a referência só puxa a luz para o natural."""
    degrade = Image.linear_gradient("L").resize((512, 512))
    imagem = ImageOps.colorize(degrade, black=(236, 228, 214), white=(96, 104, 118))
    buffer = io.BytesIO()
    imagem.save(buffer, "PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def montar_prompt(texto: str) -> str:
    texto = " ".join(texto.split())
    if not texto:
        raise ValueError("A descrição da imagem não pode ser vazia.")
    return f"{texto}. {DESCRICAO}"


def gerar_imagem(texto: str) -> bytes:
    """Chama o Style Guide da Bedrock e devolve o JPEG da imagem criada."""
    from botocore.exceptions import BotoCoreError, ClientError

    corpo = {
        "image": _referencia(),
        "style_preset": "photographic",
        "fidelity": FIDELIDADE,
        "prompt": montar_prompt(texto),
        "negative_prompt": NEGATIVO,
        "aspect_ratio": "1:1",
        "output_format": "jpeg",
    }
    try:
        resposta = _bedrock().invoke_model(modelId=STYLE_GUIDE, body=json.dumps(corpo))
    except ClientError as e:
        erro = e.response["Error"]
        raise RuntimeError(
            f"A Bedrock recusou o pedido ({erro['Code']}): "
            f"{erro['Message'].rstrip('.')}.{_DICAS.get(erro['Code'], '')}"
        ) from e
    except BotoCoreError as e:  # sem credenciais, sem rede, timeout
        raise RuntimeError(f"Não foi possível chamar a Bedrock: {e}.{_CREDENCIAL}") from e

    dados = json.loads(resposta["body"].read())
    motivo = (dados.get("finish_reasons") or [None])[0]
    if motivo or not dados.get("images"):
        raise RuntimeError(
            f"A Bedrock não devolveu imagem (motivo: {motivo}). Reescreva a descrição da imagem."
        )
    return base64.b64decode(dados["images"][0])


# Buscar no Wikimedia Commons


def _abrir(url: str) -> bytes:
    requisicao = urllib.request.Request(url, headers={"User-Agent": AGENTE_HTTP})
    with urllib.request.urlopen(requisicao, timeout=30) as resposta:
        return resposta.read()


def _api_commons(parametros: dict) -> dict:
    return json.loads(_abrir(f"{COMMONS}?{urllib.parse.urlencode(parametros)}"))


def _sem_html(texto: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", texto).split())


def _credito(meta: dict) -> str:
    autor = _sem_html(meta.get("Artist", {}).get("value", "")) or "autor desconhecido"
    if len(autor) > 60:
        autor = autor[:57] + "..."
    licenca = meta.get("LicenseShortName", {}).get("value", "")
    return f"Foto: {autor}, {licenca}, via Wikimedia Commons"


def _livre(meta: dict) -> bool:
    licenca = meta.get("LicenseShortName", {}).get("value", "")
    return licenca.startswith(LICENCAS_LIVRES) and meta.get("NonFree", {}).get("value") != "true"


def buscar_foto(termos: str) -> tuple[bytes, str] | None:
    """A primeira foto do Commons para os termos que seja grande e de licença livre, com o
    crédito. Devolve None se nenhuma servir."""
    parametros = {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{termos} filetype:bitmap",
        "gsrnamespace": 6,  # arquivos
        "gsrlimit": 20,
        "prop": "imageinfo",
        "iiprop": "url|size|mime|extmetadata",
        "iiurlwidth": 1280,
    }
    try:
        paginas = _api_commons(parametros).get("query", {}).get("pages", {}).values()
        for pagina in sorted(paginas, key=lambda p: p.get("index", 0)):
            info = (pagina.get("imageinfo") or [{}])[0]
            meta = info.get("extmetadata", {})
            if (
                info.get("mime") in ("image/jpeg", "image/png")
                and min(info.get("width", 0), info.get("height", 0)) >= LADO_MINIMO
                and _livre(meta)
                and info.get("thumburl")
            ):
                return _abrir(info["thumburl"]), _credito(meta)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        raise RuntimeError(
            f"Não foi possível buscar a foto no Wikimedia Commons: {e}. Confira a internet, "
            "troque a `foto` por `gerar` ou use --sem-imagens."
        ) from e
    return None


# Cache


def _no_cache(pasta: Path, modo: str, texto: str) -> Path:
    # Tudo o que muda a imagem entra na chave.
    chave = [modo, " ".join(texto.split())]
    if modo == "gerar":
        chave += [STYLE_GUIDE, DESCRICAO, NEGATIVO, FIDELIDADE]
    return pasta / f"{modo}-{hashlib.sha256(json.dumps(chave).encode()).hexdigest()[:16]}.jpg"


def _salvar(destino: Path, dados: bytes, credito: str) -> None:
    # Grava em temporários e renomeia: uma geração interrompida não deixa arquivo quebrado.
    # A imagem vai por último, porque é ela que marca o cache como pronto.
    for caminho, conteudo in ((destino.with_suffix(".json"), json.dumps({"credito": credito})),
                              (destino, dados)):  # fmt: skip
        temporario = caminho.with_suffix(".tmp")
        if isinstance(conteudo, str):
            temporario.write_text(conteudo, encoding="utf-8")
        else:
            temporario.write_bytes(conteudo)
        temporario.replace(caminho)


def _resumo(texto: str) -> str:
    return texto if len(texto) <= 60 else texto[:57] + "..."


def _gerar_e_salvar(texto: str, destino: Path) -> None:
    try:
        dados = gerar_imagem(texto)
    except RuntimeError as erro:
        raise RuntimeError(f'Imagem "{_resumo(texto)}": {erro}') from erro
    _salvar(destino, dados, CREDITO_IA)


def estimativa(deck: dict, saida: str | Path = "outputs") -> Estimativa:
    """Quantas imagens do deck faltam buscar e criar, sem buscar nem criar nada."""
    capa, slides = pedidos_do_deck(deck)
    pedidos = {p for p in (capa, *slides) if p}
    pasta = pasta_da_aula(deck, saida) / "imagens"
    faltando = [p for p in pedidos if not _no_cache(pasta, *p).exists()]
    fotos = sum(modo == "foto" for modo, _ in faltando)
    return Estimativa(fotos, len(faltando) - fotos, len(pedidos) - len(faltando))


def ilustracoes(pedidos, pasta: Path, pagar: bool = True) -> dict[tuple[str, str], Ilustracao]:
    """Uma imagem por pedido (modo, texto). Só busca ou gera o que não está no cache.

    Sem `pagar`, nada é cobrado: as imagens por IA que faltam ficam de fora, e uma foto que não
    for encontrada não vira imagem por IA."""
    caminhos = {p: _no_cache(pasta, *p) for p in pedidos}
    faltando = {caminho: p for p, caminho in caminhos.items() if not caminho.exists()}
    if faltando:
        pasta.mkdir(parents=True, exist_ok=True)
    a_gerar = {}
    if pagar:
        a_gerar = {c: texto for c, (modo, texto) in faltando.items() if modo == "gerar"}

    fotos = {c: texto for c, (modo, texto) in faltando.items() if modo == "foto"}
    if fotos:
        print(f"Buscando {len(fotos)} foto(s) no Wikimedia Commons...")
    for caminho, termos in fotos.items():
        achada = buscar_foto(termos)
        if achada:
            _salvar(caminho, *achada)
        elif pagar:
            print(f'  Nenhuma foto livre para "{_resumo(termos)}"; ela será gerada por IA.')
            a_gerar[caminho] = termos
        else:
            print(
                f'  Nenhuma foto livre para "{_resumo(termos)}"; o slide fica sem imagem. '
                "Troque as palavras-chave ou use --aceitar-custo para criá-la por IA."
            )

    if a_gerar:
        custo = dolares(len(a_gerar) * CUSTO_POR_IMAGEM)
        print(f"Gerando {len(a_gerar)} imagem(ns) na Amazon Bedrock (cerca de {custo})...")
        _bedrock()  # cria o cliente antes das threads
        # Se uma imagem falhar, as outras terminam e ficam no cache antes de o erro subir.
        with ThreadPoolExecutor(PARALELO) as executor:
            list(executor.map(_gerar_e_salvar, a_gerar.values(), a_gerar.keys()))

    prontas = {}
    for p, caminho in caminhos.items():
        if not caminho.exists():  # imagem por IA que não foi autorizada
            continue
        credito = json.loads(caminho.with_suffix(".json").read_text(encoding="utf-8"))["credito"]
        with Image.open(caminho) as imagem:
            prontas[p] = Ilustracao(imagem.convert("RGB"), credito)
    return prontas
