from pathlib import Path
from typing import get_args

import pytest

from prompts.estilo_prompt import ESTILOS, Estilo, montar_prompt

ESTILOS_DIR = Path(__file__).parents[1] / "assets" / "estilos"


def test_todo_estilo_do_schema_tem_preset_e_imagem_de_referencia():
    assert set(get_args(Estilo)) == set(ESTILOS)
    for estilo in ESTILOS:
        assert (ESTILOS_DIR / f"{estilo}.png").is_file()


@pytest.mark.parametrize("estilo", get_args(Estilo))
def test_prompt_junta_tema_e_estilo(estilo):
    final = montar_prompt("  um robô regando plantas ", estilo)
    assert final == f"um robô regando plantas. {ESTILOS[estilo].descricao}"


def test_prompt_vazio_falha():
    with pytest.raises(ValueError):
        montar_prompt("   ", "8bit")
