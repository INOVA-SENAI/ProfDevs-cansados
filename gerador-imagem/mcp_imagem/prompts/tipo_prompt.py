"""Monta o prompt final de cada tipo de imagem. Função pura: não chama API nenhuma."""

from typing import Literal, NamedTuple

# Para criar um tipo: acrescente o nome aqui, um Preset em TIPOS e assets/estilos/<nome>.png.
Tipo = Literal["8bit", "pixelart"]


class Preset(NamedTuple):
    # vai para o prompt; em inglês porque os modelos da Stability entendem melhor
    descricao: str
    pixels: int  # tamanho da grade final no lado maior (quantos "pixels de arte")
    cores: int  # tamanho máximo da paleta
    fidelidade: float  # 0 a 1: quanto a saída copia o estilo da imagem de referência


TIPOS: dict[str, Preset] = {
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

# A imagem final é PNG sem fundo: pedir um objeto isolado em fundo liso deixa a
# remoção de fundo limpa.
ISOLADO = (
    "single isolated subject, centered, fully visible, "
    "on a plain flat solid white background, no scenery"
)

NEGATIVO = (
    "blurry, smooth gradients, anti-aliasing, photorealistic, 3d render, text, "
    "watermark, logo, background scenery, landscape, sky, ground, frame, border"
)


def montar_prompt(prompt: str, tipo: Tipo, contexto: str | None = None) -> str:
    prompt = prompt.strip()
    if not prompt:
        raise ValueError("O prompt não pode ser vazio.")
    partes = [prompt]
    if contexto and contexto.strip():
        partes.append(f"Context: {contexto.strip()}")
    return ". ".join([*partes, TIPOS[tipo].descricao, ISOLADO])
