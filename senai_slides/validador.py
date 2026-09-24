"""Confere decks de slides em YAML e, com --gerar, desenha os que passaram.

Uso:
    python -m senai_slides.validador slides/minha_aula.yaml
    python -m senai_slides.validador slides/ --gerar
"""

import argparse
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from senai_slides.apresentacao import TextoLongoDemais, _nome_de_pasta
from senai_slides.gerador import gerar

# Campos aceitos por tipo de slide; os obrigatórios são os que não estão em OPCIONAIS.
CAMPOS = {
    "capa": {"titulo"},
    "divisoria": {"titulo"},
    "conteudo": {"titulo", "topicos", "destaque"},
    "diagrama": {"titulo", "itens"},
    "encerramento": set(),
}
OPCIONAIS = {"destaque"}
CAMPOS_DO_ITEM = {"titulo", "texto"}
# Tipos que desenvolvem uma seção depois da divisória.
SECOES = {"conteudo", "diagrama"}

LIMITE_TITULO = {"capa": 60, "divisoria": 40, "conteudo": 50, "diagrama": 30}
LIMITE_TOPICO = 90
LIMITE_DESTAQUE = 100
LIMITE_TITULO_ITEM = 20
LIMITE_TEXTO_ITEM = 70
MIN_TOPICOS, MAX_TOPICOS = 2, 5
MAX_TOPICOS_COM_DESTAQUE = 3
MIN_ITENS, MAX_ITENS = 3, 6
MAX_SLIDES = 20

DICA_ASPAS = "Se o texto for um número ou sim/não, coloque-o entre aspas."


@dataclass
class Resultado:
    arquivo: Path
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    deck: dict | None = None

    @property
    def ok(self) -> bool:
        return not self.erros


def _e_texto(valor: object) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def _lista_tipos() -> str:
    return ", ".join(CAMPOS)


# Onda 1: o arquivo tem a forma certa?


def _estrutura_do_deck(dados: object) -> list[str]:
    if not isinstance(dados, dict):
        return ["O arquivo precisa ter os campos `nome` e `slides` no nível principal."]

    erros = []
    for campo in sorted(set(dados) - {"nome", "slides"}, key=str):
        erros.append(f"Campo `{campo}` não existe no deck. Use só `nome` e `slides`.")

    nome = dados.get("nome")
    if not _e_texto(nome):
        erros.append(f"`nome` precisa ser um texto não vazio (ex.: nome: Aula 1). {DICA_ASPAS}")
    else:
        try:
            _nome_de_pasta(nome)
        except ValueError as erro:
            erros.append(str(erro))

    slides = dados.get("slides")
    if not isinstance(slides, list) or not slides:
        erros.append("`slides` precisa ser uma lista com pelo menos um slide.")
    return erros


def _tipo_valido(slide: object) -> bool:
    tipo = slide.get("tipo") if isinstance(slide, dict) else None
    return isinstance(tipo, str) and tipo in CAMPOS


def _estrutura_do_slide(n: int, slide: object) -> list[str]:
    if not _tipo_valido(slide):
        return [f"Slide {n}: `tipo` precisa ser um destes: {_lista_tipos()}."]

    erros = []
    tipo = slide["tipo"]
    aceitos = CAMPOS[tipo]
    for campo in sorted(set(slide) - aceitos - {"tipo"}, key=str):
        lista = ", ".join(sorted(aceitos)) or "nenhum além de `tipo`"
        erros.append(f"Slide {n} ({tipo}): o campo `{campo}` não existe. Campos aceitos: {lista}.")
    for campo in sorted(aceitos - OPCIONAIS - set(slide)):
        erros.append(f"Slide {n} ({tipo}): falta o campo `{campo}`.")

    if "titulo" in aceitos and "titulo" in slide and not _e_texto(slide["titulo"]):
        erros.append(f"Slide {n} ({tipo}): `titulo` precisa ser um texto não vazio. {DICA_ASPAS}")
    # destaque: vazio (null) é o mesmo que não ter destaque.
    destaque = slide.get("destaque")
    if "destaque" in aceitos and destaque is not None and not _e_texto(destaque):
        erros.append(f"Slide {n} ({tipo}): `destaque` precisa ser um texto. {DICA_ASPAS}")

    if tipo == "conteudo" and "topicos" in slide:
        topicos = slide["topicos"]
        if not isinstance(topicos, list) or not all(_e_texto(t) for t in topicos):
            erros.append(
                f"Slide {n} (conteudo): `topicos` precisa ser uma lista de textos, "
                f"um por linha começando com `- `. {DICA_ASPAS}"
            )
    if tipo == "diagrama" and "itens" in slide:
        erros += _estrutura_dos_itens(n, slide["itens"])
    return erros


