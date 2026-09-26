import base64
import io
import os
import urllib.error

import pytest
from botocore.exceptions import ClientError, NoCredentialsError
from PIL import Image

from senai_slides.imagens import (
    CREDITO_IA,
    DESCRICAO,
    FIDELIDADE,
    NEGATIVO,
    STYLE_GUIDE,
    Estimativa,
    Ilustracao,
    _referencia,
    buscar_foto,
    carregar_env,
    estimativa,
    gerar_imagem,
    ilustracoes,
    montar_prompt,
    pedido,
    pedidos_do_deck,
)
from tests.conftest import pagina_do_commons

TOKEN = "AWS_BEARER_TOKEN_BEDROCK"


# Pedido e prompt


@pytest.mark.parametrize(
    ("valor", "esperado"),
    [
        ("a  robot   reading", ("gerar", "a robot reading")),
        ({"gerar": "a robot"}, ("gerar", "a robot")),
        ({"foto": " asphalt  paver "}, ("foto", "asphalt paver")),
    ],
)
def test_pedido(valor, esperado):
    assert pedido(valor) == esperado


DECK = {
    "titulo": "Asfalto",
    "imagem": {"foto": "asphalt paver"},
    "slides": [
        {"layout": "ilustracao", "titulo": "Usina", "imagem": "an asphalt plant"},
        {"layout": "topicos", "titulo": "Etapas"},
        {"layout": "ilustracao", "titulo": "Rolo", "imagem": {"gerar": "a road roller"}},
        {"layout": "ilustracao", "titulo": "Usina de novo", "imagem": "an  asphalt plant"},
    ],
}


def test_pedidos_do_deck():
    assert pedidos_do_deck(DECK) == (
        ("foto", "asphalt paver"),
        [("gerar", "an asphalt plant"), None, ("gerar", "a road roller"),
         ("gerar", "an asphalt plant")],
    )  # fmt: skip
    assert pedidos_do_deck({**DECK, "imagens": False}) == (None, [None] * 4)


def test_estimativa_conta_o_que_falta_e_o_custo(bedrock, commons, tmp_path):
    # A imagem repetida só é criada (e cobrada) uma vez.
    conta = estimativa(DECK, tmp_path)
    assert (conta.fotos, conta.geradas, conta.em_cache) == (1, 2, 0)
    assert conta.custo == pytest.approx(0.14)
    assert str(conta) == (
        "1 foto real a buscar (grátis) e 2 imagens a criar por IA (cerca de US$ 0,14)"
    )
    assert bedrock.chamadas == [] and commons.buscas == []

    capa, slides = pedidos_do_deck(DECK)
    ilustracoes({capa, *filter(None, slides)}, tmp_path / "asfalto" / "imagens")
    assert str(estimativa(DECK, tmp_path)) == "3 prontas no cache (sem custo)"
    assert estimativa(DECK, tmp_path).custo == 0


@pytest.mark.parametrize(
    ("conta", "texto"),
    [
        (Estimativa(0, 0, 0), "nenhuma"),
        (Estimativa(2, 0, 0), "2 fotos reais a buscar (grátis)"),
        (Estimativa(0, 1, 1), "1 imagem a criar por IA (cerca de US$ 0,07) e 1 pronta no cache "
                              "(sem custo)"),
    ],
)  # fmt: skip
def test_texto_da_estimativa(conta, texto):
    assert str(conta) == texto


def test_prompt_pede_foto_realista():
    assert montar_prompt("  an electrician   wearing gloves ") == (
        f"an electrician wearing gloves. {DESCRICAO}"
    )
    assert "pixel art" in NEGATIVO and "text" in NEGATIVO


def test_prompt_vazio_falha():
    with pytest.raises(ValueError, match="não pode ser vazia"):
        montar_prompt("   ")


def test_referencia_de_estilo_e_neutra():
    imagem = Image.open(io.BytesIO(base64.b64decode(_referencia())))
    assert imagem.size == (512, 512)
    topo, base = imagem.getpixel((256, 5)), imagem.getpixel((256, 506))
    assert sum(topo) > sum(base)  # luz em cima, sombra embaixo; nenhum objeto


