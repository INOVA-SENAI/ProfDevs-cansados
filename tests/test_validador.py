import copy

import pytest
import yaml

from senai_slides.gerador import gerar
from senai_slides.validador import (
    LIMITE_DESTAQUE,
    LIMITE_TEXTO_ITEM,
    LIMITE_TITULO,
    LIMITE_TITULO_ITEM,
    LIMITE_TOPICO,
    MAX_ITENS,
    MAX_SLIDES,
    main,
    validar_arquivo,
    validar_deck,
)

DECK = {
    "nome": "Aula de Teste",
    "slides": [
        {"tipo": "capa", "titulo": "Segurança do Trabalho"},
        {"tipo": "divisoria", "titulo": "Riscos"},
        {"tipo": "conteudo", "titulo": "Riscos elétricos", "topicos": ["Choque", "Arco"]},
        {"tipo": "divisoria", "titulo": "Controle"},
        {
            "tipo": "conteudo",
            "titulo": "Medidas",
            "topicos": ["Desenergizar", "Aterrar"],
            "destaque": "Sempre teste antes de tocar.",
        },
        {"tipo": "conteudo", "titulo": "EPIs", "topicos": ["Luvas", "Capacete"]},
        {"tipo": "encerramento"},
    ],
}

DIAGRAMA = {
    "tipo": "diagrama",
    "titulo": "Etapas",
    "itens": [
        {"titulo": "Desligar", "texto": "Abrir o circuito."},
        {"titulo": "Bloquear", "texto": "Travar o dispositivo."},
        {"titulo": "Testar", "texto": "Confirmar a ausência de tensão."},
    ],
}


def _texto(limite: int) -> str:
    """Texto com palavras reais e exatamente `limite` caracteres."""
    texto = "Manutenção"
    while len(texto) < limite:
        texto += " Manutenção"
    return texto[:limite].rstrip().ljust(limite, "o")


def _deck(**mudancas) -> dict:
    """Cópia do DECK. slide_3={"campo": valor} troca campos do slide 3; None apaga o campo."""
    deck = copy.deepcopy(DECK)
    for chave, campos in mudancas.items():
        slide = deck["slides"][int(chave.removeprefix("slide_")) - 1]
        for campo, valor in campos.items():
            if valor is None:
                slide.pop(campo, None)
            else:
                slide[campo] = valor
    return deck


def _deck_com_diagrama(**campos) -> dict:
    """DECK com o DIAGRAMA como slide 7, antes do encerramento. None apaga o campo."""
    deck = copy.deepcopy(DECK)
    diagrama = copy.deepcopy(DIAGRAMA)
    for campo, valor in campos.items():
        if valor is None:
            diagrama.pop(campo, None)
        else:
            diagrama[campo] = valor
    deck["slides"].insert(-1, diagrama)
    return deck


def _itens_com(numero: int, campo: str, valor: object) -> list[dict]:
    itens = copy.deepcopy(DIAGRAMA["itens"])
    itens[numero - 1][campo] = valor
    return itens


def _erros(deck) -> list[str]:
    return validar_deck(deck)[0]


def _avisos(deck) -> list[str]:
    erros, avisos = validar_deck(deck)
    assert erros == []
    return avisos


def test_deck_valido_nao_tem_erros_nem_avisos():
    assert validar_deck(DECK) == ([], [])


# Onda 1: estrutura


@pytest.mark.parametrize(
    ("dados", "mensagem"),
    [
        (None, "`nome` e `slides`"),
        (["capa"], "`nome` e `slides`"),
        ({"slides": DECK["slides"]}, "`nome` precisa"),
        ({"nome": 2026, "slides": DECK["slides"]}, "entre aspas"),
        ({"nome": "!!!", "slides": DECK["slides"]}, "letras ou números"),
        ({"nome": "Aula", "slides": []}, "pelo menos um slide"),
        ({"nome": "Aula", "slides": DECK["slides"], "autor": "Ana"}, "`autor` não existe"),
    ],
)
def test_estrutura_do_deck(dados, mensagem):
    assert any(mensagem in e for e in _erros(dados))


