"""Confere decks de slides em YAML e, com --gerar, monta os que passaram.

Uso:
    python -m senai_slides.validador slides/minha_aula.yaml
    python -m senai_slides.validador slides/ --gerar
    python -m senai_slides.validador slides/ --gerar --aceitar-custo
    python -m senai_slides.validador slides/ --gerar --sem-imagens

Para cada deck sem erro, mostra quantas imagens faltam e quanto custam. Com --gerar, as fotos
reais (grátis) sempre entram; as imagens criadas por IA, que são cobradas, só com --aceitar-custo.

Os números de slide nas mensagens contam só os slides de conteúdo (a lista `slides`); capa,
agenda, divisórias e encerramento são montados à parte.
"""

import argparse
import difflib
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from senai_slides.icones import ICONES
from senai_slides.imagens import MODOS as MODOS_DE_IMAGEM
from senai_slides.imagens import Estimativa, estimativa

CAMPOS_DO_DECK = {
    "nome",
    "titulo",
    "subtitulo",
    "uc",
    "modo",
    "tags",
    "logo_curso",
    "imagens",
    "imagem",
    "notas_capa",
    "secoes",
    "slides",
}
MODOS = ("resumido", "aprofundado")
CAMPOS_COMUNS = {"layout", "secao", "titulo", "subtitulo", "notas"}

# Por layout: campos a mais, quantidade de itens e campos obrigatórios de cada item.
LAYOUTS = {
    "topicos": ({"itens", "destaque"}, (2, 6), {"icone", "titulo"}),
    "cartoes": ({"itens", "destaque"}, (2, 4), {"icone", "titulo", "texto"}),
    "numeros": ({"itens", "destaque"}, (2, 4), {"icone", "valor", "titulo"}),
    "processo": ({"itens", "destaque"}, (3, 6), {"icone", "titulo", "texto"}),
    "linha_do_tempo": ({"itens"}, (3, 5), {"icone", "valor", "titulo", "texto"}),
    "comparacao": ({"colunas", "destaque"}, None, None),
    "grafico": ({"grafico", "itens"}, (0, 3), {"icone", "titulo", "texto"}),
    "destaque": ({"destaque", "itens"}, (0, 1), {"titulo"}),
    "tabela": ({"tabela"}, None, None),
    "ilustracao": ({"itens", "destaque", "imagem"}, (2, 5), {"icone", "titulo"}),
    "diagrama": ({"itens"}, (3, 6), {"icone", "titulo", "texto"}),
}
OBRIGATORIOS = {
    "comparacao": {"colunas"},
    "grafico": {"grafico"},
    "destaque": {"destaque"},
    "tabela": {"tabela"},
    "ilustracao": {"imagem"},
}
CAMPOS_DO_ITEM = {"icone", "titulo", "texto", "valor"}
TIPOS_DE_GRAFICO = ("barras", "barras_horizontais", "linhas", "pizza")

MIN_SLIDES, MAX_SLIDES = 1, 20
MAX_TAGS, MAX_SECOES = 5, 6
LIMITE = {
    "titulo_capa": 60,
    "subtitulo_capa": 80,
    "uc": 60,
    "tag": 20,
    "secao": 40,
    "descricao_secao": 80,
    "titulo": 50,
    "titulo_diagrama": 30,
    "subtitulo": 80,
    "titulo_item": 40,
    "frase_item": 90,
    "titulo_item_diagrama": 20,
    "texto_item_diagrama": 70,
    "valor": 12,
    "rotulo_linha_do_tempo": 20,
    "destaque": 120,
    "titulo_coluna": 30,
    "celula": 80,
    "cabecalho": 30,
    "categoria": 20,
    "fonte": 80,
    "eixo_y": 30,
    "imagem": 300,
    "busca_foto": 100,
    "notas": 800,
}
# O modo muda quanto texto cabe nos itens: frases curtas ou explicações.
LIMITE_TEXTO_ITEM = {"resumido": 70, "aprofundado": 170}
LIMITE_ITEM_COLUNA = {"resumido": 70, "aprofundado": 120}

