import re
from pathlib import Path

import yaml

from senai_slides.gerador import gerar
from senai_slides.validador import validar_deck

RAIZ = Path(__file__).resolve().parent.parent
AGENTE = RAIZ / "agente" / "AGENTE_SLIDES_SENAI.md"


def _exemplo_do_agente() -> dict:
    blocos = re.findall(r"```yaml\n(.*?)```", AGENTE.read_text(encoding="utf-8"), re.S)
    assert len(blocos) == 1, "O agente deve ter exatamente um exemplo de deck em YAML."
    return yaml.safe_load(blocos[0])


def test_exemplo_do_agente_passa_no_validador_sem_avisos():
    assert validar_deck(_exemplo_do_agente()) == ([], [])


def test_exemplo_do_agente_gera_os_slides(tmp_path):
    pasta = gerar(_exemplo_do_agente(), tmp_path)

    assert len(list(pasta.glob("slide_*.png"))) == 8
    assert (pasta / "nr_10_introducao.pdf").exists()


def test_exemplo_do_agente_e_o_mesmo_de_slides_exemplo():
    exemplo = yaml.safe_load((RAIZ / "slides" / "exemplo.yaml").read_text(encoding="utf-8"))
    assert exemplo == _exemplo_do_agente()