@pytest.mark.parametrize(
    ("campos", "mensagem"),
    [
        ({"tipo": "tabela"}, "Slide 3: `tipo` precisa ser um destes"),
        ({"tipo": None}, "Slide 3: `tipo`"),
        ({"topico": ["a", "b"]}, "o campo `topico` não existe"),
        ({"topicos": None}, "falta o campo `topicos`"),
        ({"titulo": None}, "falta o campo `titulo`"),
        ({"titulo": 10}, "`titulo` precisa ser um texto"),
        ({"titulo": "   "}, "`titulo` precisa ser um texto"),
        ({"topicos": "Choque e arco"}, "`topicos` precisa ser uma lista"),
        ({"topicos": ["Choque", ""]}, "`topicos` precisa ser uma lista"),
        ({"destaque": ""}, "`destaque` precisa ser um texto"),
    ],
)
def test_estrutura_do_slide(campos, mensagem):
    assert any(mensagem in e for e in _erros(_deck(slide_3=campos)))


def test_mostra_erros_de_estrutura_limite_e_ordem_de_uma_vez():
    deck = _deck(
        slide_1={"titulo": _texto(LIMITE_TITULO["capa"] + 1)},
        slide_3={"topico": ["a", "b"], "topicos": None},
    )
    deck["slides"].pop()  # sem encerramento
    erros = _erros(deck)

    assert any("o campo `topico` não existe" in e for e in erros)
    assert any("Slide 1 (capa): o título tem" in e for e in erros)
    assert "O último slide precisa ser o `encerramento`." in erros


def test_tipo_invalido_nao_derruba_as_outras_checagens():
    erros = _erros(_deck(slide_3={"tipo": "tabela"}, slide_1={"titulo": _texto(61)}))
    assert len(erros) == 2
    assert not any("primeiro slide" in e for e in erros)


def test_destaque_nulo_e_o_mesmo_que_sem_destaque():
    deck = _deck()
    deck["slides"][2]["destaque"] = None
    assert _erros(deck) == []


def test_encerramento_nao_aceita_campos():
    assert _erros(_deck(slide_7={"titulo": "Obrigado"})) == [
        "Slide 7 (encerramento): o campo `titulo` não existe. "
        "Campos aceitos: nenhum além de `tipo`."
    ]


# Onda 2: limites, ordem e quantidade


@pytest.mark.parametrize(
    ("slide", "campo", "limite"),
    [
        (1, "titulo", LIMITE_TITULO["capa"]),
        (2, "titulo", LIMITE_TITULO["divisoria"]),
        (3, "titulo", LIMITE_TITULO["conteudo"]),
        (5, "destaque", LIMITE_DESTAQUE),
    ],
)
def test_limites_de_texto(slide, campo, limite):
    assert _erros(_deck(**{f"slide_{slide}": {campo: _texto(limite)}})) == []

    erros = _erros(_deck(**{f"slide_{slide}": {campo: _texto(limite + 1)}}))
    assert len(erros) == 1
    assert f"tem {limite + 1} caracteres; o limite é {limite}" in erros[0]


def test_limite_do_topico():
    assert _erros(_deck(slide_3={"topicos": ["Choque", _texto(LIMITE_TOPICO)]})) == []
    erros = _erros(_deck(slide_3={"topicos": ["Choque", _texto(LIMITE_TOPICO + 1)]}))
    assert len(erros) == 1
    assert "o tópico 2 tem" in erros[0]


def test_espacos_extras_nao_contam_no_limite():
    titulo = _texto(LIMITE_TITULO["divisoria"]).replace(" ", "     ")
    assert _erros(_deck(slide_2={"titulo": titulo})) == []


@pytest.mark.parametrize(
    ("quantidade", "com_destaque", "passa"),
    [
        (1, False, False),
        (2, False, True),
        (5, False, True),
        (6, False, False),
        (3, True, True),
        (4, True, False),
    ],
)
def test_quantidade_de_topicos(quantidade, com_destaque, passa):
    campos = {"topicos": [f"Tópico {i}" for i in range(quantidade)]}
    if com_destaque:
        campos["destaque"] = "Frase de impacto."
    assert (_erros(_deck(slide_3=campos)) == []) is passa


def test_capa_primeiro_e_encerramento_por_ultimo():
    deck = _deck()
    deck["slides"].reverse()
    erros = _erros(deck)
    assert "O primeiro slide precisa ser a `capa`." in erros
    assert "O último slide precisa ser o `encerramento`." in erros


def test_so_uma_capa_e_um_encerramento():
    deck = _deck()
    deck["slides"].insert(1, {"tipo": "capa", "titulo": "Outra capa"})
    deck["slides"].insert(-1, {"tipo": "encerramento"})
    erros = _erros(deck)
    assert any("2 slides `capa`" in e for e in erros)
    assert any("2 slides `encerramento`" in e for e in erros)