DICA_ASPAS = "Se o texto for um número, sim/não ou tiver `:`, coloque-o entre aspas."
SEM_IMAGENS = "O deck está com `imagens: false`, então não leva imagens."


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


def _e_numero(valor: object) -> bool:
    return isinstance(valor, (int, float)) and not isinstance(valor, bool)


def _normalizar(texto: str) -> str:
    return " ".join(texto.split())


def _tamanho(onde: str, campo: str, texto: str, limite: int) -> list[str]:
    tamanho = len(_normalizar(texto))
    if tamanho <= limite:
        return []
    return [
        f"{onde}: {campo} tem {tamanho} caracteres; o limite é {limite}. "
        f'Encurte: "{_normalizar(texto)}"'
    ]


def _texto_opcional(onde: str, campo: str, valor: object, limite: int) -> list[str]:
    if valor is None:
        return []
    if not _e_texto(valor):
        return [f"{onde}: `{campo}` precisa ser um texto. {DICA_ASPAS}"]
    return _tamanho(onde, f"`{campo}`", valor, limite)


def _texto_obrigatorio(onde: str, campo: str, valor: object, limite: int) -> list[str]:
    if valor is None:
        return [f"{onde}: falta o campo `{campo}`."]
    return _texto_opcional(onde, campo, valor, limite)


def _imagem(onde: str, valor: object) -> list[str]:
    """Texto sozinho é uma imagem criada por IA; `foto:` busca uma foto real."""
    if valor is None or isinstance(valor, str):
        return _texto_opcional(onde, "imagem", valor, LIMITE["imagem"])
    if not isinstance(valor, dict) or len(valor) != 1 or next(iter(valor)) not in MODOS_DE_IMAGEM:
        return [
            f"{onde}: `imagem` precisa ter `foto:` (termos para buscar uma foto real) ou "
            "`gerar:` (descrição da cena para a IA criar), em inglês."
        ]
    modo, texto = next(iter(valor.items()))
    limite = LIMITE["busca_foto" if modo == "foto" else "imagem"]
    return _texto_obrigatorio(onde, f"imagem.{modo}", texto, limite)


# O deck (capa, seções e a lista de slides)


