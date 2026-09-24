import os

from server import carregar_env

TOKEN = "AWS_BEARER_TOKEN_BEDROCK"


def test_token_vazio_no_env_e_no_arquivo_e_removido(tmp_path, monkeypatch):
    arquivo = tmp_path / ".env"
    arquivo.write_text(f"{TOKEN}=\n")
    # ex.: "${AWS_BEARER_TOKEN_BEDROCK:-}" vindo do cliente MCP
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
