"""Servidor MCP: gera PNG sem fundo em 8bit ou pixel art (Amazon Bedrock + Pillow). Papel do app/main.py."""

import io
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Annotated

from dotenv import dotenv_values
from mcp.server import MCPServer
from mcp.server.mcpserver import Image
from mcp.server.mcpserver.exceptions import ToolError
from PIL import Image as PILImage
from PIL import UnidentifiedImageError
from pydantic import Field

from app.image_gen import gerar, remover_fundo
from app.pixel_grid import pixelizar
from prompts.tipo_prompt import NEGATIVO, TIPOS, Tipo, montar_prompt

RAIZ = Path(__file__).parent


def carregar_env(caminho: Path) -> None:
    """Completa o ambiente com o .env sem sobrescrever o que já veio preenchido.

    Valores vazios são ignorados. Um AWS_BEARER_TOKEN_BEDROCK vazio faria o boto3
    tentar um token vazio em vez do `aws login` (IncompleteSignatureException).
    """
    for chave, valor in dotenv_values(caminho).items():
        if valor and not os.environ.get(chave):
            os.environ[chave] = valor
    if not os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "").strip():
        os.environ.pop("AWS_BEARER_TOKEN_BEDROCK", None)


carregar_env(RAIZ / ".env")
# O log vai para o stderr. Em servidor stdio, print() quebra o protocolo.
logging.basicConfig(level=logging.INFO)

mcp = MCPServer("gerador-imagem")


def ler_referencia(caminho: str) -> bytes:
    """Valida a imagem enviada pelo usuário e devolve um PNG dentro dos limites da Bedrock."""
    try:
        img = PILImage.open(Path(caminho).expanduser())
        img.load()
    except UnidentifiedImageError:
        raise ValueError(f"O arquivo não é uma imagem válida: {caminho}") from None
    except OSError:
        raise ValueError(
            f"Não foi possível abrir a imagem de referência: {caminho}"
        ) from None
    if min(img.size) < 64:
        raise ValueError(
            "A imagem de referência precisa ter pelo menos 64 px em cada lado."
        )
    if not 1 / 2.5 <= img.width / img.height <= 2.5:
        raise ValueError(
            "A proporção da imagem de referência deve ficar entre 1:2,5 e 2,5:1."
        )
    img.thumbnail((2048, 2048))  # a Bedrock aceita no máximo ~9,4 megapixels
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "PNG")
    return buf.getvalue()


@mcp.tool()
def gerar_imagem(
    prompt: Annotated[
        str, Field(description="O que desenhar, ex.: 'um robô regando plantas'")
    ],
    tipo: Annotated[Tipo, Field(description="Tipo de imagem a criar")] = "8bit",
    contexto: Annotated[
        str | None,
        Field(
            description="Onde ou para que a imagem será usada, ex.: 'ícone para slide"
            " de aula sobre eletricidade'. Orienta composição e detalhes (opcional)"
        ),
    ] = None,
    imagem_referencia: Annotated[
        str | None,
        Field(
            description="Caminho de uma imagem local para redesenhar no tipo escolhido (opcional)"
        ),
    ] = None,
) -> list[Image | str]:
    """Gera um PNG com fundo transparente no tipo escolhido (8bit ou pixel art), a partir
    de um texto ou convertendo uma imagem local."""
    preset = TIPOS[tipo]
    try:
        referencia = ler_referencia(imagem_referencia) if imagem_referencia else None
        png = gerar(
            montar_prompt(prompt, tipo, contexto),
            NEGATIVO,
            (RAIZ / "assets" / "estilos" / f"{tipo}.png").read_bytes(),
            preset.fidelidade,
            referencia,
        )
        png = remover_fundo(png)
    except (ValueError, RuntimeError) as e:
        # Só ToolError chega ao cliente com a mensagem; outras exceções viram erro genérico.
        raise ToolError(str(e)) from e
    final = pixelizar(PILImage.open(io.BytesIO(png)), preset.pixels, preset.cores)
    destino = (
        RAIZ / "outputs" / f"{tipo}-{datetime.now().astimezone():%Y%m%d-%H%M%S-%f}.png"
    )
    final.save(destino)
    return [Image(path=destino), f"PNG com fundo transparente salvo em {destino}"]


if __name__ == "__main__":
    mcp.run()
