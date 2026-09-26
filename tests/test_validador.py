import copy

import pytest
import yaml
from botocore.exceptions import NoCredentialsError

from senai_slides.gerador import gerar
from senai_slides.validador import (
    LIMITE,
    LIMITE_TEXTO_ITEM,
    MAX_SLIDES,
    main,
    validar_arquivo,
    validar_deck,
)


def _item(n: int, **campos) -> dict:
    return {"icone": "lightbulb", "titulo": f"Item {n}", "texto": f"Texto do item {n}.", **campos}


DECK = {
    "nome": "Aula de Teste",
    "titulo": "Segurança do Trabalho",
    "uc": "Instalações Elétricas",
    "tags": ["segurança", "NR-10"],
    "imagem": "an electrician wearing insulated gloves",
    "secoes": [{"nome": "Riscos", "descricao": "O que pode dar errado"}, {"nome": "Controle"}],
    "slides": [
        {"layout": "cartoes", "secao": "Riscos", "titulo": "Principais riscos",
         "itens": [_item(1), _item(2), _item(3)]},
        {"layout": "ilustracao", "secao": "Riscos", "titulo": "Onde o risco aparece",
         "itens": [_item(1), _item(2)], "imagem": "sparks flying from an electrical panel"},
        {"layout": "destaque", "secao": "Riscos", "titulo": "Regra de ouro",
         "destaque": "Todo circuito está energizado até prova em contrário."},
        {"layout": "diagrama", "secao": "Controle", "titulo": "Etapas",
         "itens": [_item(1), _item(2), _item(3)]},
        {"layout": "tabela", "secao": "Controle", "titulo": "Quem pode trabalhar",
         "tabela": {"cabecalho": ["Perfil", "Definição"],
                    "linhas": [["Qualificado", "Tem curso"], ["Habilitado", "Tem registro"]]}},
    ],
}  # fmt: skip


def _texto(limite: int) -> str:
    """Texto com palavras reais e exatamente `limite` caracteres."""
    texto = "Manutenção"
    while len(texto) < limite:
        texto += " Manutenção"
    return texto[:limite].rstrip().ljust(limite, "o")


def _deck(**mudancas) -> dict:
    """Cópia do DECK. slide_3={"campo": valor} troca campos do slide 3; None apaga o campo.
    As demais chaves trocam campos do deck."""
    deck = copy.deepcopy(DECK)
    for chave, valor in mudancas.items():
        if chave.startswith("slide_"):
            slide = deck["slides"][int(chave.removeprefix("slide_")) - 1]
            for campo, novo in valor.items():
                if novo is None:
                    slide.pop(campo, None)
                else:
                    slide[campo] = novo
        elif valor is None:
            deck.pop(chave, None)
        else:
            deck[chave] = valor
    return deck


def _erros(deck) -> list[str]:
    return validar_deck(deck)[0]


def _avisos(deck) -> list[str]:
    erros, avisos = validar_deck(deck)
    assert erros == []
    return avisos


def _tem(mensagem: str, mensagens: list[str]) -> bool:
    return any(mensagem in m for m in mensagens)


def test_deck_valido_nao_tem_erros_nem_avisos():
    assert validar_deck(DECK) == ([], [])


def test_formato_antigo_tem_um_erro_so():
    antigo = {"nome": "Aula", "slides": [{"tipo": "capa", "titulo": "X"}, {"tipo": "encerramento"}]}
    erros, avisos = validar_deck(antigo)
    assert len(erros) == 1 and avisos == []
    assert "formato antigo" in erros[0]


# O deck