def _estrutura_do_deck(dados: dict) -> list[str]:
    erros = []
    for campo in sorted(set(dados) - CAMPOS_DO_DECK, key=str):
        erros.append(
            f"Campo `{campo}` não existe no deck. "
            f"Campos aceitos: {', '.join(sorted(CAMPOS_DO_DECK))}."
        )
    capa = "Capa"
    erros += _texto_obrigatorio(capa, "titulo", dados.get("titulo"), LIMITE["titulo_capa"])
    erros += _texto_opcional(capa, "subtitulo", dados.get("subtitulo"), LIMITE["subtitulo_capa"])
    erros += _texto_opcional(capa, "uc", dados.get("uc"), LIMITE["uc"])
    erros += _imagem(capa, dados.get("imagem"))
    erros += _texto_opcional(capa, "notas_capa", dados.get("notas_capa"), LIMITE["notas"])
    erros += _texto_opcional("Deck", "nome", dados.get("nome"), 60)
    if dados.get("modo") is not None and dados["modo"] not in MODOS:
        erros.append(f"`modo` precisa ser `resumido` ou `aprofundado`, e não `{dados['modo']}`.")
    if dados.get("logo_curso") is not None and not isinstance(dados["logo_curso"], bool):
        erros.append("`logo_curso` precisa ser `true` ou `false`.")
    if dados.get("imagens") is not None and not isinstance(dados["imagens"], bool):
        erros.append("`imagens` precisa ser `true` ou `false`.")
    if dados.get("imagens") is False and dados.get("imagem") is not None:
        erros.append(SEM_IMAGENS + " Tire a `imagem` da capa ou mude para `imagens: true`.")

    tags = dados.get("tags")
    if tags is not None:
        if not isinstance(tags, list) or not all(_e_texto(tag) for tag in tags):
            erros.append(
                f"`tags` precisa ser uma lista de textos, ex.: [NR-10, segurança]. {DICA_ASPAS}"
            )
        else:
            if len(tags) > MAX_TAGS:
                erros.append(f"Use no máximo {MAX_TAGS} `tags`; o deck tem {len(tags)}.")
            for tag in tags:
                erros += _tamanho("Capa", f'a tag "{tag}"', tag, LIMITE["tag"])

    secoes = dados.get("secoes")
    if secoes is not None:
        if not isinstance(secoes, list) or not all(isinstance(s, dict) for s in secoes):
            erros.append(
                "`secoes` precisa ser uma lista em que cada seção tem `nome` e `descricao`."
            )
        else:
            if len(secoes) > MAX_SECOES:
                erros.append(f"Use no máximo {MAX_SECOES} seções; o deck tem {len(secoes)}.")
            for i, secao in enumerate(secoes, start=1):
                onde = f"Seção {i}"
                for campo in sorted(set(secao) - {"nome", "descricao"}, key=str):
                    erros.append(f"{onde}: o campo `{campo}` não existe. Use `nome` e `descricao`.")
                erros += _texto_obrigatorio(onde, "nome", secao.get("nome"), LIMITE["secao"])
                erros += _texto_opcional(
                    onde, "descricao", secao.get("descricao"), LIMITE["descricao_secao"]
                )

    slides = dados.get("slides")
    if not isinstance(slides, list) or not slides:
        erros.append("`slides` precisa ser uma lista com pelo menos um slide de conteúdo.")
    elif len(slides) > MAX_SLIDES:
        erros.append(
            f"O deck tem {len(slides)} slides de conteúdo; o máximo é {MAX_SLIDES}. "
            "Divida a aula em duas apresentações."
        )
    return erros


# Cada slide de conteúdo


def _icone(onde: str, nome: object) -> list[str]:
    if nome in ICONES:
        return []
    parecidos = difflib.get_close_matches(str(nome), ICONES, n=3)
    dica = f" Parecidos: {', '.join(parecidos)}." if parecidos else ""
    return [f"{onde}: o ícone `{nome}` não está na lista de ícones permitidos.{dica}"]


def _itens(onde: str, layout: str, itens: object, modo: str) -> list[str]:
    _, quantidade, obrigatorios = LAYOUTS[layout]
    if itens is None:
        itens = []
    if not isinstance(itens, list) or not all(isinstance(i, dict) for i in itens):
        return [
            f"{onde}: `itens` precisa ser uma lista; cada item começa com `- icone:` "
            "ou `- titulo:`."
        ]
    minimo, maximo = quantidade
    erros = []
    if not minimo <= len(itens) <= maximo:
        regra = f"de {minimo} a {maximo}" if minimo != maximo else f"{minimo}"
        erros.append(f"{onde}: tem {len(itens)} itens; o layout `{layout}` usa {regra}.")

    diagrama = layout == "diagrama"
    limite_titulo = LIMITE["titulo_item_diagrama" if diagrama else "titulo_item"]
    limite_texto = LIMITE["texto_item_diagrama"] if diagrama else LIMITE_TEXTO_ITEM[modo]
    limite_valor = LIMITE["rotulo_linha_do_tempo" if layout == "linha_do_tempo" else "valor"]
    for n, item in enumerate(itens, start=1):
        local = f"{onde}, item {n}"
        for campo in sorted(set(item) - CAMPOS_DO_ITEM, key=str):
            erros.append(
                f"{local}: o campo `{campo}` não existe. "
                "Campos do item: icone, titulo, texto, valor."
            )
        for campo in sorted(obrigatorios - set(item)):
            erros.append(f"{local}: falta o campo `{campo}`.")
        if "icone" in item:
            erros += _icone(local, item["icone"])
        # Sem `texto`, o título do item vira uma frase (como um tópico de lista).
        so_titulo = layout in ("topicos", "ilustracao") and not item.get("texto")
        limite = LIMITE["frase_item"] if so_titulo else limite_titulo
        erros += _texto_opcional(local, "titulo", item.get("titulo"), limite)
        erros += _texto_opcional(local, "texto", item.get("texto"), limite_texto)
        valor = item.get("valor")
        if _e_numero(valor):
            valor = str(valor)
        erros += _texto_opcional(local, "valor", valor, limite_valor)
    return erros


