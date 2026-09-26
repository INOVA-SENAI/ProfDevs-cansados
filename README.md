# ProfDevs-cansados

Crie apresentações de aula no padrão visual do **SENAI 2026** conversando com uma IA.

A IA escreve o conteúdo da aula em um **deck YAML**. O validador confere o deck (campos, layouts, tamanho dos textos, ícones, seções) e, se estiver tudo certo, a biblioteca `senai_slides` monta uma apresentação **.pptx editável** no padrão SENAI 2026: capa, agenda, divisórias de seção, slides de conteúdo com ícones, gráficos e imagens realistas (fotos reais ou criadas por IA), e encerramento com os contatos do SENAI/SC. Junto saem uma prévia PNG de cada slide e um PDF.

> **Status:** MVP pronto e testado. O texto, a montagem e as fotos reais não custam nada. Só as imagens criadas por IA são cobradas (Amazon Bedrock, cerca de US$ 0,07 por imagem), e só quando você autoriza.

O projeto junta três partes: o validador e o agente deste repositório, o gerador de apresentações `.pptx` do repositório [icrcode/teste-kiro](https://github.com/icrcode/teste-kiro) (layouts, ícones, gráficos e tema SENAI; licença MIT, em [LICENSES/teste-kiro.txt](LICENSES/teste-kiro.txt)) e o gerador de imagens da branch `prof/joao-borges` (Amazon Bedrock).

**Sumário:** [Como funciona](#como-funciona) · [Instalação](#instalação-uma-vez-só) · [Como usar em qualquer IA](#como-usar-em-qualquer-ia) · [Comandos](#comandos) · [O deck](#o-deck) · [Imagens e custos](#imagens-e-custos) · [Privacidade e segurança](#privacidade-e-segurança) · [Estrutura](#estrutura-do-projeto) · [Kiro](#trabalhamos-com-o-kiro) · [Desenvolvimento](#para-quem-vai-desenvolver)

## Como funciona

```
Pedido do professor
   │
   ▼
IA (skill no Kiro, prompt em qualquer chat, agente de código ou API)
   │  1. pergunta se você quer imagens e quanto vão custar
   │  2. escreve slides/<aula>.yaml
   ▼
python -m senai_slides.validador slides/<aula>.yaml --gerar      (no Kiro: ao salvar)
   │
   ├─ erro?  mensagem em português dizendo o slide e o que corrigir; nada é gerado
   └─ ok?    mostra quantas imagens faltam e o custo
             ├─ foto:  Wikimedia Commons (grátis, com crédito)
             ├─ gerar: Amazon Bedrock (pago), só com --aceitar-custo
             └─ outputs/<aula>/<aula>.pptx + slide_01.png ... + <aula>.pdf
```

**A IA escreve, o código desenha.** A IA só escreve dados (textos, nomes de ícones, valores de gráficos), e o validador não deixa gerar um deck fora do padrão. Por isso o visual sai sempre igual ao modelo oficial, qualquer que seja a IA. As imagens entram numa moldura fixa, com o crédito embaixo; a logo e os textos nunca passam por uma IA de imagem.

## Instalação (uma vez só)

Requisito: Python 3.10 ou mais novo.

```bash
git clone <url-do-repositorio>
cd ProfDevs-cansados
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux/Mac
pip install -r requirements.txt
copy .env.example .env           # Windows (Linux/Mac: cp); só precisa para imagens por IA
```

> No Windows, use `python` ou `py`. O comando `python3` pode abrir a Microsoft Store.

Na primeira geração no Windows, a fonte Open Sans é instalada só para o seu usuário (sem administrador), para o PowerPoint mostrar a tipografia do modelo. Para não instalar, use `--sem-instalar-fontes`.

Para imagens criadas por IA, configure a AWS uma vez ([Configurar a AWS](#configurar-a-aws-uma-vez-por-máquina)). Sem isso, tudo funciona com fotos reais ou sem imagens.

## Como usar em qualquer IA

O "cérebro" do projeto é um único arquivo: [agente/AGENTE_SLIDES_SENAI.md](agente/AGENTE_SLIDES_SENAI.md). Ele traz as regras de conteúdo, o formato do deck, os layouts, os limites de texto, a lista de ícones e um exemplo. Qualquer IA que receba esse arquivo vira o **Agente de Slides SENAI**. Não importa o modelo: o validador confere tudo o que a IA escrever.

A conversa é sempre igual, em qualquer IA:

1. Você pede a aula: tema, turma e, se quiser, nível e número de slides.
2. O agente **pergunta se você quer imagens** e dá a estimativa de custo:

   | Opção | Custo |
   |---|---|
   | Sem imagens | grátis |
   | Só fotos reais (Wikimedia Commons) | grátis |
   | Fotos reais e imagens criadas por IA nas cenas específicas | cerca de US$ 0,07 por imagem criada |
   | Só imagens criadas por IA | cerca de US$ 0,07 por imagem |

   Com 8 slides de conteúdo, a aula costuma ter 3 ou 4 imagens (a capa e cerca de 1 slide a cada 3). Só com IA, isso dá entre US$ 0,21 e US$ 0,28.
3. O agente devolve o deck em YAML e as instruções para gerar.
4. Você gera a apresentação no seu computador (ou o agente gera, no Kiro e nos agentes de código).
5. Se o validador acusar erro, você cola a mensagem na conversa, e o agente devolve o deck corrigido.

**Para pular a pergunta das imagens**, diga a escolha já no pedido: *"sem imagens"*, *"só fotos reais"* ou *"pode usar imagens por IA, até US$ 0,30"*.

"N slides" são sempre N slides **de conteúdo**. Capa, agenda, divisórias e encerramento entram sozinhos e não contam.

### No Kiro

Abra a pasta do projeto no Kiro e peça no chat: *"Gere uma aula de 8 slides sobre NR-10 para a turma de Instalações Elétricas"*. A skill `gerador-slides` entra sozinha (ou chame com `/gerador-slides`). Ela pergunta sobre as imagens, escreve `slides/<aula>.yaml`, roda o validador, corrige os erros, gera a apresentação e confere as prévias. Depois disso, cada vez que você editar e salvar o YAML, o hook gera de novo, **sem cobrar nada**.

### Em uma IA de chat (ChatGPT, Claude, Gemini, Copilot, DeepSeek, Le Chat...)

A IA de chat escreve o deck; quem gera a apresentação é o projeto, no seu computador.

1. Abra [agente/AGENTE_SLIDES_SENAI.md](agente/AGENTE_SLIDES_SENAI.md), copie **todo** o conteúdo e cole como primeira mensagem da conversa. Se a IA reclamar que o texto é longo demais, **anexe o arquivo** em vez de colar.
2. Na mensagem seguinte, faça o pedido. Modelo:
   ```
   Faça uma aula de 8 slides sobre NR-12 para a turma de Mecânica Industrial, nível resumido.
   ```
   Se tiver um trecho de apostila, cole junto: o agente usa como fonte principal.
3. Responda a pergunta das imagens.
4. Salve o bloco YAML que a IA devolver em `slides/` (ex.: `slides/aula_nr12.yaml`), em UTF-8.
5. No terminal, na pasta do projeto e com o `venv` ativo, rode:
   ```bash
   python -m senai_slides.validador slides/aula_nr12.yaml --gerar
   ```
   O validador mostra quantas imagens faltam e quanto custam. Sem mais nada, só entram as fotos reais, que são grátis. Se você aprovou imagens por IA, acrescente `--aceitar-custo`.
6. A apresentação aparece em `outputs/<nome-da-aula>/`: o `.pptx` para abrir e editar no PowerPoint, uma prévia PNG por slide e um PDF.

Se aparecer algum **erro**, cole a mensagem na mesma conversa. O agente já sabe corrigir e devolve o deck inteiro. Linhas de **aviso** não impedem a geração.

**Para não colar o arquivo em toda conversa**, deixe o agente fixo na IA que você usa:

| IA | Como deixar fixo |
|---|---|
| ChatGPT | Crie um **Projeto** e ponha o arquivo nas instruções ou nos arquivos do projeto. Num **GPT personalizado**, o campo de instruções é curto demais para o arquivo inteiro: envie-o como conhecimento e escreva nas instruções *"Siga à risca o arquivo AGENTE_SLIDES_SENAI.md"*. |
| Claude | Crie um **Projeto** e adicione o arquivo ao conhecimento do projeto, ou cole o texto nas instruções do projeto. |
| Gemini | Crie um **Gem** e cole o texto nas instruções, ou envie o arquivo como conhecimento do Gem. |
| Copilot e outras | Anexe o arquivo no começo de cada conversa. |

Dicas:

- O prompt tem uns 25 mil caracteres. Prefira a versão mais recente do modelo, que segue melhor instruções longas. Modelos pequenos erram mais campos, mas o validador aponta cada erro, e basta colar a mensagem de volta.
- Se a IA começar a inventar campos ou layouts, lembre: *"Siga só o formato do AGENTE_SLIDES_SENAI.md"*. Em conversas muito longas, abra uma nova e cole o arquivo de novo.
- A IA de chat não roda o validador nem vê o seu computador. Quem gera a apresentação é sempre você, com o comando do passo 5.

### Em um agente de código (Claude Code, Cursor, Copilot no VS Code, Codex, Gemini CLI, Windsurf...)

Agentes que leem a pasta e rodam comandos fazem tudo sozinhos, como a skill do Kiro. Abra a pasta do projeto no agente e mande:

```
Leia .kiro/skills/gerador-slides/SKILL.md e agente/AGENTE_SLIDES_SENAI.md e siga os passos
da skill para criar uma aula de 8 slides sobre NR-12 para a turma de Mecânica Industrial.
```

O agente pergunta sobre as imagens, escreve o deck em `slides/`, valida, corrige, gera e confere as prévias. Se ele não ativar o `venv`, peça para usar o Python do projeto direto: `venv\Scripts\python -m senai_slides.validador ...` (Windows) ou `venv/bin/python -m senai_slides.validador ...` (Linux/Mac). A skill proíbe usar `--aceitar-custo` sem você aprovar o valor.

### Pela API de qualquer modelo

Para automatizar (um script, um bot, uma integração):

1. Use o conteúdo de [agente/AGENTE_SLIDES_SENAI.md](agente/AGENTE_SLIDES_SENAI.md) como **instrução de sistema** (*system prompt*).
2. Mande o pedido como mensagem do usuário, **já com a escolha das imagens**, porque ninguém vai responder a pergunta. Ex.: *"Aula de 8 slides sobre NR-12 para Mecânica Industrial, nível resumido. Imagens: só fotos reais."*
3. Pegue o único bloco ` ```yaml ` da resposta e salve em `slides/<aula>.yaml`.
4. Rode `python -m senai_slides.validador slides/<aula>.yaml --gerar`. O código de saída é `0` quando deu tudo certo e `1` quando houve erro.
5. Se houve erro, mande a saída do validador como nova mensagem na mesma conversa e repita a partir do passo 3.

### Sem IA

O deck é um arquivo de texto comum. Copie [slides/exemplo.yaml](slides/exemplo.yaml), troque o conteúdo seguindo a seção [O deck](#o-deck) e rode o validador.

## Comandos

```bash
python -m senai_slides.validador slides/aula.yaml                   # só confere
python -m senai_slides.validador slides/aula.yaml --gerar           # confere e gera (sem custo)
python -m senai_slides.validador slides/aula.yaml --gerar --aceitar-custo   # cria também as imagens por IA
python -m senai_slides.validador slides/ --gerar                    # todos os decks da pasta
```

| Opção | O que faz |
|---|---|
| `--gerar` | Monta o `.pptx`, as prévias PNG e o PDF de cada deck sem erro. Entram as fotos reais e o que já está no cache |
| `--aceitar-custo` | Cria na Amazon Bedrock as imagens por IA que faltam (cerca de US$ 0,07 cada). Use só depois de aprovar o valor |
| `--sem-imagens` | Gera sem nenhuma imagem, nem as do cache: não busca fotos nem cria imagens. Para quando não há internet |
| `--saida PASTA` | Pasta de saída (padrão: `outputs`) |
| `--sem-instalar-fontes` | Não instala a Open Sans no Windows |

Exemplo de saída:

```
slides\exemplo.yaml: OK, 8 slides de conteúdo.
  Imagens: 1 foto real a buscar (grátis) e 2 imagens a criar por IA (cerca de US$ 0,14).
Custo não autorizado: 2 imagens a criar por IA (cerca de US$ 0,14) ficam de fora, e esses slides saem sem imagem. ...
Buscando 1 foto(s) no Wikimedia Commons...
13 slides salvos em: ...\outputs\nr_10_introducao\nr_10_introducao.pptx
```

- **erro:** o deck está fora do formato (campo errado, texto longo demais, ícone que não existe...). Nada é gerado até corrigir. A mensagem diz o número do slide, contando só os slides de conteúdo.
- **aviso:** boa prática (layouts repetidos, capa sem imagem, dados ilustrativos...). Não impede a geração.

Cada aula gera, em `outputs/<nome-da-aula>/`: `<nome-da-aula>.pptx` (editável no PowerPoint), `slide_01.png`, `slide_02.png`... (prévias em 1920x1080), `<nome-da-aula>.pdf` e a pasta `imagens/` (cache das imagens).

## O deck

"N slides" são N slides de conteúdo, na lista `slides`. Capa, agenda (a partir de 4 slides), uma divisória por seção e encerramento são montados sozinhos.

```yaml
nome: NR-10 Introducao
titulo: Segurança em Instalações Elétricas
uc: Instalações Elétricas
modo: resumido                  # ou aprofundado: textos maiores e notas mais longas
tags: [NR-10, segurança]
imagem:
  gerar: an electrician locking a circuit breaker with a red safety padlock   # imagem da capa

secoes:
  - nome: Riscos elétricos
    descricao: O que pode acontecer e onde o perigo aparece

slides:
  - layout: cartoes
    secao: Riscos elétricos
    titulo: Principais riscos da eletricidade
    itens:
      - icone: electric_bolt
        titulo: Choque elétrico
        texto: Corrente passando pelo corpo, que pode causar parada cardíaca.
      - icone: local_fire_department
        titulo: Arco elétrico
        texto: Descarga com calor intenso, que causa queimaduras graves.
    notas: Apresente os riscos e peça exemplos que a turma já viu.
```

**Campos do deck**

| Campo | O que é | Limite |
|---|---|---|
| `titulo` | Título da capa (obrigatório) | 60 caracteres |
| `nome` | Nome da pasta e dos arquivos gerados (padrão: o título) | 60 |
| `subtitulo` | Frase da capa (aparece se não houver `uc`) | 80 |
| `uc` | Curso ou unidade curricular; a capa mostra "UC: ..." | 60 |
| `modo` | `resumido` (padrão) ou `aprofundado` | |
| `tags` | Palavras-chave em pílulas na capa | até 5, com 20 cada |
| `imagem` | Imagem da capa: `foto:` ou `gerar:` ([Imagens e custos](#imagens-e-custos)) | 100 / 300 |
| `imagens` | `false` quando a aula não deve ter imagens | |
| `logo_curso` | `true` põe o logo "Técnico DESI" na capa | |
| `notas_capa` | Notas do apresentador da capa | 800 |
| `secoes` | Até 6 seções, cada uma com `nome` (40) e `descricao` (80); cada seção vira uma divisória | |
| `slides` | Os slides de conteúdo (obrigatório) | de 1 a 20 |

Todo slide tem `layout`, `titulo` (50 caracteres; 30 no `diagrama`), `notas` (800) e, opcionais, `subtitulo` (80) e `secao` (obrigatória quando o deck tem `secoes`). Os outros campos dependem do layout:

| Layout | Para quê |
|---|---|
| `topicos` | 2 a 6 conceitos com ícone, título e texto |
| `cartoes` | 2 a 4 cartões lado a lado |
| `numeros` | 2 a 4 indicadores em destaque |
| `processo` | 3 a 6 etapas em sequência |
| `linha_do_tempo` | 3 a 5 marcos |
| `comparacao` | duas colunas lado a lado |
| `grafico` | barras, barras horizontais, linhas ou pizza, com a fonte dos dados |
| `destaque` | uma frase de impacto |
| `tabela` | até 5 colunas e 8 linhas |
| `ilustracao` | 2 a 5 itens ao lado de uma foto real ou de uma imagem criada por IA |
| `diagrama` | título no círculo central e 3 a 6 itens em volta (modelo em [.kiro/steering/referencias/diagrama.png](.kiro/steering/referencias/diagrama.png)) |

Os campos de cada layout, os limites de texto de cada modo e a lista de ícones estão no [prompt do agente](agente/AGENTE_SLIDES_SENAI.md), seções 3 a 5. O exemplo completo, com 8 slides e 7 layouts, está em [slides/exemplo.yaml](slides/exemplo.yaml).

Regras de conteúdo que o agente segue (e que valem para quem escreve à mão):

- Pouco texto por slide; varie os layouts (nunca o mesmo em slides seguidos).
- Não invente números de normas, valores técnicos ou estatísticas. Dado que ainda vai ser levantado fica como `[__]`; gráfico com valores aproximados leva "Dados ilustrativos" na `fonte`.
- Com 8 slides ou mais, organize a aula em 2 a 4 seções.
- Notas do apresentador em todos os slides.
- Se um texto tiver `:`, começar com caractere especial ou for só um número, coloque-o entre aspas.

## Imagens e custos

A capa e cada slide `ilustracao` podem levar uma imagem realista, escolhida conforme o contexto do slide. O campo `imagem` tem duas formas:

```yaml
imagem:
  foto: asphalt paver        # busca uma foto real no Wikimedia Commons (palavras-chave em inglês)
imagem:
  gerar: a teacher reviewing a digital booklet with students in a computer lab   # a IA cria a cena
```

- **`foto`:** busca uma foto real, de licença livre (CC0, domínio público, CC BY ou CC BY-SA), no Wikimedia Commons. É gratuita. O crédito com autor e licença sai embaixo da foto, como a licença pede. Se nenhuma foto servir, o terminal avisa: sem `--aceitar-custo`, o slide fica sem imagem; com ele, a imagem é criada por IA.
- **`gerar`:** a IA cria uma imagem fotográfica com o Style Guide da Stability AI na Amazon Bedrock (o gerador de imagens da branch `prof/joao-borges`), em [senai_slides/imagens.py](senai_slides/imagens.py). Custa cerca de US$ 0,07 e leva uns 10 s por imagem, cobrados na conta AWS da credencial. A imagem sai com a legenda "Imagem gerada por IA". Texto sozinho em `imagem` também é `gerar`.
- **Descrições em inglês**, sem texto, letras, logotipos ou pessoas reais identificáveis. O estilo não precisa ser descrito: sai sempre realista.
- **Cache:** cada imagem fica em `outputs/<aula>/imagens/`. Gerar de novo sem mudar a `imagem` não busca nem cobra outra vez. Mudar uma única palavra de um `gerar:` cria (e cobra) uma imagem nova. Apagar a pasta `imagens/` faz tudo ser buscado e cobrado de novo.
- **Deck sem imagens:** `imagens: false` no topo do deck. O validador não pede imagem na capa nem slides `ilustracao`.
- **Sem internet:** `--gerar --sem-imagens`. Nenhuma imagem entra, nem as do cache: a capa sai sem figura, e os slides `ilustracao` viram slides de tópicos.

**Quanto custa**

| O quê | Custo |
|---|---|
| Validar, montar o `.pptx`, as prévias e o PDF | grátis, no seu computador |
| Conversa com a IA que escreve o deck | o plano da IA que você já usa; o projeto não cobra nada |
| `foto:` (Wikimedia Commons) | grátis |
| `gerar:` (Amazon Bedrock) | cerca de US$ 0,07 por imagem, cobrado **uma vez** (depois vem do cache) e **só com `--aceitar-custo`** |
| Hook do Kiro ao salvar | nunca cobra: não usa `--aceitar-custo` |

Antes de cobrar qualquer coisa, o validador mostra a linha `Imagens:` com a conta exata de cada deck, já descontando o cache. Sem `--aceitar-custo`, ele avisa quantas imagens ficaram de fora e quanto custariam.

### Configurar a AWS (uma vez por máquina)

Só é preciso para as imagens criadas por IA (`gerar:`).

1. Na Amazon Bedrock, região **us-east-1**, ative o acesso aos *Stability AI Image Services*. Isso aceita os termos do AWS Marketplace, com cobrança por uso, e precisa ser feito uma vez por conta.
2. Copie `.env.example` para `.env`, tire o `#` da linha `AWS_BEARER_TOKEN_BEDROCK=` e cole a chave de API da Bedrock depois do `=`. A chave é criada no console da Bedrock (*API keys* → *long-term*); prefira uma que só possa chamar os modelos da Stability.
   - Sem chave: deixe a linha comentada e rode `aws configure set region us-east-1` e `aws login`.
3. O `.env` está no `.gitignore`, e o caça-segredos acusa chave da Bedrock em qualquer outro arquivo. **Nunca faça commit da chave nem cole a chave no chat de uma IA.**

| Mensagem (começo) | O que fazer |
|---|---|
| `Falta uma credencial AWS válida` | Confira o `.env` ou refaça o `aws login`. Enquanto isso, gere sem `--aceitar-custo` |
| `A Bedrock recusou o pedido (AccessDeniedException)` | Ative os modelos (passo 1). Conta AWS nova pode levar até 2 h para ser verificada |
| `A Bedrock recusou o pedido (ThrottlingException)` | Limite de imagens por minuto da conta. Rode de novo: as imagens prontas ficam no cache |
| `A Bedrock não devolveu imagem (motivo: Filter reason ...)` | O filtro de conteúdo barrou a descrição. Reescreva a `imagem` do slide de forma mais neutra |
| `Não foi possível buscar a foto no Wikimedia Commons` | Sem internet ou o site fora do ar. Tente de novo, troque `foto` por `gerar` ou use `--sem-imagens` |
| `Nenhuma foto livre para ...` (aviso) | O Commons não tinha foto que servisse. Use palavras-chave mais comuns; com `--aceitar-custo`, ela é criada por IA |
| `Custo não autorizado: N imagens a criar por IA ...` (aviso) | A apresentação saiu sem as imagens pagas. Se o custo estiver aprovado, rode de novo com `--aceitar-custo` |
| `O deck está com imagens: false ...` (erro) | Tire a `imagem` e troque o layout `ilustracao` por `topicos` ou `cartoes`, ou mude para `imagens: true` |

## Privacidade e segurança

- **Dados de alunos:** nenhum nome, nota ou dado pessoal de aluno no deck. O texto do pedido e da apostila vai para o serviço da IA que você usa.
- **Fotos de pessoas:** não use fotos de alunos ou de pessoas identificáveis sem autorização (LGPD). O modelo de slides do teste-kiro tinha uma colagem com fotos de alunos e saiu do projeto por isso.
- **Chave da AWS:** fica só no `.env`. Nunca no código, no deck, no chat de uma IA, num print ou num commit. Se a chave vazar, apague-a no console da Bedrock e crie outra.
- **Caça-segredos:** `python scripts/caca_segredos.py` procura chaves da AWS e da Bedrock no repositório. No Kiro, ele roda sozinho ao fim de cada task.

## Estrutura do projeto

| Caminho | O que tem |
|---|---|
| [agente/AGENTE_SLIDES_SENAI.md](agente/AGENTE_SLIDES_SENAI.md) | Regras de conteúdo, layouts, limites e ícones; é o prompt para usar em qualquer IA |
| [slides/](slides/) | Decks das aulas em YAML, incluindo o [exemplo](slides/exemplo.yaml) |
| [senai_slides/validador.py](senai_slides/validador.py) | Confere o deck, mostra o custo das imagens e, com `--gerar`, monta a apresentação |
| [senai_slides/gerador.py](senai_slides/gerador.py) | Roteiro (capa, agenda, divisórias, conteúdo, encerramento), imagens e arquivos de saída |
| [senai_slides/tema.py](senai_slides/tema.py) | Cores, fontes, ícones, peças do PowerPoint e os slides fixos |
| [senai_slides/layouts.py](senai_slides/layouts.py) | Os 11 layouts de conteúdo e os gráficos |
| [senai_slides/diagrama.py](senai_slides/diagrama.py) | Fundo do layout `diagrama` |
| [senai_slides/previa.py](senai_slides/previa.py) | Prévia PNG e PDF a partir do `.pptx`, sem PowerPoint |
| [senai_slides/imagens.py](senai_slides/imagens.py) | Busca fotos no Wikimedia Commons e cria imagens na Amazon Bedrock, com cache e estimativa de custo |
| [senai_slides/icones.py](senai_slides/icones.py) | Lista de ícones Material Symbols permitidos |
| [senai_slides/assets/](senai_slides/assets/) | Logos e fontes (Open Sans e os ícones). **Não edite.** |
| [scripts/caca_segredos.py](scripts/caca_segredos.py) | Procura chaves da AWS e da Bedrock no repositório |
| [.env.example](.env.example) | Modelo do `.env` com a credencial da Bedrock (o `.env` fica fora do git) |
| [LICENSES/](LICENSES/) | Licença do código reaproveitado do teste-kiro (MIT) |
| [tests/](tests/) | Testes automatizados (nenhum chama a AWS nem a internet) |
| `outputs/` | Apresentações geradas e cache das imagens (fora do git) |

## Trabalhamos com o Kiro

Antes de mexer no projeto, leia a pasta `.kiro/`:

| Arquivo | O que tem |
|---|---|
| [.kiro/steering/product.md](.kiro/steering/product.md) | Objetivo e público do produto |
| [.kiro/steering/tech.md](.kiro/steering/tech.md) | Stack, comandos e regras técnicas |
| [.kiro/steering/structure.md](.kiro/steering/structure.md) | Pastas e convenções de nomes |
| [.kiro/steering/identidade-visual.md](.kiro/steering/identidade-visual.md) | Cores, fonte e desenho de cada tipo de slide |
| [.kiro/specs/gerador-slides/](.kiro/specs/gerador-slides/) | Spec atual: `requirements.md` (EARS), `design.md` e `tasks.md` (em ondas) |
| [.kiro/skills/gerador-slides/SKILL.md](.kiro/skills/gerador-slides/SKILL.md) | Skill do agente: pergunta sobre as imagens, escreve o deck, valida e gera. Também serve de roteiro para outros agentes de código |
| [.kiro/hooks/](.kiro/hooks/) | Validar e gerar ao salvar `slides/*.yaml` (sem custo); caça-segredos ao fim de cada task |

## Identidade visual

- Tema extraído do modelo SENAI 2026 "Identidade Nova" pelo gerador do teste-kiro. O arquivo do modelo não está no projeto: a cópia do teste-kiro tinha uma colagem com fotos de alunos, que não pode ser distribuída (LGPD)
- Azul SENAI `#164194` e laranja `#E84910`; nos gráficos, uma paleta validada para daltonismo
- Fonte Open Sans (a do modelo) e ícones Material Symbols Rounded, sem emojis
- Slides 16:9 (13,33 x 7,5 pol), com transição suave e entrada animada dos gráficos
- Toda imagem leva o crédito do autor ou a legenda "Imagem gerada por IA"
- Detalhes de cada tipo de slide em [.kiro/steering/identidade-visual.md](.kiro/steering/identidade-visual.md)

## Para quem vai desenvolver

```bash
pytest            # testes (nenhum chama a AWS nem a internet)
ruff check .      # lint
ruff format .     # formatação
```

- **Regra de ouro:** se mudar um layout, um campo do deck, um limite do validador ou a lista de ícones, atualize também o [prompt do agente](agente/AGENTE_SLIDES_SENAI.md) e a tabela de campos deste README. Os testes validam e geram o exemplo do prompt e conferem a lista de ícones; eles falham se o prompt e o código divergirem.
- Antes de commitar: `python scripts/caca_segredos.py`.
- Crie branches no formato `feature/nome-da-feature` ou `fix/descricao-do-bug`.
- Arquivos Python em `snake_case`; pastas em minúsculas e sem espaços.

## O que falta

- [ ] Testar a skill no Kiro e o prompt em pelo menos duas IAs diferentes (ex.: ChatGPT e Gemini) com um tema real de aula
- [ ] Revisar os ícones dos decks convertidos do formato antigo (receberam ícones genéricos)
- [ ] Opcional: gráficos nativos do PowerPoint (hoje são imagens em alta resolução)
- [ ] Desafio extra: rodar o caça-segredos como pre-commit do Git