@pytest.mark.parametrize(
    ("mudancas", "mensagem"),
    [
        ({"titulo": None}, "Capa: falta o campo `titulo`"),
        ({"titulo": 2026}, "`titulo` precisa ser um texto"),
        ({"titulo": _texto(LIMITE["titulo_capa"] + 1)}, "o limite é 60"),
        ({"autor": "Ana"}, "Campo `autor` não existe no deck"),
        ({"modo": "rapido"}, "`modo` precisa ser `resumido` ou `aprofundado`"),
        ({"estilo_imagens": "pixelart"}, "Campo `estilo_imagens` não existe no deck"),
        ({"imagem": {"buscar": "x"}}, "`imagem` precisa ter `foto:`"),
        ({"imagem": {"foto": "x", "gerar": "y"}}, "`imagem` precisa ter `foto:`"),
        ({"imagem": {"foto": None}}, "falta o campo `imagem.foto`"),
        ({"imagem": {"foto": _texto(101)}}, "o limite é 100"),
        ({"imagem": {"gerar": _texto(301)}}, "o limite é 300"),
        ({"logo_curso": "sim"}, "`logo_curso` precisa ser `true` ou `false`"),
        ({"imagens": "não"}, "`imagens` precisa ser `true` ou `false`"),
        ({"imagens": False}, "Tire a `imagem` da capa"),
        ({"imagens": False, "imagem": None}, "Slide 2 (ilustracao): O deck está com"),
        ({"tags": "segurança"}, "`tags` precisa ser uma lista"),
        ({"tags": ["a", "b", "c", "d", "e", "f"]}, "no máximo 5 `tags`"),
        ({"tags": [_texto(21)]}, "a tag"),
        ({"secoes": "Riscos"}, "`secoes` precisa ser uma lista"),
        ({"secoes": [{"titulo": "Riscos"}]}, "Seção 1: o campo `titulo` não existe"),
        ({"slides": []}, "pelo menos um slide de conteúdo"),
    ],
)
def test_estrutura_do_deck(mudancas, mensagem):
    assert _tem(mensagem, _erros(_deck(**mudancas)))


def test_maximo_de_slides():
    deck = _deck(secoes=None)
    deck["slides"] = [
        {"layout": "destaque", "titulo": f"Parte {i}", "destaque": "Frase."}
        for i in range(MAX_SLIDES + 1)
    ]
    assert _tem(f"o máximo é {MAX_SLIDES}", _erros(deck))
    deck["slides"].pop()
    assert _erros(deck) == []


def test_arquivo_que_nao_e_um_deck():
    assert _tem("`titulo` e `slides`", _erros(["capa"]))


# Cada slide


@pytest.mark.parametrize(
    ("campos", "mensagem"),
    [
        ({"layout": "tabelinha"}, "Slide 1: `layout` precisa ser um destes"),
        ({"titulo": None}, "Slide 1 (cartoes): falta o campo `titulo`"),
        ({"titulo": _texto(LIMITE["titulo"] + 1)}, "o limite é 50"),
        ({"imagem": "a robot"}, "o layout `cartoes` não usa o campo `imagem`"),
        ({"itens": [_item(1)]}, "tem 1 itens; o layout `cartoes` usa de 2 a 4"),
        ({"itens": "choque, arco"}, "`itens` precisa ser uma lista"),
        ({"itens": [_item(1), _item(2, cor="azul")]}, "item 2: o campo `cor` não existe"),
        (
            {"itens": [_item(1), {"icone": "bolt", "titulo": "Sem texto"}]},
            "item 2: falta o campo `texto`",
        ),
        ({"itens": [_item(1), _item(2, icone="raio")]}, "o ícone `raio` não está na lista"),
        ({"itens": [_item(1), _item(2, icone="bolts")]}, "Parecidos: bolt"),
        ({"destaque": 10}, "`destaque` precisa ser um texto"),
    ],
)
def test_estrutura_do_slide(campos, mensagem):
    assert _tem(mensagem, _erros(_deck(slide_1=campos)))


@pytest.mark.parametrize(
    ("layout", "campo"),
    [("destaque", "destaque"), ("tabela", "tabela"), ("ilustracao", "imagem")],
)
def test_campos_obrigatorios_do_layout(layout, campo):
    n = [s["layout"] for s in DECK["slides"]].index(layout) + 1
    assert _tem(
        f"Slide {n} ({layout}): falta o campo `{campo}`",
        _erros(_deck(**{f"slide_{n}": {campo: None}})),
    )


def test_diagrama_tem_titulo_curto_e_nao_tem_subtitulo():
    erros = _erros(
        _deck(slide_4={"titulo": _texto(LIMITE["titulo_diagrama"] + 1), "subtitulo": "X"})
    )
    assert _tem("o limite é 30", erros)
    assert _tem("o layout `diagrama` não usa o campo `subtitulo`", erros)


@pytest.mark.parametrize("modo", ["resumido", "aprofundado"])
def test_limite_do_texto_do_item_depende_do_modo(modo):
    limite = LIMITE_TEXTO_ITEM[modo]
    itens = [_item(1), _item(2, texto=_texto(limite))]
    assert _erros(_deck(modo=modo, slide_1={"itens": itens})) == []
    itens[1]["texto"] = _texto(limite + 1)
    assert _tem(f"o limite é {limite}", _erros(_deck(modo=modo, slide_1={"itens": itens})))