def _estrutura_dos_itens(n: int, itens: object) -> list[str]:
    if not isinstance(itens, list) or not all(isinstance(item, dict) for item in itens):
        return [
            f"Slide {n} (diagrama): `itens` precisa ser uma lista em que cada item começa "
            "com `- titulo:` e tem a linha `texto:` logo abaixo."
        ]
    erros = []
    for i, item in enumerate(itens, start=1):
        for campo in sorted(set(item) - CAMPOS_DO_ITEM, key=str):
            erros.append(
                f"Slide {n} (diagrama): o item {i} tem o campo `{campo}`, que não existe. "
                "Campos aceitos: texto, titulo."
            )
        for campo in sorted(CAMPOS_DO_ITEM):
            if campo not in item:
                erros.append(f"Slide {n} (diagrama): falta o campo `{campo}` no item {i}.")
            elif not _e_texto(item[campo]):
                erros.append(
                    f"Slide {n} (diagrama): o `{campo}` do item {i} precisa ser um texto "
                    f"não vazio. {DICA_ASPAS}"
                )
    return erros


# Onda 2: regras independentes entre si. Cada uma roda sobre a parte do deck bem formada,
# para mostrar o máximo de erros de uma vez.


def _tamanho(n: int, tipo: str, campo: str, texto: str, limite: int) -> list[str]:
    tamanho = len(_normalizar(texto))
    if tamanho <= limite:
        return []
    return [
        f"Slide {n} ({tipo}): o {campo} tem {tamanho} caracteres; o limite é {limite}. "
        f'Encurte: "{_normalizar(texto)}"'
    ]


def _limites_de_texto(slides: list[tuple[int, dict]]) -> list[str]:
    """Recebe só os slides bem formados, com o número de cada um no deck."""
    erros = []
    for n, slide in slides:
        tipo = slide["tipo"]
        if tipo in LIMITE_TITULO:
            erros += _tamanho(n, tipo, "título", slide["titulo"], LIMITE_TITULO[tipo])
        if tipo == "diagrama":
            erros += _limites_do_diagrama(n, slide["itens"])
        if tipo != "conteudo":
            continue

        topicos, destaque = slide["topicos"], slide.get("destaque")
        maximo = MAX_TOPICOS_COM_DESTAQUE if destaque else MAX_TOPICOS
        if not MIN_TOPICOS <= len(topicos) <= maximo:
            regra = f"de {MIN_TOPICOS} a {maximo}" + (" quando há destaque" if destaque else "")
            erros.append(
                f"Slide {n} (conteudo): tem {len(topicos)} tópicos; use {regra}. "
                "Se precisar de mais, divida em dois slides."
            )
        for i, topico in enumerate(topicos, start=1):
            erros += _tamanho(n, tipo, f"tópico {i}", topico, LIMITE_TOPICO)
        if destaque:
            erros += _tamanho(n, tipo, "destaque", destaque, LIMITE_DESTAQUE)
    return erros


def _limites_do_diagrama(n: int, itens: list[dict]) -> list[str]:
    erros = []
    if not MIN_ITENS <= len(itens) <= MAX_ITENS:
        dica = (
            "Com menos itens, prefira um slide de `conteudo`."
            if len(itens) < MIN_ITENS
            else "Se precisar de mais, divida em dois slides."
        )
        erros.append(
            f"Slide {n} (diagrama): tem {len(itens)} itens; use de {MIN_ITENS} a {MAX_ITENS}. "
            + dica
        )
    for i, item in enumerate(itens, start=1):
        erros += _tamanho(n, "diagrama", f"título do item {i}", item["titulo"], LIMITE_TITULO_ITEM)
        erros += _tamanho(n, "diagrama", f"texto do item {i}", item["texto"], LIMITE_TEXTO_ITEM)
    return erros


def _ordem(slides: list[dict]) -> list[str]:
    tipos = [s["tipo"] for s in slides]
    erros = []
    if tipos[0] != "capa":
        erros.append("O primeiro slide precisa ser a `capa`.")
    if tipos[-1] != "encerramento":
        erros.append("O último slide precisa ser o `encerramento`.")
    for tipo, lugar in (("capa", "no início"), ("encerramento", "no fim")):
        if tipos.count(tipo) > 1:
            erros.append(f"O deck tem {tipos.count(tipo)} slides `{tipo}`; use só um, {lugar}.")
    return erros


def _quantidade(slides: list[dict]) -> list[str]:
    if len(slides) <= MAX_SLIDES:
        return []
    return [
        f"O deck tem {len(slides)} slides; o máximo é {MAX_SLIDES}. "
        "Divida a aula em duas apresentações."
    ]


# Onda 3: avisos de conteúdo. Não bloqueiam a geração.