def _colunas(onde: str, colunas: object, modo: str) -> list[str]:
    if (
        not isinstance(colunas, list)
        or len(colunas) != 2
        or not all(isinstance(c, dict) for c in colunas)
    ):
        return [
            f"{onde}: `colunas` precisa ser uma lista com exatamente 2 colunas, "
            "cada uma com `titulo` e `itens`."
        ]
    erros = []
    for n, coluna in enumerate(colunas, start=1):
        local = f"{onde}, coluna {n}"
        erros += _texto_obrigatorio(local, "titulo", coluna.get("titulo"), LIMITE["titulo_coluna"])
        itens = coluna.get("itens")
        if not isinstance(itens, list) or not all(_e_texto(i) for i in itens):
            erros.append(f"{local}: `itens` precisa ser uma lista de textos. {DICA_ASPAS}")
            continue
        if not 3 <= len(itens) <= 6:
            erros.append(f"{local}: tem {len(itens)} itens; use de 3 a 6.")
        for i, texto in enumerate(itens, start=1):
            erros += _tamanho(local, f"o item {i}", texto, LIMITE_ITEM_COLUNA[modo])
    return erros


def _grafico(onde: str, g: object) -> list[str]:
    if not isinstance(g, dict):
        return [f"{onde}: `grafico` precisa ter `tipo`, `categorias`, `series` e `fonte`."]
    erros = []
    if g.get("tipo") not in TIPOS_DE_GRAFICO:
        erros.append(
            f"{onde}: o `tipo` do gráfico precisa ser um destes: {', '.join(TIPOS_DE_GRAFICO)}."
        )
    categorias = g.get("categorias")
    if not isinstance(categorias, list) or not 2 <= len(categorias) <= 12:
        erros.append(f"{onde}: o gráfico precisa de `categorias`, uma lista de 2 a 12 rótulos.")
        categorias = None
    else:
        for c in categorias:
            erros += _tamanho(onde, f'a categoria "{c}"', str(c), LIMITE["categoria"])
    series = g.get("series")
    maximo = 1 if g.get("tipo") == "pizza" else 3
    if not isinstance(series, list) or not 1 <= len(series) <= maximo:
        regra = "exatamente 1 série" if maximo == 1 else "de 1 a 3 séries"
        erros.append(f"{onde}: o gráfico precisa de {regra} em `series`.")
    else:
        for n, serie in enumerate(series, start=1):
            local = f"{onde}, série {n}"
            if not isinstance(serie, dict) or not _e_texto(serie.get("nome")):
                erros.append(f"{local}: cada série precisa de `nome` e `valores`.")
                continue
            valores = serie.get("valores")
            if not isinstance(valores, list) or not all(_e_numero(v) for v in valores):
                erros.append(f"{local}: `valores` precisa ser uma lista de números, sem aspas.")
            elif categorias is not None and len(valores) != len(categorias):
                erros.append(
                    f"{local}: tem {len(valores)} valores para {len(categorias)} categorias."
                )
    erros += _texto_obrigatorio(onde, "fonte", g.get("fonte"), LIMITE["fonte"])
    erros += _texto_opcional(onde, "eixo_y", g.get("eixo_y"), LIMITE["eixo_y"])
    return erros