def test_item_so_com_titulo_vira_frase():
    frase = {"icone": "bolt", "titulo": _texto(LIMITE["frase_item"])}
    assert _erros(_deck(slide_2={"itens": [frase, frase]})) == []
    longa = {"icone": "bolt", "titulo": _texto(LIMITE["frase_item"] + 1)}
    assert _tem("o limite é 90", _erros(_deck(slide_2={"itens": [frase, longa]})))


def test_diagrama_limita_os_itens():
    itens = [_item(1), _item(2), _item(3, titulo=_texto(21))]
    assert _tem("o limite é 20", _erros(_deck(slide_4={"itens": itens})))


# Comparação, gráfico e tabela

COMPARACAO = {
    "layout": "comparacao",
    "titulo": "Coletivas e individuais",
    "colunas": [
        {"titulo": "Coletivas", "itens": ["Desenergizar", "Aterrar", "Sinalizar"]},
        {"titulo": "Individuais", "itens": ["Luvas", "Capacete", "Vestimenta"]},
    ],
}
GRAFICO = {
    "layout": "grafico",
    "titulo": "Acidentes por tipo",
    "grafico": {
        "tipo": "barras",
        "categorias": ["Choque", "Arco", "Queda"],
        "series": [{"nome": "2025", "valores": [3, 2, 1]}],
        "fonte": "Dados ilustrativos",
    },
}


def _com(slide: dict) -> dict:
    deck = _deck(secoes=None)
    for s in deck["slides"]:
        s.pop("secao")
    deck["slides"].append(copy.deepcopy(slide))
    return deck


def test_comparacao_e_grafico_validos():
    assert _erros(_com(COMPARACAO)) == []
    assert _erros(_com(GRAFICO)) == []


@pytest.mark.parametrize(
    ("mudar", "mensagem"),
    [
        (lambda s: s["colunas"].pop(), "exatamente 2 colunas"),
        (lambda s: s["colunas"][0]["itens"].pop(), "coluna 1: tem 2 itens; use de 3 a 6"),
        (lambda s: s["colunas"][1].pop("titulo"), "coluna 2: falta o campo `titulo`"),
    ],
)
def test_erros_da_comparacao(mudar, mensagem):
    slide = copy.deepcopy(COMPARACAO)
    mudar(slide)
    assert _tem(mensagem, _erros(_com(slide)))


@pytest.mark.parametrize(
    ("mudar", "mensagem"),
    [
        (lambda g: g.update(tipo="radar"), "o `tipo` do gráfico precisa ser um destes"),
        (lambda g: g.update(categorias=["Só uma"]), "lista de 2 a 12 rótulos"),
        (lambda g: g["series"][0].update(valores=["3", 2, 1]), "lista de números, sem aspas"),
        (lambda g: g["series"][0].update(valores=[3, 2]), "tem 2 valores para 3 categorias"),
        (lambda g: g.update(tipo="pizza", series=g["series"] * 2), "exatamente 1 série"),
        (lambda g: g.pop("fonte"), "falta o campo `fonte`"),
    ],
)
def test_erros_do_grafico(mudar, mensagem):
    slide = copy.deepcopy(GRAFICO)
    mudar(slide["grafico"])
    assert _tem(mensagem, _erros(_com(slide)))


def test_tabela_aceita_numeros_e_confere_as_linhas():
    tabela = {"cabecalho": ["Curso", "Horas"], "linhas": [["Básico", 40], ["SEP", 40]]}
    assert _erros(_deck(slide_5={"tabela": tabela})) == []
    tabela["linhas"].append(["Só uma célula"])
    assert _tem(
        "a linha 3 da tabela precisa ter 2 células", _erros(_deck(slide_5={"tabela": tabela}))
    )


# Seções


def test_secao_que_nao_existe():
    assert _tem('precisa ser o nome de uma das seções: "Riscos", "Controle"',
                _erros(_deck(slide_1={"secao": "Perigos"})))  # fmt: skip


def test_slides_da_mesma_secao_ficam_juntos():
    deck = _deck()
    deck["slides"][2]["secao"] = "Controle"
    deck["slides"][3]["secao"] = "Riscos"
    assert _tem('os slides da seção "Riscos" precisam ficar juntos', _erros(deck))


def test_secao_sem_slide():
    deck = _deck(secoes=DECK["secoes"] + [{"nome": "Extra"}])
    assert _tem('A seção "Extra" não tem nenhum slide', _erros(deck))


