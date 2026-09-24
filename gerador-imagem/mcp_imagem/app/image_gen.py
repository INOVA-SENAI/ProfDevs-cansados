"""Chamada à Amazon Bedrock (Stability AI Image Services). Única parte do projeto que fala com a IA."""

import base64
import json
import os
from functools import cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

# Perfis "us." roteiam entre us-east-1, us-east-2 e us-west-2. Em set/2026 os modelos de
# texto→imagem da Bedrock (Nova Canvas, SD3.5, Stable Image Core) estão em Legacy ou saíram;
# estes dois estão Active e geram a partir de uma imagem de referência.
STYLE_GUIDE = "us.stability.stable-image-style-guide-v1:0"
STYLE_TRANSFER = "us.stability.stable-style-transfer-v1:0"
REMOVE_BACKGROUND = "us.stability.stable-image-remove-background-v1:0"

_CREDENCIAL = (
    " Falta uma credencial AWS válida: defina AWS_BEARER_TOKEN_BEDROCK no"
    " mcp_imagem/.env ou rode `aws login` (README, seção 4.2)."
)
_DICAS = {
    "UnrecognizedClientException": _CREDENCIAL,
    "IncompleteSignatureException": _CREDENCIAL,
    "ExpiredTokenException": _CREDENCIAL,
    "AccessDeniedException": " Confira se a conta AWS já foi verificada e se os modelos"
    " Stability AI estão ativos (README, seção 4.1).",
}


@cache
def _bedrock():
    # Credenciais: AWS_BEARER_TOKEN_BEDROCK (chave de API da Bedrock) ou a cadeia padrão da AWS.
    return boto3.client(
        "bedrock-runtime",
        region_name=os.getenv("AWS_REGION", "us-east-1"),
        config=Config(read_timeout=300),
    )


def _b64(dados: bytes) -> str:
    return base64.b64encode(dados).decode()


def gerar(
    prompt: str,
    negativo: str,
    estilo_ref: bytes,
    fidelidade: float,
    referencia: bytes | None = None,
) -> bytes:
    """Devolve os bytes PNG gerados.

    Sem `referencia`: Style Guide cria a imagem do prompt no estilo de `estilo_ref`.
    Com `referencia`: Style Transfer redesenha `referencia` no estilo de `estilo_ref`.
    """
    if referencia is None:
        modelo = STYLE_GUIDE
        corpo = {
            "image": _b64(estilo_ref),
            "style_preset": "pixel-art",
            "fidelity": fidelidade,
        }
    else:
        modelo = STYLE_TRANSFER
        corpo = {"init_image": _b64(referencia), "style_image": _b64(estilo_ref)}
    corpo |= {"prompt": prompt, "negative_prompt": negativo}
    return _invocar(modelo, corpo)


def remover_fundo(png: bytes) -> bytes:
    """Devolve o PNG com o fundo transparente (Stability Remove Background)."""
    return _invocar(REMOVE_BACKGROUND, {"image": _b64(png)})


def _invocar(modelo: str, corpo: dict) -> bytes:
    corpo = corpo | {"output_format": "png"}
    try:
        resposta = _bedrock().invoke_model(modelId=modelo, body=json.dumps(corpo))
    except ClientError as e:
        erro = e.response["Error"]
        raise RuntimeError(
            f"A Bedrock recusou o pedido ({erro['Code']}): "
            f"{erro['Message'].rstrip('.')}.{_DICAS.get(erro['Code'], '')}"
        ) from e
    except BotoCoreError as e:  # sem credenciais, sem rede, timeout
        raise RuntimeError(
            f"Não foi possível chamar a Bedrock: {e}.{_CREDENCIAL}"
        ) from e

    dados = json.loads(resposta["body"].read())
    motivo = (dados.get("finish_reasons") or [None])[0]
    if motivo or not dados.get("images"):
        raise RuntimeError(
            f"A Bedrock não devolveu imagem (motivo: {motivo}). Tente outro prompt ou outra imagem."
        )
    return base64.b64decode(dados["images"][0])