def _celula(valor: object) -> str | None:
    if _e_numero(valor):
        return str(valor)
    return valor if isinstance(valor, str) else None


def _tabela(onde: str, tabela: object) -> list[str]:
    if not isinstance(tabela, dict):
        return [f"{onde}: `tabela` precisa ter `cabecalho` e `linhas`."]
    cabecalho = tabela.get("cabecalho")
    if not isinstance(cabecalho, list) or not 2 <= len(cabecalho) <= 5:
        return [f"{onde}: o `cabecalho` da tabela precisa ter de 2 a 5 colunas."]
    erros = []
    for titulo in cabecalho:
        if _celula(titulo) is None:
            erros.append(f"{onde}: cada título do `cabecalho` precisa ser um texto.")
        else:
            erros += _tamanho(onde, "um título do cabeçalho", _celula(titulo), LIMITE["cabecalho"])
    linhas = tabela.get("linhas")
    if not isinstance(linhas, list) or not 2 <= len(linhas) <= 8:
        return erros + [f"{onde}: a tabela precisa de 2 a 8 `linhas`."]
    for n, linha in enumerate(linhas, start=1):
        if not isinstance(linha, list) or len(linha) != len(cabecalho):
            erros.append(
                f"{onde}: a linha {n} da tabela precisa ter {len(cabecalho)} células, "
                "como o cabeçalho."
            )
            continue
        for celula in linha:
            texto = _celula(celula)
            if texto is None:
                erros.append(f"{onde}: a linha {n} tem uma célula que não é texto nem número.")
            else:
                erros += _tamanho(onde, f"uma célula da linha {n}", texto, LIMITE["celula"])
    return erros


def _slide(n: int, slide: object, modo: str, com_imagens: bool) -> list[str]:
    layout = slide.get("layout") if isinstance(slide, dict) else None
    if layout not in LAYOUTS:
        return [f"Slide {n}: `layout` precisa ser um destes: {', '.join(LAYOUTS)}."]
    onde = f"Slide {n} ({layout})"
    if layout == "ilustracao" and not com_imagens:
        return [f"{onde}: {SEM_IMAGENS} Troque o layout por `topicos` ou `cartoes`."]
    extras, quantidade, _ = LAYOUTS[layout]
    aceitos = CAMPOS_COMUNS | extras
    if layout == "diagrama":
        aceitos = aceitos - {"subtitulo"}  # o título vai no círculo central
    erros = []
    for campo in sorted(set(slide) - aceitos, key=str):
        erros.append(
            f"{onde}: o layout `{layout}` não usa o campo `{campo}`. "
            f"Campos aceitos: {', '.join(sorted(aceitos))}."
        )
    for campo in sorted(OBRIGATORIOS.get(layout, set()) - set(slide)):
        erros.append(f"{onde}: falta o campo `{campo}`.")

    limite_titulo = LIMITE["titulo_diagrama" if layout == "diagrama" else "titulo"]
    erros += _texto_obrigatorio(onde, "titulo", slide.get("titulo"), limite_titulo)
    erros += _texto_opcional(onde, "subtitulo", slide.get("subtitulo"), LIMITE["subtitulo"])
    erros += _texto_opcional(onde, "notas", slide.get("notas"), LIMITE["notas"])
    erros += _texto_opcional(onde, "secao", slide.get("secao"), LIMITE["secao"])
    if "destaque" in aceitos:
        erros += _texto_opcional(onde, "destaque", slide.get("destaque"), LIMITE["destaque"])
    if "imagem" in aceitos:
        erros += _imagem(onde, slide.get("imagem"))
    if quantidade is not None:
        erros += _itens(onde, layout, slide.get("itens"), modo)
    if layout == "comparacao" and "colunas" in slide:
        erros += _colunas(onde, slide["colunas"], modo)
    if layout == "grafico" and "grafico" in slide:
        erros += _grafico(onde, slide["grafico"])
    if layout == "tabela" and "tabela" in slide:
        erros += _tabela(onde, slide["tabela"])
    return erros


