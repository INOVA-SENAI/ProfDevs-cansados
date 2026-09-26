"""Confere a skill, os hooks e o caça-segredos que ficam em .kiro/ e scripts/."""

import importlib.util
import json
import re
from pathlib import Path

import pytest
import yaml

RAIZ = Path(__file__).resolve().parent.parent
KIRO = RAIZ / ".kiro"
SKILL = KIRO / "skills" / "gerador-slides" / "SKILL.md"

# Nomes de gatilho aceitos pelo Kiro (kiro.dev/docs/hooks).
GATILHOS = {
    "PromptSubmit",
    "AgentStop",
    "SessionStart",
    "PreToolUse",
    "PostToolUse",
    "FileCreate",
    "FileSave",
    "FileDelete",
    "PreTaskExecution",
    "PostTaskExecution",
}


def _hooks() -> dict[str, dict]:
    hooks = {}
    for arquivo in (KIRO / "hooks").glob("*.json"):
        dados = json.loads(arquivo.read_text(encoding="utf-8"))
        assert dados["version"] == "v1", arquivo.name
        for hook in dados["hooks"]:
            hooks[hook["name"]] = hook
    return hooks


def test_skill_tem_name_e_description():
    texto = SKILL.read_text(encoding="utf-8")
    frontmatter = yaml.safe_load(re.match(r"---\n(.*?)\n---\n", texto, re.S).group(1))

    assert frontmatter["name"] == SKILL.parent.name
    assert re.fullmatch(r"[a-z0-9-]{1,64}", frontmatter["name"])
    assert 0 < len(frontmatter["description"]) <= 1024
    assert "slides" in frontmatter["description"]


def test_skill_so_cita_arquivos_que_existem():
    texto = SKILL.read_text(encoding="utf-8")
    assert "python -m senai_slides.validador" in texto
    for caminho in ("agente/AGENTE_SLIDES_SENAI.md", "slides/exemplo.yaml"):
        assert caminho in texto
        assert (RAIZ / caminho).exists()


def test_hooks_usam_gatilhos_validos():
    hooks = _hooks()
    assert set(hooks) == {"Validar e gerar slides", "Caça-segredos"}
    for hook in hooks.values():
        assert hook["trigger"] in GATILHOS
        assert hook["action"]["type"] == "command"


@pytest.mark.parametrize(
    ("caminho", "casa"),
    [
        ("slides/exemplo.yaml", True),
        ("slides\\aula.yml", True),
        (str(RAIZ / "slides" / "aula.yaml"), True),
        ("slides/aula.md", False),
        ("tests/dados.yaml", False),
    ],
)
def test_hook_de_slides_so_dispara_para_decks(caminho, casa):
    matcher = _hooks()["Validar e gerar slides"]["matcher"]
    assert bool(re.search(matcher, caminho)) is casa


def _caca_segredos():
    arquivo = RAIZ / "scripts" / "caca_segredos.py"
    spec = importlib.util.spec_from_file_location("caca_segredos", arquivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# Montadas em partes para este arquivo não disparar o próprio caça-segredos.
CHAVE_FALSA = "AKIA" + "ABCDEFGHIJKLMNOP"
SEGREDO_FALSO = "aws_" + "secret_access_key = abc123"
BEDROCK = "AWS_BEARER_TOKEN_" + "BEDROCK"


@pytest.mark.parametrize(
    ("conteudo", "achados"),
    [
        (f"chave = '{CHAVE_FALSA}'\n", 1),
        (f"linha 1\n{SEGREDO_FALSO}\n", 1),
        (f"{BEDROCK}={'ABSK' + 'x1y2z3' * 8}\n", 1),
        (f"# {BEDROCK}=\nAWS_REGION=us-east-1\n", 0),
        ("Hook que busca por AKIA e aws_secret no código.\n", 0),
        ("nome: Aula\n", 0),
    ],
)
def test_caca_segredos(tmp_path, conteudo, achados):
    arquivo = tmp_path / "config.py"
    arquivo.write_text(conteudo, encoding="utf-8")
    assert len(_caca_segredos().procurar([arquivo])) == achados


def test_caca_segredos_ignora_binarios_e_arquivos_apagados(tmp_path):
    binario = tmp_path / "logo.png"
    binario.write_bytes(b"\x89PNG\0" + CHAVE_FALSA.encode())
    assert _caca_segredos().procurar([binario, tmp_path / "apagado.txt"]) == []


def test_caca_segredos_nao_mostra_a_chave(tmp_path, capsys):
    arquivo = tmp_path / "config.py"
    arquivo.write_text(CHAVE_FALSA, encoding="utf-8")

    assert _caca_segredos().main([str(arquivo)]) == 1
    saida = capsys.readouterr().out
    assert "config.py:1" in saida
    assert CHAVE_FALSA not in saida


def test_repositorio_sem_segredos(monkeypatch):
    monkeypatch.chdir(RAIZ)
    assert _caca_segredos().main([]) == 0