def test_maximo_de_slides():
    deck = _deck()
    for i in range(MAX_SLIDES - len(deck["slides"]) + 1):
        deck["slides"].insert(
            -1, {"tipo": "conteudo", "titulo": f"Parte {i}", "topicos": ["a"] * 2}
        )
        if len(deck["slides"]) == MAX_SLIDES:
            assert _erros(deck) == []

    assert _erros(deck) == [
        f"O deck tem {MAX_SLIDES + 1} slides; o máximo é {MAX_SLIDES}. "
        "Divida a aula em duas apresentações."
    ]


# Onda 3: avisos


def test_aviso_de_destaque_demais():
    avisos = _avisos(_deck(slide_3={"destaque": "Uma."}, slide_6={"destaque": "Outra."}))
    assert any("3 de 3 slides de conteúdo têm destaque" in a for a in avisos)


def test_aviso_de_conteudo_antes_da_primeira_divisoria():
    deck = _deck()
    del deck["slides"][1]
    assert any("Slide 2: há conteúdo antes da primeira divisória" in a for a in _avisos(deck))


def test_aviso_de_secao_sem_conteudo():
    deck = _deck()
    deck["slides"].insert(-1, {"tipo": "divisoria", "titulo": "Encerrando"})
    assert any("Slide 7: a seção não tem nenhum slide" in a for a in _avisos(deck))


def test_aviso_de_titulo_em_caixa_alta():
    assert any("CAIXA ALTA" in a for a in _avisos(_deck(slide_3={"titulo": "RISCOS"})))


def test_aviso_de_destaque_sem_ponto_final():
    avisos = _avisos(_deck(slide_5={"destaque": "Sempre teste antes de tocar"}))
    assert any("ponto final" in a for a in avisos)


def test_aviso_de_titulo_repetido():
    avisos = _avisos(_deck(slide_6={"titulo": "riscos elétricos"}))
    assert "Slide 6: repete o título do slide 3." in avisos


# Diagrama


def test_deck_com_diagrama_nao_tem_erros_nem_avisos():
    assert validar_deck(_deck_com_diagrama()) == ([], [])


@pytest.mark.parametrize(
    ("campos", "mensagem"),
    [
        ({"itens": None}, "Slide 7 (diagrama): falta o campo `itens`"),
        ({"topicos": ["a", "b"]}, "o campo `topicos` não existe"),
        ({"itens": "Desligar e bloquear"}, "`itens` precisa ser uma lista"),
        ({"itens": ["Desligar", "Bloquear", "Testar"]}, "`itens` precisa ser uma lista"),
        ({"itens": _itens_com(2, "icone", "lupa")}, "o item 2 tem o campo `icone`"),
        ({"itens": _itens_com(2, "texto", None)}, "o `texto` do item 2 precisa ser um texto"),
        ({"itens": _itens_com(3, "titulo", 10)}, "o `titulo` do item 3 precisa ser um texto"),
    ],
)
def test_estrutura_do_diagrama(campos, mensagem):
    assert any(mensagem in e for e in _erros(_deck_com_diagrama(**campos)))


def test_item_sem_texto():
    itens = copy.deepcopy(DIAGRAMA["itens"])
    del itens[0]["texto"]
    assert _erros(_deck_com_diagrama(itens=itens)) == [
        "Slide 7 (diagrama): falta o campo `texto` no item 1."
    ]


@pytest.mark.parametrize(
    ("quantidade", "mensagem"),
    [
        (2, "prefira um slide de `conteudo`"),
        (3, None),
        (MAX_ITENS, None),
        (MAX_ITENS + 1, "divida em dois slides"),
    ],
)
def test_quantidade_de_itens(quantidade, mensagem):
    itens = [{"titulo": f"Item {i}", "texto": "Texto."} for i in range(quantidade)]
    erros = _erros(_deck_com_diagrama(itens=itens))
    if mensagem is None:
        assert erros == []
    else:
        assert len(erros) == 1
        assert f"tem {quantidade} itens; use de 3 a {MAX_ITENS}" in erros[0]
        assert mensagem in erros[0]


@pytest.mark.parametrize(
    ("campo", "limite", "descricao"),
    [
        ("titulo", LIMITE_TITULO_ITEM, "título do item 2"),
        ("texto", LIMITE_TEXTO_ITEM, "texto do item 2"),
    ],
)
def test_limites_dos_itens(campo, limite, descricao):
    assert _erros(_deck_com_diagrama(itens=_itens_com(2, campo, _texto(limite)))) == []

    erros = _erros(_deck_com_diagrama(itens=_itens_com(2, campo, _texto(limite + 1))))
    assert len(erros) == 1
    assert f"o {descricao} tem {limite + 1} caracteres; o limite é {limite}" in erros[0]


