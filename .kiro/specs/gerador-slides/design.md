# Design: Gerador de slides SENAI

## Visão geral

Mesma ideia do gerador de arquiteturas: **a IA escreve, o código desenha**.

```
Pedido do professor
      │
      ▼
IA (skill gerador-slides no Kiro, ou prompt portátil em qualquer chat)
      │ escreve
      ▼
slides/<nome>.yaml ──(hook FileSave)──▶ python -m senai_slides.validador slides/ --gerar
                                                   │
                           erro? ──sim──▶ mensagem em português, nada é gerado
                                                   │ não
                                                   ▼
                                      senai_slides.gerador.gerar(deck)
                                                   │
                                                   ▼
                                      Apresentacao (Pillow) ──▶ outputs/<nome>/slide_NN.png + <nome>.pdf
```

Por que YAML e não o script Python da versão anterior:

| | Script Python | Deck YAML |
|---|---|---|
| O que a IA escreve | código | só dados |
| Revisão | ler o código | validador aponta slide e campo |
| Risco | `import` ou laço inesperado | nenhum código é executado |
| Professor edita | precisa entender Python | lista de textos |

## Componentes

| Arquivo | Papel |
|---|---|
| `senai_slides/validador.py` | Lê o YAML, confere estrutura, limites, ordem e quantidade (erros) e boas práticas (avisos). CLI com `--gerar`. |
| `senai_slides/gerador.py` | `gerar(deck, pasta)`: traduz cada slide do deck em uma chamada da `Apresentacao`. Assume deck já validado. |
| `senai_slides/apresentacao.py` | Desenho, sem mudança. Continua disponível como API Python. |
| `slides/exemplo.yaml` | Deck de exemplo, igual ao do prompt do agente. |
| `.kiro/skills/gerador-slides/SKILL.md` | Fluxo do agente dentro do Kiro. |
| `.kiro/hooks/validar-slides.json` | FileSave em `slides/*.yaml` → validar e gerar. |
| `.kiro/hooks/caca-segredos.json` | PostTaskExecution → `python scripts/caca_segredos.py`. |
| `scripts/caca_segredos.py` | Procura chaves da AWS nos arquivos do `git ls-files`. |
| `agente/AGENTE_SLIDES_SENAI.md` | Prompt portátil; fonte única das regras de conteúdo e dos limites. |

## Formato do deck

```yaml
nome: NR-10 Introducao        # vira outputs/nr_10_introducao/
slides:
  - tipo: capa
    titulo: ...
  - tipo: divisoria
    titulo: ...
  - tipo: conteudo
    titulo: ...
    topicos: [..., ...]
    destaque: ...             # opcional
  - tipo: diagrama
    titulo: ...               # vai no círculo central
    itens:                    # de 3 a 6
      - titulo: ...
        texto: ...
  - tipo: encerramento
```

## Interfaces

```python
validar_deck(dados: object) -> tuple[list[str], list[str]]   # (erros, avisos)
validar_arquivo(caminho) -> Resultado                        # .erros, .avisos, .deck, .ok
gerar(deck: dict, pasta="outputs") -> Path
main(argv) -> int                                            # 0 = tudo certo, 1 = algum erro
```

```
python -m senai_slides.validador <arquivo.yaml | pasta> [...] [--gerar] [--saida outputs]
```

## Regras em ondas

As checagens seguem a ordem das tasks:

1. **Estrutura** (onda 1). Um slide com erro de estrutura fica de fora das outras checagens, mas os demais slides continuam sendo conferidos, para o professor ver o máximo de erros de uma vez. A ordem só é checada quando todos os tipos são válidos.
2. **Limites de texto, ordem e quantidade** (onda 2). São independentes entre si, e todos os erros aparecem juntos.
3. **Avisos** (onda 3). Não bloqueiam.

## Decisões

- **Limites mais rígidos que a biblioteca.** A `Apresentacao` aceita de 1 a 6 tópicos; o validador exige de 2 a 5, que é a regra de conteúdo do modelo SENAI. No diagrama, a biblioteca desenha de 2 a 6 itens e o validador exige de 3 a 6. A biblioteca é o limite físico, e o validador é o padrão.
- **Diagrama desenhado em 2x.** Círculos, cartões e arcos são desenhados no dobro da resolução e reduzidos, para as bordas saírem suaves; o texto é escrito depois, já em 1920x1080. O degradê dos arcos mistura as cores em HSV, para o laranja chegar ao verde passando pelo amarelo, e não por um marrom.
- **Números no lugar de ícones.** O modelo de referência tem ícones; o diagrama usa o número do item, que serve para qualquer assunto e não exige que a IA escolha um ícone.
- **Erro x aviso.** É erro o que quebra o desenho ou a identidade visual (limites, ordem, campos). É aviso o que depende de julgamento (destaque demais, seção vazia).
- **Hook valida a pasta inteira.** O comando não recebe o arquivo salvo como argumento; com poucos decks, validar `slides/` inteiro é rápido e simples.
- **Matcher aceita `/` e `\`,** porque no Windows o caminho pode vir com barra invertida.
- **Caça-segredos em Python e não em `grep`,** para rodar igual em Windows e Linux e devolver código 1 quando acha algo (o `git grep` faz o contrário).
- **Fonte única das regras:** a skill aponta para o prompt do agente em vez de copiar os limites.

## Tratamento de erros

| Situação | Mensagem (resumo) |
|---|---|
| YAML quebrado | "O YAML não pôde ser lido perto da linha N…" |
| Campo com nome errado | "Slide N (conteudo): o campo `topico` não existe. Campos aceitos: …" |
| Texto longo | "Slide N (capa): o título tem 72 caracteres; o limite é 60. Encurte: …" |
| Poucos/muitos tópicos | "Slide N (conteudo): tem 6 tópicos; use de 2 a 5…" |
| Ordem | "O primeiro slide precisa ser a `capa`." |
| Desenho falhou mesmo assim | "erro ao gerar: …" (não deve acontecer; coberto por teste de pior caso) |