def _secoes_dos_slides(dados: dict, slides: list[dict]) -> list[str]:
    nomes = [s.get("nome") for s in dados.get("secoes") or [] if isinstance(s, dict)]
    usadas = [s.get("secao") or "" for s in slides]
    if not nomes:
        com_secao = [n for n, secao in enumerate(usadas, start=1) if secao]
        if com_secao:
            return [
                f"Slide {com_secao[0]}: usa `secao`, mas o deck não tem `secoes`. "
                "Liste as seções no topo do deck ou tire o campo `secao`."
            ]
        return []
    erros = []
    for n, secao in enumerate(usadas, start=1):
        if secao not in nomes:
            lista = ", ".join(f'"{nome}"' for nome in nomes)
            erros.append(f"Slide {n}: `secao` precisa ser o nome de uma das seções: {lista}.")
    vistas = []
    for n, secao in enumerate(usadas, start=1):
        if vistas and secao != vistas[-1] and secao in vistas:
            erros.append(
                f'Slide {n}: os slides da seção "{secao}" precisam ficar juntos, '
                "um depois do outro."
            )
        if not vistas or secao != vistas[-1]:
            vistas.append(secao)
    for nome in nomes:
        if nome not in usadas:
            erros.append(
                f'A seção "{nome}" não tem nenhum slide. Use-a em algum slide ou remova-a.'
            )
    return erros


# Avisos: boas práticas, não impedem a geração


def _avisos(dados: dict) -> list[str]:
    slides = dados["slides"]
    layouts = [s["layout"] for s in slides]
    avisos = []
    for n in range(1, len(layouts)):
        if layouts[n] == layouts[n - 1]:
            avisos.append(
                f"Slides {n} e {n + 1}: os dois usam o layout `{layouts[n]}`. Varie os layouts "
                "entre slides seguidos."
            )
    if len(slides) >= 5 and len(set(layouts)) < 4:
        avisos.append(
            f"O deck usa só {len(set(layouts))} layouts diferentes; com 5 slides ou mais, use "
            "pelo menos 4."
        )
    com_imagens = dados.get("imagens") is not False
    if com_imagens and not dados.get("imagem"):
        avisos.append(
            "A capa está sem `imagem`. Use `foto:` ou `gerar:` com uma imagem do tema da aula, "
            "ou `imagens: false` se o professor não quiser imagens."
        )
    if com_imagens and len(slides) >= 3 and "ilustracao" not in layouts:
        avisos.append(
            "Nenhum slide usa o layout `ilustracao`. Use-o em pelo menos um slide para a aula ter "
            "imagens sobre o conteúdo."
        )
    vistos: dict[str, int] = {}
    for n, slide in enumerate(slides, start=1):
        chave = _normalizar(slide["titulo"]).casefold()
        if chave in vistos:
            avisos.append(f"Slide {n}: repete o título do slide {vistos[chave]}.")
        vistos.setdefault(chave, n)
        grafico = slide.get("grafico")
        if isinstance(grafico, dict) and "ilustrativ" in str(grafico.get("fonte", "")).lower():
            avisos.append(
                f"Slide {n}: o gráfico usa dados ilustrativos. Troque por dados reais antes de "
                "apresentar."
            )
        if dados.get("modo") == "aprofundado" and not slide.get("notas"):
            avisos.append(f"Slide {n}: no modo aprofundado, escreva as `notas` do apresentador.")
    return avisos


