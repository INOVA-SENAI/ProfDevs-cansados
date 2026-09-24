import random

import pytest
from PIL import Image, ImageDraw

from app.pixel_grid import pixelizar


@pytest.mark.parametrize("tamanho", [(1024, 1024), (1000, 700)])
def test_grade_de_blocos_iguais_e_paleta_limitada(tamanho):
    ruido = Image.frombytes(
        "RGB", tamanho, random.Random(0).randbytes(tamanho[0] * tamanho[1] * 3)
    )
    saida = pixelizar(ruido, pixels=64, cores=16)

    bloco = max(tamanho) // 64
    assert saida.width % bloco == 0 and saida.height % bloco == 0
    assert len(saida.getcolors()) <= 16
    for x in range(0, saida.width, bloco):
        for y in range(0, saida.height, bloco):
            assert len(saida.crop((x, y, x + bloco, y + bloco)).getcolors()) == 1


def test_fundo_transparente_vira_binario_e_objeto_fica_opaco():
    # círculo vermelho com borda suavizada (alpha intermediário) sobre fundo transparente
    img = Image.new("RGBA", (1024, 1024), (0, 0, 0, 0))
    mascara = Image.new("L", (4096, 4096), 0)
    ImageDraw.Draw(mascara).ellipse((1024, 1024, 3072, 3072), fill=255)
    img.paste(
        (220, 30, 30, 255), mask=mascara.resize((1024, 1024), Image.Resampling.LANCZOS)
    )

    saida = pixelizar(img, pixels=64, cores=16)

    assert saida.mode == "RGBA"
    assert set(saida.getchannel("A").get_flattened_data()) == {0, 255}
    assert saida.getpixel((0, 0))[3] == 0  # canto = fundo
    assert saida.getpixel((512, 512)) == (220, 30, 30, 255)  # centro = objeto