def _avisos(slides: list[dict]) -> list[str]:
    avisos = []
    tipos = [s["tipo"] for s in slides]

    conteudos = [s for s in slides if s["tipo"] == "conteudo"]
    com_destaque = sum(1 for s in conteudos if s.get("destaque"))
    if com_destaque > 1 and com_destaque * 3 > len(conteudos):
        avisos.append(
            f"{com_destaque} de {len(conteudos)} slides de conteúdo têm destaque. "
            "Guarde o destaque para no máximo 1 a cada 3 slides."
        )

    primeiro = next((i for i, tipo in enumerate(tipos) if tipo in SECOES), None)
    if primeiro is not None and ("divisoria" not in tipos or primeiro < tipos.index("divisoria")):
        avisos.append(
            f"Slide {primeiro + 1}: há conteúdo antes da primeira divisória. "
            "Organize a aula em seções, cada uma começando com uma `divisoria`."
        )

    vistos: dict[str, int] = {}
    for n, slide in enumerate(slides, start=1):
        tipo = slide["tipo"]
        if tipo == "divisoria" and (n == len(slides) or tipos[n] not in SECOES):
            avisos.append(f"Slide {n}: a seção não tem nenhum slide de conteúdo logo depois.")

        if tipo == "conteudo":
            if _normalizar(slide["titulo"]).isupper():
                avisos.append(
                    f"Slide {n}: o título está em CAIXA ALTA. Nos slides de conteúdo, "
                    "use capitalização normal; a caixa alta é só da capa e da divisória."
                )
            destaque = slide.get("destaque")
            if destaque and not destaque.rstrip().endswith("."):
                avisos.append(
                    f"Slide {n}: termine o destaque com ponto final (no modelo, ele sai em verde)."
                )

        if tipo != "encerramento":
            chave = _normalizar(slide["titulo"]).casefold()
            if chave in vistos:
                avisos.append(f"Slide {n}: repete o título do slide {vistos[chave]}.")
            else:
                vistos[chave] = n
    return avisos


def validar_deck(dados: object) -> tuple[list[str], list[str]]:
    """Devolve (erros, avisos). Com qualquer erro, o deck não deve ser gerado."""
    erros = _estrutura_do_deck(dados)
    slides = dados.get("slides") if isinstance(dados, dict) else None
    if not isinstance(slides, list) or not slides:
        return erros, []

    bem_formados = []
    for n, slide in enumerate(slides, start=1):
        erros_do_slide = _estrutura_do_slide(n, slide)
        erros += erros_do_slide
        if not erros_do_slide:
            bem_formados.append((n, slide))

    erros += _limites_de_texto(bem_formados)
    if all(_tipo_valido(s) for s in slides):
        erros += _ordem(slides) + _quantidade(slides)
    return erros, ([] if erros else _avisos(slides))


def validar_arquivo(caminho: str | Path) -> Resultado:
    resultado = Resultado(Path(caminho))
    try:
        dados = yaml.safe_load(resultado.arquivo.read_text(encoding="utf-8"))
    except UnicodeDecodeError:
        resultado.erros.append("O arquivo não está em UTF-8. Salve-o de novo nessa codificação.")
        return resultado
    except yaml.YAMLError as erro:
        marca = getattr(erro, "problem_mark", None)
        onde = f" perto da linha {marca.line + 1}" if marca else ""
        resultado.erros.append(
            f"O YAML não pôde ser lido{onde}. Confira a indentação e coloque entre aspas "
            "os textos que têm `:` ou começam com caracteres especiais."
        )
        return resultado

    resultado.erros, resultado.avisos = validar_deck(dados)
    if resultado.ok:
        resultado.deck = dados
    return resultado


def _arquivos(caminhos: list[str]) -> tuple[list[Path], list[Path]]:
    arquivos, faltando = [], []
    for caminho in map(Path, caminhos):
        if caminho.is_dir():
            arquivos += sorted(p for p in caminho.iterdir() if p.suffix in (".yaml", ".yml"))
        elif caminho.is_file():
            arquivos.append(caminho)
        else:
            faltando.append(caminho)
    return arquivos, faltando


def _relatar(resultado: Resultado) -> None:
    if resultado.ok:
        print(f"{resultado.arquivo}: OK, {len(resultado.deck['slides'])} slides.")
    else:
        total = len(resultado.erros)
        erros = "1 erro" if total == 1 else f"{total} erros"
        print(f"{resultado.arquivo}: {erros}. Corrija antes de gerar.")
    for erro in resultado.erros:
        print(f"  - erro: {erro}")
    for aviso in resultado.avisos:
        print(f"  - aviso: {aviso}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m senai_slides.validador",
        description="Confere decks de slides em YAML e, com --gerar, gera os slides.",
    )
    parser.add_argument("caminhos", nargs="+", help="arquivos .yaml ou pastas com eles")
    parser.add_argument("--gerar", action="store_true", help="gera PNGs e PDF dos decks sem erro")
    parser.add_argument("--saida", default="outputs", help="pasta de saída (padrão: outputs)")
    args = parser.parse_args(argv)
    # O hook do Kiro lê a saída por pipe; sem isso, o Windows troca os acentos por "?".
    sys.stdout.reconfigure(encoding="utf-8")

    arquivos, faltando = _arquivos(args.caminhos)
    for caminho in faltando:
        print(f"{caminho}: arquivo ou pasta não encontrado.")
    if not arquivos and not faltando:
        print("Nenhum arquivo .yaml encontrado.")
        return 1

    falhou = bool(faltando)
    for arquivo in arquivos:
        resultado = validar_arquivo(arquivo)
        _relatar(resultado)
        if not resultado.ok:
            falhou = True
        elif args.gerar:
            try:
                gerar(resultado.deck, args.saida)
            except (TextoLongoDemais, ValueError) as erro:
                print(f"  - erro ao gerar: {erro}")
                falhou = True
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
