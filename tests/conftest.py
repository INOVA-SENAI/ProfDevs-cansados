import base64
import hashlib
import io
import json

import pytest
from PIL import Image, ImageDraw

from senai_slides import imagens, tema


class BedrockFalsa:
    """Faz o papel da Amazon Bedrock nos testes: nenhum teste chama a AWS nem gasta dinheiro."""

    def __init__(self):
        self.chamadas: list[dict] = []
        self.erro: Exception | None = None
        self.so_falha_com: str | None = None  # com isto, só o prompt que contém o texto falha
        self.resposta: dict | None = None  # troca o JSON devolvido

    def invoke_model(self, modelId, body):
        corpo = json.loads(body)
        self.chamadas.append({"modelo": modelId, **corpo})
        if self.erro and (self.so_falha_com is None or self.so_falha_com in corpo["prompt"]):
            raise self.erro
        dados = self.resposta or {
            "images": [_imagem_falsa(corpo["prompt"])],
            "finish_reasons": [None],
        }
        return {"body": io.BytesIO(json.dumps(dados).encode())}


def pagina_do_commons(
    titulo="File:Foto.jpg",
    largura=1600,
    altura=1200,
    mime="image/jpeg",
    licenca="CC BY-SA 4.0",
    autor='<a href="/wiki/User:Fulano">Fulano</a>',
    nao_livre=False,
) -> dict:
    """Uma página de arquivo como a API do Wikimedia Commons devolve."""
    meta = {"LicenseShortName": {"value": licenca}, "Artist": {"value": autor}}
    if nao_livre:
        meta["NonFree"] = {"value": "true"}
    return {
        "title": titulo,
        "imageinfo": [
            {
                "mime": mime,
                "width": largura,
                "height": altura,
                "thumburl": f"https://upload.example/{titulo}",
                "extmetadata": meta,
            }
        ],
    }


class CommonsFalso:
    """Faz o papel do Wikimedia Commons nos testes: nenhum teste acessa a internet."""

    def __init__(self):
        self.buscas: list[str] = []
        self.paginas: list[dict] | None = None  # None: devolve uma foto que serve
        self.erro: Exception | None = None

    def api(self, parametros: dict) -> dict:
        self.buscas.append(parametros["gsrsearch"])
        if self.erro:
            raise self.erro
        paginas = [pagina_do_commons()] if self.paginas is None else self.paginas
        return {"query": {"pages": {str(i): {**p, "index": i + 1} for i, p in enumerate(paginas)}}}

    def abrir(self, url: str) -> bytes:
        return base64.b64decode(_imagem_falsa(url, (1280, 960)))


def _imagem_falsa(semente: str, tamanho=(1024, 1024)) -> str:
    """Imagem com cores que mudam conforme o texto, em base64."""
    r, g, b = hashlib.sha256(semente.encode()).digest()[:3]
    imagem = Image.new("RGB", tamanho, (r, g, b))
    ImageDraw.Draw(imagem).ellipse((256, 256, 768, 768), fill=(255 - r, 255 - g, 255 - b))
    buffer = io.BytesIO()
    imagem.save(buffer, "JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


@pytest.fixture(autouse=True)
def bedrock(monkeypatch) -> BedrockFalsa:
    falsa = BedrockFalsa()
    monkeypatch.setattr(imagens, "_bedrock", lambda: falsa)
    return falsa


@pytest.fixture(autouse=True)
def commons(monkeypatch) -> CommonsFalso:
    falso = CommonsFalso()
    monkeypatch.setattr(imagens, "_api_commons", falso.api)
    monkeypatch.setattr(imagens, "_abrir", falso.abrir)
    return falso


@pytest.fixture(autouse=True)
def graficos_rapidos(monkeypatch):
    """Gráficos em baixa resolução: o teste confere a montagem, não a nitidez."""
    monkeypatch.setattr(tema, "DPI", 60)
