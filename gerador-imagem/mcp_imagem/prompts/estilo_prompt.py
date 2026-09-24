"""Monta o prompt final de cada estilo. Função pura: não chama API nenhuma."""

from typing import Literal, NamedTuple

Estilo = Literal["8bit", "pixelart"]


class Preset(NamedTuple):
    # vai para o prompt; em inglês porque os modelos da Stability entendem melhor
    descricao: str
    pixels: int  # tamanho da grade final no lado maior (quantos "pixels de arte")
    cores: int  # tamanho máximo da paleta
    fidelidade: float  # 0 a 1: quanto a saída copia o estilo da imagem de referência


ESTILOS: dict[str, Preset] = {
    "8bit": Preset(
        "8-bit NES-era video game sprite art, very low resolution, chunky square pixels, "
        "limited 16-color palette, flat colors, bold dark outlines, no anti-aliasing",
        pixels=64,
        cores=16,
        # 0,8 recopiava a cena de referência e ignorava o prompt (teste de 24/09/2026)
        fidelidade=0.5,
    ),
    "pixelart": Preset(
        "detailed 16-bit SNES-era pixel art, crisp pixel grid, limited palette, "
        "subtle dithering, clean hard edges, no anti-aliasing",
        pixels=128,
        cores=32,
        # 0,6 puxava as cores e o chão da referência para a cena (teste de 24/09/2026)
        fidelidade=0.4,
    ),
}

NEGATIVO = "blurry, smooth gradients, anti-aliasing, photorealistic, 3d render, text, watermark, logo"


def montar_prompt(prompt: str, estilo: Estilo) -> str:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("O prompt não pode ser vazio.")
    return f"{prompt}. {ESTILOS[estilo].descricao}"