def test_secao_sem_lista_de_secoes():
    assert _tem("o deck não tem `secoes`", _erros(_deck(secoes=None)))


# Avisos


def test_aviso_de_layout_repetido_em_sequencia():
    deck = _deck()
    deck["slides"][1] = {**deck["slides"][0], "titulo": "Outros riscos"}
    assert _tem("Slides 1 e 2: os dois usam o layout `cartoes`", _avisos(deck))


def test_aviso_de_poucos_layouts():
    destaque = {"layout": "destaque", "destaque": "Frase."}
    tabela = {"layout": "tabela", "tabela": DECK["slides"][4]["tabela"]}
    deck = _deck(secoes=None)
    deck["slides"] = [{**[destaque, tabela][i % 2], "titulo": f"Parte {i}"} for i in range(5)]
    assert _tem("usa só 2 layouts diferentes", _avisos(deck))


@pytest.mark.parametrize("imagem", ["a classroom", {"gerar": "a classroom"}, {"foto": "classroom"}])
def test_formas_de_imagem(imagem):
    assert _erros(_deck(imagem=imagem, slide_2={"imagem": imagem})) == []


def test_avisos_de_imagem():
    assert _tem("A capa está sem `imagem`", _avisos(_deck(imagem=None)))
    deck = _deck()
    deck["slides"][1] = {"layout": "topicos", "secao": "Riscos", "titulo": "Onde o risco aparece",
                         "itens": [_item(1), _item(2)]}  # fmt: skip
    assert _tem("Nenhum slide usa o layout `ilustracao`", _avisos(deck))


def test_deck_sem_imagens_nao_tem_avisos_de_imagem():
    deck = _deck(imagens=False, imagem=None)
    deck["slides"][1] = {"layout": "topicos", "secao": "Riscos", "titulo": "Onde o risco aparece",
                         "itens": [_item(1), _item(2)]}  # fmt: skip
    assert _avisos(deck) == []


def test_aviso_de_titulo_repetido_e_dados_ilustrativos():
    deck = _com(GRAFICO)
    deck["slides"][2]["titulo"] = "principais riscos"
    avisos = _avisos(deck)
    assert _tem("Slide 3: repete o título do slide 1", avisos)
    assert _tem("Slide 6: o gráfico usa dados ilustrativos", avisos)


def test_aviso_de_notas_no_modo_aprofundado():
    avisos = _avisos(_deck(modo="aprofundado"))
    assert _tem("Slide 1: no modo aprofundado, escreva as `notas`", avisos)


# Desenho: o que o validador aprova, a biblioteca consegue desenhar.


def test_deck_no_pior_caso_dos_limites_cabe_no_desenho(tmp_path):
    texto = _texto(LIMITE_TEXTO_ITEM["aprofundado"])
    itens = [_item(i, titulo=_texto(LIMITE["titulo_item"]), texto=texto) for i in range(6)]
    diagrama = [_item(i, titulo=_texto(20), texto=_texto(70)) for i in range(6)]
    deck = _deck(
        modo="aprofundado",
        titulo=_texto(LIMITE["titulo_capa"]),
        slide_1={"titulo": _texto(LIMITE["titulo"]), "subtitulo": _texto(80), "itens": itens[:4],
                 "destaque": _texto(LIMITE["destaque"]), "notas": "Notas."},
        slide_2={"itens": itens[:5], "destaque": _texto(120), "notas": "Notas."},
        slide_3={"destaque": _texto(120), "notas": "Notas."},
        slide_4={"titulo": _texto(30), "itens": diagrama, "notas": "Notas."},
        slide_5={"notas": "Notas."},
    )  # fmt: skip
    assert _erros(deck) == []
    pasta = gerar(deck, tmp_path)
    assert len(list(pasta.glob("slide_*.png"))) == 1 + 1 + 2 + 5 + 1


# Arquivo e linha de comando


def _salvar(pasta, nome, dados) -> str:
    arquivo = pasta / nome
    texto = dados if isinstance(dados, str) else yaml.safe_dump(dados, allow_unicode=True)
    arquivo.write_text(texto, encoding="utf-8")
    return str(arquivo)


def test_yaml_quebrado_informa_a_linha(tmp_path):
    arquivo = _salvar(
        tmp_path, "aula.yaml", "titulo: Aula\nslides:\n  - layout: topicos\n   titulo: X\n"
    )
    resultado = validar_arquivo(arquivo)
    assert not resultado.ok
    assert "perto da linha 4" in resultado.erros[0]