def validar_deck(dados: object) -> tuple[list[str], list[str]]:
    """Devolve (erros, avisos). Com qualquer erro, o deck não deve ser gerado."""
    if not isinstance(dados, dict):
        return ["O arquivo precisa ter os campos `titulo` e `slides` no nível principal."], []
    slides = dados.get("slides")
    if isinstance(slides, list) and any(isinstance(s, dict) and "tipo" in s for s in slides):
        return [
            "Este deck está no formato antigo, com `tipo:` em cada slide. Agora a capa vem de "
            "`titulo` no topo do deck e cada slide de conteúdo tem um `layout`; veja o "
            "formato em agente/AGENTE_SLIDES_SENAI.md."
        ], []
    erros = _estrutura_do_deck(dados)
    if not isinstance(slides, list) or not slides:
        return erros, []
    modo = dados.get("modo") if dados.get("modo") in MODOS else "resumido"
    com_imagens = dados.get("imagens") is not False
    for n, slide in enumerate(slides, start=1):
        erros += _slide(n, slide, modo, com_imagens)
    if all(isinstance(s, dict) for s in slides):
        erros += _secoes_dos_slides(dados, slides)
    return erros, ([] if erros else _avisos(dados))


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


def _relatar(resultado: Resultado, conta: Estimativa | None) -> None:
    if resultado.ok:
        print(f"{resultado.arquivo}: OK, {len(resultado.deck['slides'])} slides de conteúdo.")
        sem = resultado.deck.get("imagens") is False
        print(f"  Imagens: {'nenhuma (`imagens: false`)' if sem else conta}.")
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
        description="Confere decks de slides em YAML e, com --gerar, monta o .pptx.",
    )
    parser.add_argument("caminhos", nargs="+", help="arquivos .yaml ou pastas com eles")
    parser.add_argument(
        "--gerar", action="store_true", help="monta .pptx, prévias PNG e PDF dos decks sem erro"
    )
    parser.add_argument("--saida", default="outputs", help="pasta de saída (padrão: outputs)")
    parser.add_argument(
        "--aceitar-custo",
        action="store_true",
        help="cria na Amazon Bedrock as imagens por IA (cerca de US$ 0,07 cada); sem esta opção, "
        "só entram as fotos reais e o que já está no cache",
    )
    parser.add_argument(
        "--sem-imagens",
        action="store_true",
        help="gera sem imagens, nem as do cache: não busca fotos nem cria imagens",
    )
    parser.add_argument(
        "--sem-instalar-fontes",
        action="store_true",
        help="não instala a Open Sans no Windows do usuário",
    )
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
    resultados = [validar_arquivo(arquivo) for arquivo in arquivos]
    contas = {}
    for resultado in resultados:
        if resultado.ok:
            contas[resultado.arquivo] = estimativa(resultado.deck, args.saida)
        _relatar(resultado, contas.get(resultado.arquivo))
        falhou |= not resultado.ok
    a_pagar = Estimativa(0, sum(c.geradas for c in contas.values()), 0)
    if args.gerar and a_pagar.geradas and not (args.aceitar_custo or args.sem_imagens):
        print(
            f"Custo não autorizado: {a_pagar} ficam de fora, e esses slides saem sem imagem. "
            "Confirme o custo com o professor e rode de novo com --aceitar-custo para criá-las."
        )
    if args.gerar and any(r.ok for r in resultados):
        # Importado só aqui: validar não precisa carregar o PowerPoint nem o matplotlib.
        from senai_slides.gerador import gerar
        from senai_slides.tema import instalar_fontes_usuario

        if not args.sem_instalar_fontes and instalar_fontes_usuario():
            print("Open Sans instalada para o usuário, para o PowerPoint mostrar a fonte certa.")
        for resultado in (r for r in resultados if r.ok):
            try:
                gerar(
                    resultado.deck,
                    args.saida,
                    imagens=not args.sem_imagens,
                    pagar=args.aceitar_custo,
                )
            # RuntimeError: a Bedrock não gerou alguma imagem (credencial, filtro, rede).
            except (ValueError, RuntimeError) as erro:
                print(f"{resultado.arquivo}: erro ao gerar: {erro}")
                falhou = True
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
