import random

import pytest
from PIL import Image

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
