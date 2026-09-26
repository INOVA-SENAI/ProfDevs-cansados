import re
from pathlib import Path

import yaml

from senai_slides.gerador import gerar
from senai_slides.icones import ICONES
from senai_slides.imagens import pedido
from senai_slides.validador import validar_deck

RAIZ = Path(__file__).resolve().parent.parent
AGENTE = RAIZ / "agente" / "AGENTE_SLIDES_SENAI.md"


def _exemplo_do_agente() -> dict:
    blocos = re.findall(r"```yaml\n(.*?)```", AGENTE.read_text(encoding="utf-8"), re.S)
    assert len(blocos) == 1, "O agente deve ter exatamente um exemplo de deck em YAML."
    return yaml.safe_load(blocos[0])


def test_exemplo_do_agente_passa_no_validador_sem_avisos():
    assert validar_deck(_exemplo_do_agente()) == ([], [])


def test_exemplo_do_agente_usa_varios_layouts():
    layouts = {s["layout"] for s in _exemplo_do_agente()["slides"]}
    assert {"ilustracao", "diagrama", "tabela", "comparacao"} <= layouts
    assert len(layouts) >= 6


def test_exemplo_do_agente_gera_os_slides(tmp_path, bedrock, commons):
    exemplo = _exemplo_do_agente()
    pasta = gerar(exemplo, tmp_path)

    # A capa e cada slide `ilustracao` têm uma imagem: foto real ou criada por IA.
    imagens = [exemplo["imagem"]] + [
        s["imagem"] for s in exemplo["slides"] if s["layout"] == "ilustracao"
    ]
    modos = [pedido(i)[0] for i in imagens]
    assert {"foto", "gerar"} <= set(modos)
    assert len(bedrock.chamadas) == modos.count("gerar")
    assert len(commons.buscas) == modos.count("foto")
    assert len(list((pasta / "imagens").glob("*.jpg"))) == len(imagens)
    # capa + agenda + uma divisória por seção + conteúdo + encerramento
    total = 1 + 1 + len(exemplo["secoes"]) + len(exemplo["slides"]) + 1
    assert len(list(pasta.glob("slide_*.png"))) == total
    assert (pasta / "nr_10_introducao.pptx").exists()
    assert (pasta / "nr_10_introducao.pdf").exists()


def test_agente_lista_exatamente_os_icones_permitidos():
    texto = AGENTE.read_text(encoding="utf-8")
    secao = texto.split("## 5. Ícones permitidos")[1].split("## 6.")[0]
    listados = re.search(r"```\n(.*?)```", secao, re.S).group(1).split()
    assert listados == ICONES


def test_exemplo_do_agente_e_o_mesmo_de_slides_exemplo():
    exemplo = yaml.safe_load((RAIZ / "slides" / "exemplo.yaml").read_text(encoding="utf-8"))
    assert exemplo == _exemplo_do_agente()
