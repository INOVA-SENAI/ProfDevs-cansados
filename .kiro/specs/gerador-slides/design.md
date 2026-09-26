# Design Document

## Overview

**A IA escreve, o código desenha.** A IA (skill `gerador-slides` no Kiro, ou o prompt portátil em qualquer chat) escreve só dados num deck YAML: textos, nomes de ícones, valores de gráficos e descrições de ilustrações. O validador confere o deck e aponta cada problema em português; só um deck sem erro é montado.

O projeto junta três partes:

| Parte | Origem |
|---|---|
| Deck YAML, validador, agente, skill, hooks, layout `diagrama` | este repositório |
| Montagem do `.pptx` no modelo SENAI 2026 Identidade Nova: tema, 9 layouts, ícones, gráficos, agenda, divisórias, prévia | repositório icrcode/teste-kiro (licença MIT), portado para `senai_slides/` |
| Ilustrações pela Amazon Bedrock | branch `prof/joao-borges` (`mcp_imagem`), portado para `senai_slides/imagens.py` |

## Architecture

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
                                      gerador.gerar(deck)
                                        ├─ roteiro: capa, agenda, divisórias, conteúdo, encerramento
                                        ├─ imagens.ilustracoes(): cache ou Amazon Bedrock
                                        ├─ tema + layouts (python-pptx) ──▶ <nome>.pptx
                                        └─ previa (Pillow) ──▶ slide_NN.png + <nome>.pdf
