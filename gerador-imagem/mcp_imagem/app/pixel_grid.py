"""Pós-processamento com Pillow: o código garante o que a IA faz mal (mesma ideia do logo_overlay).

Modelos de imagem desenham "pixel art" com pixels de tamanhos diferentes e bordas borradas.
Aqui a imagem vira uma grade real de blocos iguais, com paleta limitada. A transparência
também vira binária (cada bloco é 100% opaco ou 100% transparente), sem borda semitransparente.
"""

from PIL import Image


def pixelizar(img: Image.Image, pixels: int, cores: int) -> Image.Image:
    """Devolve RGBA. Imagem sem transparência sai toda opaca."""
    bloco = max(1, max(img.size) // pixels)
    pequena = img.convert("RGBA").resize(
        (img.width // bloco, img.height // bloco), Image.Resampling.BOX
    )
    opaco = pequena.getchannel("A").point(lambda a: 255 if a >= 128 else 0)
    saida = pequena.convert("RGB").quantize(colors=cores).convert("RGBA")
    saida.putalpha(opaco)
    return saida.resize(
        (saida.width * bloco, saida.height * bloco), Image.Resampling.NEAREST
    )