# Credenciais do .env


def test_token_vazio_no_env_e_no_arquivo_e_removido(tmp_path, monkeypatch):
    arquivo = tmp_path / ".env"
    arquivo.write_text(f"{TOKEN}=\n")
    monkeypatch.setenv(TOKEN, "")

    carregar_env(arquivo)

    # sem a variável, o boto3 volta a usar o aws login / credenciais padrão
    assert TOKEN not in os.environ


def test_arquivo_preenche_so_o_que_o_ambiente_nao_trouxe(tmp_path, monkeypatch):
    arquivo = tmp_path / ".env"
    arquivo.write_text(f"{TOKEN}=do-arquivo\nAWS_REGION=us-west-2\n")
    monkeypatch.setenv(TOKEN, "")
    monkeypatch.setenv("AWS_REGION", "us-east-1")

    carregar_env(arquivo)

    assert os.environ[TOKEN] == "do-arquivo"
    assert os.environ["AWS_REGION"] == "us-east-1"


def test_sem_arquivo_env_nao_quebra(tmp_path, monkeypatch):
    monkeypatch.delenv(TOKEN, raising=False)
    carregar_env(tmp_path / "nao-existe.env")
    assert TOKEN not in os.environ


# Criar na Bedrock (simulada no conftest)


def test_cria_foto_realista_no_style_guide(bedrock):
    dados = gerar_imagem("an electrician wearing gloves")

    assert Image.open(io.BytesIO(dados)).size == (1024, 1024)
    [chamada] = bedrock.chamadas
    assert chamada["modelo"] == STYLE_GUIDE
    assert chamada["style_preset"] == "photographic"
    assert chamada["fidelity"] == FIDELIDADE
    assert chamada["aspect_ratio"] == "1:1"
    assert chamada["image"] == _referencia()
    assert chamada["prompt"] == montar_prompt("an electrician wearing gloves")
    assert chamada["negative_prompt"] == NEGATIVO


@pytest.mark.parametrize(
    ("erro", "mensagem"),
    [
        (
            ClientError({"Error": {"Code": "ExpiredTokenException", "Message": "Expirou."}}, "x"),
            "Falta uma credencial AWS válida",
        ),
        (
            ClientError({"Error": {"Code": "AccessDeniedException", "Message": "Negado"}}, "x"),
            "modelos da Stability AI estão ativos",
        ),
        (
            ClientError({"Error": {"Code": "ThrottlingException", "Message": "Calma"}}, "x"),
            "ficam no cache",
        ),
        (NoCredentialsError(), "Não foi possível chamar a Bedrock"),
    ],
)
def test_erros_da_bedrock_viram_mensagem_em_portugues(bedrock, erro, mensagem):
    bedrock.erro = erro
    with pytest.raises(RuntimeError, match=mensagem):
        gerar_imagem("a robot")


def test_imagem_barrada_pelo_filtro(bedrock):
    bedrock.resposta = {"images": [], "finish_reasons": ["Filter reason: prompt"]}
    with pytest.raises(RuntimeError, match="Filter reason: prompt"):
        gerar_imagem("a robot")


# Buscar no Wikimedia Commons (simulado no conftest)


def test_busca_so_fotos_e_escolhe_a_primeira_que_serve(commons):
    commons.paginas = [
        pagina_do_commons("File:Pequena.jpg", largura=640, altura=480),
        pagina_do_commons("File:Desenho.svg", mime="image/svg+xml"),
        pagina_do_commons("File:Proprietaria.jpg", licenca="All rights reserved"),
        pagina_do_commons("File:Nao-livre.jpg", nao_livre=True),
        pagina_do_commons("File:Boa.jpg", autor='<span class="fn">Ana <b>Souza</b></span>'),
        pagina_do_commons("File:Segunda.jpg"),
    ]
    dados, credito = buscar_foto("asphalt paver")

    assert commons.buscas == ["asphalt paver filetype:bitmap"]
    assert Image.open(io.BytesIO(dados)).size == (1280, 960)
    assert credito == "Foto: Ana Souza, CC BY-SA 4.0, via Wikimedia Commons"


