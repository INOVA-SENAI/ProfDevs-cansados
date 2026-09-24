import pytest
from PIL import Image

from senai_slides import Apresentacao, TextoLongoDemais
from senai_slides.apresentacao import (
    ALTURA,
    AZUL,
    BRANCO,
    CARTAO_LARGURA,
    LARANJA,
    LARGURA,
    MAX_ITENS,
    RAIO_NUMERO,
    VERDE,
    _cores_diagrama,
    _posicoes_diagrama,
)

ITEM = {"titulo": "Item", "texto": "Texto do item."}


def _perto(cor, esperada, tolerancia=40):
    return all(abs(a - b) <= tolerancia for a, b in zip(cor[:3], esperada, strict=True))


def _texto(palavra: str, limite: int) -> str:
    texto = palavra
    while len(f"{texto} {palavra}") <= limite:
        texto = f"{texto} {palavra}"
    return texto


def _ultimo(apres: Apresentacao) -> Image.Image:
    return apres.slides[-1].convert("RGB")


@pytest.fixture
def apres(tmp_path):
    return Apresentacao("Aula de Teste", pasta=tmp_path)


def test_capa_fundo_azul_logo_e_titulo(apres):
    apres.capa("Segurança do Trabalho")
    slide = _ultimo(apres)

    assert slide.size == (LARGURA, ALTURA)
    assert slide.getpixel((1800, 1000)) == AZUL
    logo = slide.crop((195, 112, 755, 205)).getcolors(100_000)
    assert any(_perto(c, BRANCO, 10) for _, c in logo)
    titulo = slide.crop((175, 700, 1745, 930)).getcolors(100_000)
    assert any(_perto(c, BRANCO, 10) for _, c in titulo)


@pytest.mark.parametrize("metodo", ["divisoria", "conteudo", "diagrama"])
def test_slides_internos_tem_barra_e_logo_azul(apres, metodo):
    if metodo == "divisoria":
        apres.divisoria("Seção")
    elif metodo == "conteudo":
        apres.conteudo("Título", ["Um tópico"])
    else:
        apres.diagrama("Centro", [ITEM] * MAX_ITENS)
    slide = _ultimo(apres)

    assert _perto(slide.getpixel((20, 40)), LARANJA)
    assert _perto(slide.getpixel((20, 800)), AZUL)
    logo = slide.crop((1639, 95, 1817, 142)).getcolors(100_000)
    assert any(_perto(c, AZUL, 25) for _, c in logo)
    assert slide.getpixel((1800, 1000)) == BRANCO


def test_destaque_laranja_com_ponto_final_verde(apres):
    apres.conteudo("Título", ["Tópico"], destaque="Segurança em primeiro lugar.")
    cores = [c for _, c in _ultimo(apres).crop((150, 820, 1400, 960)).getcolors(100_000)]

    assert any(_perto(c, LARANJA, 15) for c in cores)
    assert any(_perto(c, VERDE, 15) for c in cores)


@pytest.mark.parametrize("quantidade", range(2, MAX_ITENS + 1))
def test_diagrama_tem_um_cartao_por_item_nas_cores_da_paleta(apres, quantidade):
    apres.diagrama("Centro", [ITEM] * quantidade)
    slide = _ultimo(apres)

    cores = _cores_diagrama(quantidade)
    assert (cores[0], cores[-1]) == (LARANJA, AZUL)
    for (x, y, lado), cor in zip(_posicoes_diagrama(quantidade), cores, strict=True):
        ponta = x - CARTAO_LARGURA + 20 if lado < 0 else x + CARTAO_LARGURA - 20
        assert _perto(slide.getpixel((ponta, y)), cor, 5)
        assert _perto(slide.getpixel((x, y - RAIO_NUMERO + 8)), BRANCO, 30)


def test_diagrama_nao_encosta_na_logo_nem_na_borda(apres):
    item = {"titulo": _texto("Mecânica", 20), "texto": _texto("Manutenção", 70)}
    apres.diagrama(_texto("Manutenção", 30), [item] * MAX_ITENS)
    slide = _ultimo(apres)

    assert slide.crop((1500, 150, 1920, 200)).getcolors() == [(420 * 50, BRANCO)]
    assert slide.crop((1880, 0, 1920, 1080)).getcolors() == [(40 * 1080, BRANCO)]


