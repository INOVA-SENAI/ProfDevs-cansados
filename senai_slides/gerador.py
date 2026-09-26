from pathlib import Path

from senai_slides import previa
from senai_slides import tema as t
from senai_slides.imagens import ilustracoes, pasta_da_aula, pedidos_do_deck
from senai_slides.layouts import slide_conteudo

MIN_SLIDES_PARA_AGENDA = 4
CAMPOS_DO_SLIDE = {
    "secao": "",
    "subtitulo": "",
    "itens": [],
    "colunas": [],
    "grafico": None,
    "tabela": None,
    "destaque": "",
    "notas": "",
    "imagem": "",
}
CAMPOS_DO_ITEM = {"icone": "check_circle", "titulo": "", "texto": "", "valor": ""}


def _normalizar(slide: dict) -> dict:
    """Completa os campos opcionais, para os layouts não precisarem testar cada um. Números
    escritos sem aspas no YAML (ex.: `valor: 40`) viram texto."""
    s = {**CAMPOS_DO_SLIDE, **{k: v for k, v in slide.items() if v is not None}}
    s["itens"] = [
        {**CAMPOS_DO_ITEM, **{k: str(v) for k, v in i.items() if v is not None}} for i in s["itens"]
    ]
    if s["tabela"]:
        s["tabela"] = {
            "cabecalho": [str(c) for c in s["tabela"]["cabecalho"]],
            "linhas": [[str(c) for c in linha] for linha in s["tabela"]["linhas"]],
        }
    return s


def roteiro(deck: dict) -> list[tuple[str, object]]:
    """Capa, agenda, uma divisória por seção, os slides de conteúdo e o encerramento."""
    slides = [_normalizar(s) for s in deck["slides"]]
    secoes = {s["nome"]: s.get("descricao") or "" for s in deck.get("secoes") or []}
    itens = [("capa", None)]
    if len(slides) >= MIN_SLIDES_PARA_AGENDA:
        itens.append(("agenda", None))
    atual = None
    for slide in slides:
        if secoes and slide["secao"] != atual:
            atual = slide["secao"]
            itens.append(("divisoria", (atual, secoes[atual])))
        itens.append(("conteudo", slide))
    itens.append(("encerramento", None))
    return itens


def gerar(
    deck: dict, pasta: str | Path = "outputs", imagens: bool = True, pagar: bool = True
) -> Path:
    """Monta a apresentação de um deck já aprovado pelo validador.

    Salva em `<pasta>/<nome>/`: o .pptx editável, uma prévia PNG por slide e um PDF. Com
    `imagens`, a `imagem` da capa e a de cada slide `ilustracao` viram uma foto real do Wikimedia
    Commons (`foto`) ou uma imagem criada pela Amazon Bedrock (`gerar`), em cache em `imagens/`;
    sem `imagens`, nada é buscado nem cobrado e esses slides saem sem figura. Sem `pagar`, só
    entram as fotos (grátis) e o que já está no cache.
    """
    destino = pasta_da_aula(deck, pasta)
    nome = destino.name
    lista = roteiro(deck)

    capa, por_slide = pedidos_do_deck(deck)
    pedidos = {p for p in (capa, *por_slide) if p}
    prontas = ilustracoes(pedidos, destino / "imagens", pagar) if imagens and pedidos else {}

    ctx = t.nova_apresentacao(len(lista))
    conteudo = [s for tipo, s in lista if tipo == "conteudo"]
    imagem_do_slide = {id(s): prontas.get(p) for s, p in zip(conteudo, por_slide, strict=True)}
    divisorias = [d[0] for tipo, d in lista if tipo == "divisoria"]
    # Na agenda, os títulos dos slides; em apresentações longas, só as seções.
    ctx.agenda = (
        divisorias if divisorias and len(conteudo) > 12 else [s["titulo"] for s in conteudo]
    )

    n_secao = 0
    for tipo, dado in lista:
        if tipo == "capa":
            t.slide_capa(ctx, deck, prontas.get(capa))
        elif tipo == "agenda":
            t.slide_agenda(ctx)
        elif tipo == "divisoria":
            n_secao += 1
            t.slide_divisoria(ctx, n_secao, *dado)
        elif tipo == "conteudo":
            slide_conteudo(ctx, dado, imagem_do_slide[id(dado)])
        else:
            t.slide_encerramento(ctx)

    destino.mkdir(parents=True, exist_ok=True)
    arquivo = destino / f"{nome}.pptx"
    ctx.prs.save(arquivo)
    previa.exportar(ctx.prs, destino)
    print(f"{len(lista)} slides salvos em: {arquivo.resolve()}")
    print(f"Prévias PNG e PDF em: {destino.resolve()}")
    return destino
