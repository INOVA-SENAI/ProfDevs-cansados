from pathlib import Path

from senai_slides.apresentacao import Apresentacao


def gerar(deck: dict, pasta: str | Path = "outputs") -> Path:
    """Desenha um deck já aprovado pelo validador e salva PNGs e PDF."""
    apres = Apresentacao(deck["nome"], pasta=pasta)
    for slide in deck["slides"]:
        tipo = slide["tipo"]
        if tipo == "capa":
            apres.capa(slide["titulo"])
        elif tipo == "divisoria":
            apres.divisoria(slide["titulo"])
        elif tipo == "conteudo":
            apres.conteudo(slide["titulo"], slide["topicos"], slide.get("destaque"))
        elif tipo == "diagrama":
            apres.diagrama(slide["titulo"], slide["itens"])
        else:
            apres.encerramento()
    return apres.salvar()