def test_arquivo_fora_de_utf8(tmp_path):
    arquivo = tmp_path / "aula.yaml"
    arquivo.write_bytes("titulo: Aula elétrica\n".encode("latin-1"))
    assert "UTF-8" in validar_arquivo(arquivo).erros[0]


def test_cli_gera_so_decks_sem_erro(tmp_path, capsys):
    bom = _salvar(tmp_path, "boa.yaml", DECK)
    _salvar(tmp_path, "ruim.yaml", _deck(nome="Aula ruim", slide_1={"layout": "tabelinha"}))
    saida = tmp_path / "saida"

    assert main([str(tmp_path), "--gerar", "--saida", str(saida), "--sem-instalar-fontes"]) == 1

    assert (saida / "aula_de_teste" / "aula_de_teste.pptx").exists()
    assert (saida / "aula_de_teste" / "aula_de_teste.pdf").exists()
    assert not (saida / "aula_ruim").exists()
    texto = capsys.readouterr().out
    assert f"{bom}: OK, 5 slides de conteúdo." in texto
    assert "1 erro. Corrija antes de gerar." in texto


def test_cli_sem_gerar_nao_cria_arquivos(tmp_path, capsys):
    arquivo = _salvar(tmp_path, "boa.yml", DECK)
    assert main([arquivo, "--saida", str(tmp_path / "saida")]) == 0
    assert not (tmp_path / "saida").exists()
    assert "  Imagens: 2 imagens a criar por IA (cerca de US$ 0,14)." in capsys.readouterr().out


def test_cli_mostra_deck_sem_imagens(tmp_path, capsys):
    deck = _deck(imagens=False, imagem=None, slide_2={"layout": "topicos", "imagem": None})
    assert main([_salvar(tmp_path, "boa.yaml", deck)]) == 0
    assert "  Imagens: nenhuma (`imagens: false`)." in capsys.readouterr().out


def test_cli_so_cobra_com_aceitar_custo(tmp_path, bedrock, capsys):
    arquivo = _salvar(tmp_path, "boa.yaml", DECK)
    comando = [arquivo, "--gerar", "--saida", str(tmp_path / "saida"), "--sem-instalar-fontes"]

    assert main(comando) == 0
    assert bedrock.chamadas == []
    texto = capsys.readouterr().out
    assert "Custo não autorizado: 2 imagens a criar por IA (cerca de US$ 0,14)" in texto
    assert "--aceitar-custo" in texto
    assert (tmp_path / "saida" / "aula_de_teste" / "aula_de_teste.pptx").exists()

    assert main([*comando, "--aceitar-custo"]) == 0
    assert len(bedrock.chamadas) == 2

    assert main(comando) == 0  # já estão no cache: nada a autorizar
    assert len(bedrock.chamadas) == 2
    texto = capsys.readouterr().out
    assert "  Imagens: 2 prontas no cache (sem custo)." in texto
    assert "Custo não autorizado" not in texto


def test_cli_sem_imagens_nao_chama_a_bedrock(tmp_path, bedrock):
    arquivo = _salvar(tmp_path, "boa.yaml", DECK)
    saida = tmp_path / "saida"
    assert (
        main([arquivo, "--gerar", "--sem-imagens", "--saida", str(saida), "--sem-instalar-fontes"])
        == 0
    )
    assert bedrock.chamadas == []
    assert (saida / "aula_de_teste" / "aula_de_teste.pptx").exists()


def test_cli_erro_da_bedrock_nao_gera_o_deck(tmp_path, bedrock, capsys):
    bedrock.erro = NoCredentialsError()
    arquivo = _salvar(tmp_path, "boa.yaml", DECK)
    saida = tmp_path / "saida"

    comando = [arquivo, "--gerar", "--aceitar-custo", "--saida", str(saida)]
    assert main([*comando, "--sem-instalar-fontes"]) == 1

    assert not list(saida.glob("*/*.pptx"))
    texto = capsys.readouterr().out
    assert "erro ao gerar: Imagem" in texto
    assert "rode sem --aceitar-custo" in texto


def test_cli_arquivo_inexistente(tmp_path, capsys):
    assert main([str(tmp_path / "nao_existe.yaml")]) == 1
    assert "não encontrado" in capsys.readouterr().out


def test_cli_pasta_sem_yaml(tmp_path, capsys):
    assert main([str(tmp_path)]) == 1
    assert "Nenhum arquivo .yaml" in capsys.readouterr().out
