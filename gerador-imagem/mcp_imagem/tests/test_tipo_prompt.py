from pathlib import Path
from typing import get_args

import pytest

from prompts.tipo_prompt import ISOLADO, TIPOS, Tipo, montar_prompt

ESTILOS_DIR = Path(__file__).parents[1] / "assets" / "estilos"


def test_todo_tipo_do_schema_tem_preset_e_imagem_de_referencia():
    assert set(get_args(Tipo)) == set(TIPOS)
    for tipo in TIPOS:
        assert (ESTILOS_DIR / f"{tipo}.png").is_file()


@pytest.mark.parametrize("tipo", get_args(Tipo))
def test_prompt_junta_tema_tipo_e_fundo_liso(tipo):
    final = montar_prompt("  um robô regando plantas ", tipo)
    assert final == f"um robô regando plantas. {TIPOS[tipo].descricao}. {ISOLADO}"


def test_contexto_entra_no_prompt_e_vazio_e_ignorado():
    com = montar_prompt("árvore", "8bit", " ícone para slide de aula de biologia ")
    assert com.startswith("árvore. Context: ícone para slide de aula de biologia. ")
    assert montar_prompt("árvore", "8bit", "   ") == montar_prompt("árvore", "8bit")


def test_prompt_vazio_falha():
    with pytest.raises(ValueError):
        montar_prompt("   ", "8bit")