```

## Components and Interfaces

| Arquivo | Papel |
|---|---|
| `senai_slides/validador.py` | Lê o YAML, confere deck, slides, itens, gráficos, tabelas, ícones e seções (erros) e boas práticas (avisos). Mostra a estimativa de imagens e custo de cada deck. CLI com `--gerar`, `--aceitar-custo`, `--sem-imagens` e `--sem-instalar-fontes`. |
| `senai_slides/gerador.py` | `roteiro(deck)` e `gerar(deck, pasta, imagens, pagar)`. Assume deck já validado. |
| `senai_slides/tema.py` | Paleta, fontes, ícones, peças do PowerPoint, ajuste de texto, gráficos base e os slides fixos (capa, agenda, divisória, encerramento). |
| `senai_slides/layouts.py` | Os 11 layouts de conteúdo e os gráficos de barras, linhas e pizza. |
| `senai_slides/diagrama.py` | Fundo do layout `diagrama` (imagem transparente em 2x). |
| `senai_slides/previa.py` | Desenha o `.pptx` como PNG e monta o PDF, sem PowerPoint. |
| `senai_slides/imagens.py` | Imagens: busca no Wikimedia Commons (`foto`), Style Guide fotográfico da Bedrock (`gerar`), créditos, cache e estimativa de custo. |
| `senai_slides/icones.py` | Lista de ícones permitidos (a fonte em `assets/fonts/` tem só estes). |
| `agente/AGENTE_SLIDES_SENAI.md` | Prompt portátil; fonte única das regras de conteúdo, dos layouts, dos limites e dos ícones. |
| `.kiro/skills/gerador-slides/SKILL.md` | Fluxo do agente dentro do Kiro. |
| `.kiro/hooks/*.json` | FileSave em `slides/*.yaml` → validar e gerar; PostTaskExecution → caça-segredos. |

```python
validar_deck(dados: object) -> tuple[list[str], list[str]]   # (erros, avisos)
validar_arquivo(caminho) -> Resultado                        # .erros, .avisos, .deck, .ok
roteiro(deck: dict) -> list[tuple[str, object]]
gerar(deck: dict, pasta="outputs", imagens=True, pagar=True) -> Path
estimativa(deck: dict, saida="outputs") -> Estimativa         # .fotos, .geradas, .em_cache, .custo
main(argv) -> int                                            # 0 = tudo certo, 1 = algum erro
```

## Data Models

```yaml
nome: NR-10 Introducao        # opcional: vira outputs/nr_10_introducao/
titulo: ...                   # capa
subtitulo: ...                # opcional
uc: ...                       # opcional: "UC: ..." na capa
modo: resumido                # ou aprofundado
tags: [..., ...]              # opcional, até 5
imagem: {foto: ...}           # opcional: foto real (palavras-chave) ou {gerar: ...} (cena), em inglês
logo_curso: false             # opcional: logo "Técnico DESI" na capa
secoes:                       # opcional: uma divisória por seção
  - nome: ...
    descricao: ...
slides:                       # só conteúdo, de 1 a 20
  - layout: topicos           # ou cartoes, numeros, processo, linha_do_tempo, comparacao,
                              #    grafico, destaque, tabela, ilustracao, diagrama
    secao: ...
    titulo: ...
    subtitulo: ...
    notas: ...
    itens: [{icone, titulo, texto, valor}]
    colunas: [{titulo, itens: [...]}]       # comparacao
    grafico: {tipo, eixo_y, categorias, series: [{nome, valores}], fonte}
    tabela: {cabecalho: [...], linhas: [[...]]}
    destaque: ...
    imagem: {foto: ...} ou {gerar: ...}     # ilustracao
```

## Correctness Properties

### Property 1: Deck aprovado sempre é montado

Todo deck aprovado pelo validador é montado sem erro, mesmo no pior caso dos limites (`test_deck_no_pior_caso_dos_limites_cabe_no_desenho`).

**Validates: Requirements 2.5**

### Property 2: Roteiro previsível

O número de slides do `.pptx` é sempre capa + agenda (a partir de 4) + uma divisória por seção + slides de conteúdo + encerramento (`test_roteiro_com_agenda_e_divisorias`).

**Validates: Requirements 3.1, 3.2, 3.3**

### Property 3: Todo layout tem desenho

Todo layout que o validador aceita tem uma função em `layouts.LAYOUTS` (`test_todo_layout_do_validador_tem_desenho`).

**Validates: Requirements 1.4**

### Property 4: Prompt e código não divergem

O exemplo do prompt passa no validador sem avisos e é igual a `slides/exemplo.yaml`, e a lista de ícones do prompt é igual à de `icones.py` (`tests/test_agente.py`).

**Validates: Requirements 9.2**

### Property 5: Nenhuma imagem é paga duas vezes

A mesma descrição de imagem, no mesmo estilo, nunca é gerada de novo (`test_cache_nao_paga_duas_vezes_pela_mesma_imagem`).

**Validates: Requirements 11.3**

### Property 6: Nada é cobrado sem autorização

Sem `--aceitar-custo`, o validador com `--gerar` nunca chama a Bedrock; com a opção, chama uma vez por imagem que a estimativa contou, e a estimativa seguinte dá zero (`test_cli_so_cobra_com_aceitar_custo`, `test_sem_pagar_so_entram_fotos_e_cache`).

**Validates: Requirements 11.9, 11.10**

## Decisões

- **Formato de conteúdo do teste-kiro, em YAML.** O teste-kiro validava JSON com pydantic e pedia o conteúdo à API do Claude ou ao Kiro CLI. Aqui o conteúdo é YAML, escrito pela skill ou por qualquer IA de chat, e o validador próprio dá mensagens em português com o número do slide. A orquestração pela API e pelo Kiro CLI ficou de fora: a skill cumpre esse papel.
- **Ajuste de texto próprio.** O `fit_text` do python-pptx falha quando uma palavra sozinha não cabe na largura (ex.: "DESENERGIZAÇÃO" no círculo do diagrama), e o erro era engolido, deixando a fonte no tamanho máximo. `tema.tamanho_que_cabe` mede com a Open Sans pelo Pillow, com a mesma altura de linha da prévia.
- **Fonte de ícones reduzida.** O Material Symbols completo tem 15 MB; a versão em `assets/fonts/` é estática (FILL 0, GRAD 0, opsz 48, wght 400), só com os ícones de `icones.py`, e tem 54 KB.
- **Diagrama em duas camadas.** O fundo (faixas, cartões, anel, sombras e esferas) é uma imagem transparente em 2x; textos e ícones são elementos do PowerPoint, editáveis. O degradê mistura as cores em HSV, para o laranja chegar ao verde passando pelo amarelo.
- **Imagens pelo gerador, não pelo MCP.** O deck chama o mesmo código do gerador de imagens do João direto; assim funciona também com o prompt portátil, e o cache evita pagar duas vezes quando o hook gera de novo a cada salvamento. 2 chamadas em paralelo e retentativa adaptativa do boto3, porque 3 simultâneas deram `ThrottlingException` (24/09/2026).
- **Imagens realistas: foto real ou criada.** Pixel art foi abandonada (25/09/2026). `foto` busca no Wikimedia Commons, que tem licenças livres e devolve autor e licença para o crédito; `gerar` usa o Style Guide com o preset `photographic`. O Style Guide exige uma imagem de referência; a referência é um degradê de luz gerado pelo código, sem pessoas, e a fidelidade 0,1 deixa a cena vir do texto (com 0,3 a imagem saía lavada).
- **Custo só com autorização.** O hook gera a pasta inteira a cada salvamento, e decks convertidos ou copiados podiam cobrar dezenas de imagens sem ninguém pedir. Por isso o professor escolhe as imagens na conversa, com a estimativa, e a CLI só cria imagem por IA com `--aceitar-custo`, que o hook nunca usa. Não há pergunta interativa no terminal: o agente do Kiro roda o comando sem ninguém para responder.
- **Sem a colagem do modelo.** O modelo `.pptx` do teste-kiro tinha uma colagem com fotos de alunos e de um professor, usada a 8% no fundo das divisórias e do encerramento. O arquivo saiu do projeto e o fundo virou um degradê azul.
- **Gráficos como imagem em HD.** Como no teste-kiro, os gráficos são desenhados pelo matplotlib no tamanho exato da área, em 300 dpi. Gráficos nativos do PowerPoint ficam para depois.
- **Erro x aviso.** É erro o que quebra o desenho ou o formato (campos, limites, layouts, ícones, seções). É aviso o que depende de julgamento (layout repetido, deck sem imagem, dados ilustrativos).
- **Hook valida a pasta inteira.** O comando não recebe o arquivo salvo; com poucos decks, validar `slides/` inteiro é simples. O matcher aceita `/` e `\`.
- **Fonte única das regras:** a skill aponta para o prompt do agente em vez de copiar os limites.

## Error Handling

| Situação | Mensagem (resumo) |
|---|---|
| YAML quebrado | "O YAML não pôde ser lido perto da linha N…" |
| Formato antigo | "Este deck está no formato antigo, com `tipo:` em cada slide…" |
| Campo que o layout não usa | "Slide N (cartoes): o layout `cartoes` não usa o campo `imagem`. Campos aceitos: …" |
| Texto longo | "Slide N (topicos): `titulo` tem 57 caracteres; o limite é 50. Encurte: …" |
| Quantidade de itens | "Slide N (cartoes): tem 5 itens; o layout `cartoes` usa de 2 a 4." |
| Ícone fora da lista | "… o ícone `raio` não está na lista de ícones permitidos. Parecidos: …" |
| Seções | "Slide N: os slides da seção "X" precisam ficar juntos…" |
| Sem credencial AWS | "erro ao gerar: Imagem "...": … Falta uma credencial AWS válida … rode sem --aceitar-custo." |
| Limite da conta | "… (ThrottlingException) … Rode de novo daqui a pouco: as imagens que já foram geradas ficam no cache" |
| Custo não aceito | "Custo não autorizado: 2 imagens a criar por IA (cerca de US$ 0,14) ficam de fora… rode de novo com --aceitar-custo" |
| `imagens: false` com imagem | "Slide N (ilustracao): O deck está com `imagens: false`… Troque o layout por `topicos` ou `cartoes`." |

## Testing Strategy

- `tests/test_validador.py`: cada regra do validador, avisos, pior caso dos limites montado de verdade e a CLI, com a estimativa e o `--aceitar-custo`.
- `tests/test_gerador.py`: roteiro, um deck com todos os layouts (`.pptx`, prévias, PDF, notas, página, imagens), `--sem-imagens`, logo do curso, ajuste de texto, diagrama e prévia.
- `tests/test_imagens.py`: pedido, prompt, referência neutra, `.env`, chamada à Bedrock, busca e crédito no Commons, reserva por IA, erros, cache, estimativa e geração sem pagar.
- `tests/test_agente.py`: exemplo do prompt e lista de ícones.
- `tests/test_kiro.py`: skill, hooks e caça-segredos.
- `tests/conftest.py`: troca a Bedrock por uma falsa em todos os testes e baixa a resolução dos gráficos.
