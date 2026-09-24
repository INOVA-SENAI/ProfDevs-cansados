"""Procura chaves da AWS nos arquivos do repositório. Sai com código 1 se achar alguma.

Uso:
    python scripts/caca_segredos.py              arquivos versionados e novos (fora do .gitignore)
    python scripts/caca_segredos.py a.py b.yaml  só os arquivos informados
"""

import re
import subprocess
import sys
from pathlib import Path

PADROES = {
    "chave de acesso da AWS (AKIA/ASIA)": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "segredo da AWS (aws_secret...)": re.compile(r"aws_secret\w*\s*[=:]\s*\S+", re.IGNORECASE),
}


def arquivos_do_repositorio() -> list[Path]:
    saida = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        capture_output=True,
        check=True,
    ).stdout
    return [Path(p) for p in saida.decode("utf-8").split("\0") if p]


def procurar(arquivos: list[Path]) -> list[tuple[Path, int, str]]:
    achados = []
    for arquivo in arquivos:
        try:
            dados = arquivo.read_bytes()
        except OSError:  # apagado do disco, mas ainda no índice do git
            continue
        if b"\0" in dados[:8000]:  # binário (PNG, PDF...)
            continue
        for n, linha in enumerate(dados.decode("utf-8", "ignore").splitlines(), start=1):
            for tipo, padrao in PADROES.items():
                if padrao.search(linha):
                    achados.append((arquivo, n, tipo))
    return achados


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    sys.stdout.reconfigure(encoding="utf-8")  # o hook do Kiro lê a saída por pipe
    arquivos = [Path(a) for a in argv] or arquivos_do_repositorio()
    achados = procurar(arquivos)
    # O valor encontrado nunca é impresso, para não vazar a chave no log.
    for arquivo, n, tipo in achados:
        print(f"{arquivo}:{n}: possível {tipo}. Remova do arquivo e troque a chave.")
    if achados:
        print(f"{len(achados)} possível(is) segredo(s) encontrado(s). Não faça commit.")
        return 1
    print(f"Nenhum segredo encontrado em {len(arquivos)} arquivos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