def test_limite_do_titulo_do_diagrama():
    limite = LIMITE_TITULO["diagrama"]
    assert _erros(_deck_com_diagrama(titulo=_texto(limite))) == []
    erros = _erros(_deck_com_diagrama(titulo=_texto(limite + 1)))
    assert len(erros) == 1
    assert f"Slide 7 (diagrama): o título tem {limite + 1} caracteres" in erros[0]


def test_diagrama_basta_para_a_secao_nao_ficar_vazia():
    deck = _deck_com_diagrama()
    deck["slides"].insert(6, {"tipo": "divisoria", "titulo": "Procedimento"})
    assert _avisos(deck) == []


def test_aviso_de_diagrama_antes_da_primeira_divisoria():
    deck = _deck_com_diagrama()
    deck["slides"].insert(1, deck["slides"].pop(6))
    assert any("Slide 2: há conteúdo antes da primeira divisória" in a for a in _avisos(deck))


# Desenho: o que o validador aprova, a biblioteca consegue desenhar.


def test_deck_no_pior_caso_dos_limites_cabe_no_desenho(tmp_path):
    deck = _deck(
        slide_1={"titulo": _texto(LIMITE_TITULO["capa"])},
        slide_2={"titulo": _texto(LIMITE_TITULO["divisoria"])},
        slide_3={
            "titulo": _texto(LIMITE_TITULO["conteudo"]),
            "topicos": [_texto(LIMITE_TOPICO)] * 5,
        },
        slide_5={
            "titulo": "Medidas de controle " + _texto(LIMITE_TITULO["conteudo"] - 20),
            "topicos": [_texto(LIMITE_TOPICO)] * 3,
            "destaque": _texto(LIMITE_DESTAQUE - 1) + ".",
        },
    )
    item = {"titulo": _texto(LIMITE_TITULO_ITEM), "texto": _texto(LIMITE_TEXTO_ITEM)}
    deck["slides"].insert(
        -1,
        {
            "tipo": "diagrama",
            "titulo": _texto(LIMITE_TITULO["diagrama"]),
            "itens": [item] * MAX_ITENS,
        },
    )
    assert _erros(deck) == []
    assert len(list(gerar(deck, tmp_path).glob("slide_*.png"))) == 8


# Arquivo e linha de comando


def _salvar(pasta, nome, dados) -> str:
    arquivo = pasta / nome
    texto = dados if isinstance(dados, str) else yaml.safe_dump(dados, allow_unicode=True)
    arquivo.write_text(texto, encoding="utf-8")
    return str(arquivo)


def test_yaml_quebrado_informa_a_linha(tmp_path):
    arquivo = _salvar(tmp_path, "aula.yaml", "nome: Aula\nslides:\n  - tipo: capa\n   titulo: X\n")
    resultado = validar_arquivo(arquivo)
    assert not resultado.ok
    assert "perto da linha 4" in resultado.erros[0]


def test_arquivo_fora_de_utf8(tmp_path):
    arquivo = tmp_path / "aula.yaml"
    arquivo.write_bytes("nome: Aula elétrica\n".encode("latin-1"))
    assert "UTF-8" in validar_arquivo(arquivo).erros[0]


def test_cli_gera_so_decks_sem_erro(tmp_path, capsys):
    bom = _salvar(tmp_path, "boa.yaml", DECK)
    ruim = _deck(slide_3={"topicos": ["só um"]})
    ruim["nome"] = "Aula ruim"
    _salvar(tmp_path, "ruim.yaml", ruim)
    saida = tmp_path / "saida"

    assert main([str(tmp_path), "--gerar", "--saida", str(saida)]) == 1

    assert (saida / "aula_de_teste" / "aula_de_teste.pdf").exists()
    assert not (saida / "aula_ruim").exists()
    texto = capsys.readouterr().out
    assert f"{bom}: OK, 7 slides." in texto
    assert "1 erro. Corrija antes de gerar." in texto


def test_cli_sem_gerar_nao_cria_arquivos(tmp_path):
    arquivo = _salvar(tmp_path, "boa.yml", DECK)
    assert main([arquivo, "--saida", str(tmp_path / "saida")]) == 0
    assert not (tmp_path / "saida").exists()


def test_cli_arquivo_inexistente(tmp_path, capsys):
    assert main([str(tmp_path / "nao_existe.yaml")]) == 1
    assert "não encontrado" in capsys.readouterr().out


def test_cli_pasta_sem_yaml(tmp_path, capsys):
    assert main([str(tmp_path)]) == 1
    assert "Nenhum arquivo .yaml" in capsys.readouterr().out