def test_encerramento_tem_contatos(apres):
    apres.encerramento()
    slide = _ultimo(apres)

    assert slide.getpixel((100, 100)) == AZUL
    contatos = slide.crop((955, 380, 1700, 660)).getcolors(100_000)
    assert any(_perto(c, BRANCO, 10) for _, c in contatos)
    assert any(_perto(c, LARANJA, 15) for _, c in contatos)


def test_limites_documentados_no_agente_cabem(apres):
    apres.capa(_texto("Manutenção", 60))
    apres.divisoria(_texto("Máquinas", 40))
    apres.conteudo(_texto("Mecânica", 50), [_texto("Manutenção", 90)] * 5)
    apres.conteudo(
        _texto("Mecânica", 50),
        [_texto("Manutenção", 90)] * 3,
        destaque=_texto("Manutenção", 99) + ".",
    )
    item = {"titulo": _texto("Mecânica", 20), "texto": _texto("Manutenção", 70)}
    apres.diagrama(_texto("Manutenção", 30), [item] * MAX_ITENS)
    assert len(apres.slides) == 5


def test_texto_nao_invade_a_margem_direita(apres):
    apres.conteudo(
        _texto("Mecânica", 50),
        [_texto("Manutenção", 90)] * 3,
        destaque=_texto("Manutenção", 99) + ".",
    )
    slide = _ultimo(apres)

    faixa_direita = slide.crop((1540, 200, 1920, 1080)).getcolors(100_000)
    assert faixa_direita == [(380 * 880, BRANCO)]


def test_texto_absurdo_gera_erro_claro(apres):
    with pytest.raises(TextoLongoDemais, match="Encurte"):
        apres.capa("Palavra " * 60)


@pytest.mark.parametrize(
    ("chamada", "mensagem"),
    [
        (lambda a: a.capa(""), "título da capa"),
        (lambda a: a.divisoria("   "), "título da divisória"),
        (lambda a: a.conteudo("T", []), "1 a 6 tópicos"),
        (lambda a: a.conteudo("T", ["a"] * 7), "1 a 6 tópicos"),
        (lambda a: a.conteudo("T", "não é lista"), "1 a 6 tópicos"),
        (lambda a: a.conteudo("T", ["ok", ""]), "tópico"),
        (lambda a: a.conteudo("T", ["ok"], destaque=""), "destaque"),
        (lambda a: a.diagrama("", [ITEM] * 3), "título do diagrama"),
        (lambda a: a.diagrama("T", [ITEM]), "2 a 6 itens"),
        (lambda a: a.diagrama("T", [ITEM] * 7), "2 a 6 itens"),
        (lambda a: a.diagrama("T", "não é lista"), "2 a 6 itens"),
        (lambda a: a.diagrama("T", [ITEM, "só texto"]), "item 2 do diagrama"),
        (lambda a: a.diagrama("T", [ITEM, {"titulo": "Sem texto"}]), "texto do item 2"),
    ],
)
def test_entradas_invalidas(apres, chamada, mensagem):
    with pytest.raises(ValueError, match=mensagem):
        chamada(apres)


def test_nome_vira_pasta_sem_acentos(tmp_path):
    assert Apresentacao("Aula 1: Elétrica Básica!", pasta=tmp_path).nome == "aula_1_eletrica_basica"


def test_salvar_gera_pngs_e_pdf(apres, tmp_path, capsys):
    apres.capa("Capa")
    apres.divisoria("Seção")
    apres.encerramento()

    pasta = apres.salvar()

    assert pasta == tmp_path / "aula_de_teste"
    pngs = sorted(p.name for p in pasta.glob("*.png"))
    assert pngs == ["slide_01.png", "slide_02.png", "slide_03.png"]
    assert Image.open(pasta / "slide_01.png").size == (LARGURA, ALTURA)
    assert (pasta / "aula_de_teste.pdf").read_bytes().startswith(b"%PDF")
    assert "3 slides salvos" in capsys.readouterr().out


def test_salvar_de_novo_remove_slides_antigos(apres):
    for _ in range(3):
        apres.divisoria("Seção")
    apres.salvar()

    apres.slides = apres.slides[:1]
    pasta = apres.salvar()

    assert [p.name for p in pasta.glob("*.png")] == ["slide_01.png"]


def test_salvar_sem_slides_gera_erro(apres):
    with pytest.raises(ValueError, match="nenhum slide"):
        apres.salvar()
