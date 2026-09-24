"""Pós-processamento com Pillow: o código garante o que a IA faz mal (mesma ideia do logo_overlay).

Modelos de imagem desenham "pixel art" com pixels de tamanhos diferentes e bordas borradas.
Aqui a imagem vira uma grade real de blocos iguais, com paleta limitada.
"""

from PIL import Image


def pixelizar(img: Image.Image, pixels: int, cores: int) -> Image.Image:
    bloco = max(1, max(img.size) // pixels)
    pequena = img.convert("RGB").resize(
        (img.width // bloco, img.height // bloco), Image.Resampling.BOX
    )
    pequena = pequena.quantize(colors=cores)
    return pequena.resize(
        (pequena.width * bloco, pequena.height * bloco), Image.Resampling.NEAREST
    )