def test_busca_sem_foto_livre(commons):
    commons.paginas = [pagina_do_commons(licenca="GFDL")]
    assert buscar_foto("something rare") is None


def test_busca_sem_internet(commons):
    commons.erro = urllib.error.URLError("sem rede")
    with pytest.raises(RuntimeError, match="Wikimedia Commons.*troque a `foto` por `gerar`"):
        buscar_foto("asphalt paver")


# Cache


def test_cache_nao_busca_nem_paga_duas_vezes(bedrock, commons, tmp_path, capsys):
    pedidos = {("foto", "asphalt paver"), ("gerar", "a robot"), ("gerar", "a padlock")}

    primeira = ilustracoes(pedidos, tmp_path)
    assert (len(commons.buscas), len(bedrock.chamadas)) == (1, 2)
    saida = capsys.readouterr().out
    assert "Buscando 1 foto(s)" in saida
    assert "Gerando 2 imagem(ns)" in saida

    segunda = ilustracoes(pedidos, tmp_path)
    assert (len(commons.buscas), len(bedrock.chamadas)) == (1, 2)
    assert capsys.readouterr().out == ""

    assert set(segunda) == pedidos
    assert all(isinstance(i, Ilustracao) for i in segunda.values())
    assert segunda[("foto", "asphalt paver")].credito.startswith("Foto: Fulano")
    assert segunda[("gerar", "a robot")].credito == CREDITO_IA
    assert (
        primeira[("gerar", "a robot")].imagem.tobytes()
        == segunda[("gerar", "a robot")].imagem.tobytes()
    )


def test_sem_foto_livre_a_imagem_e_criada_por_ia(bedrock, commons, tmp_path, capsys):
    commons.paginas = []
    [ilustracao] = ilustracoes({("foto", "electrician insulated gloves")}, tmp_path).values()

    assert ilustracao.credito == CREDITO_IA
    assert bedrock.chamadas[0]["prompt"].startswith("electrician insulated gloves.")
    assert "Nenhuma foto livre" in capsys.readouterr().out

    ilustracoes({("foto", "electrician insulated gloves")}, tmp_path)
    assert (len(commons.buscas), len(bedrock.chamadas)) == (1, 1)


def test_sem_pagar_so_entram_fotos_e_cache(bedrock, commons, tmp_path, capsys):
    pedidos = {("foto", "asphalt paver"), ("gerar", "a robot")}
    prontas = ilustracoes(pedidos, tmp_path, pagar=False)
    assert set(prontas) == {("foto", "asphalt paver")}
    assert bedrock.chamadas == []

    ilustracoes({("gerar", "a robot")}, tmp_path)  # com o custo aceito
    assert set(ilustracoes(pedidos, tmp_path, pagar=False)) == pedidos
    assert len(bedrock.chamadas) == 1

    commons.paginas = []
    assert ilustracoes({("foto", "road roller")}, tmp_path, pagar=False) == {}
    assert bedrock.chamadas[1:] == []
    assert "o slide fica sem imagem" in capsys.readouterr().out


def test_falha_em_uma_imagem_guarda_as_outras_no_cache(bedrock, tmp_path):
    bedrock.erro = NoCredentialsError()
    bedrock.so_falha_com = "padlock"
    pedidos = {("gerar", "a robot"), ("gerar", "a padlock"), ("gerar", "a helmet")}

    with pytest.raises(RuntimeError, match='Imagem "a padlock"'):
        ilustracoes(pedidos, tmp_path)
    assert len(list(tmp_path.glob("*.jpg"))) == 2
    assert not list(tmp_path.glob("*.tmp"))

    bedrock.erro = None
    ilustracoes(pedidos, tmp_path)
    assert len(bedrock.chamadas) == 4  # só a que tinha falhado foi gerada de novo
