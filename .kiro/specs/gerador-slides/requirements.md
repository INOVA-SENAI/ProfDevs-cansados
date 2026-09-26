# Requirements Document

## Introduction

Gerador de slides SENAI. A IA escreve o conteúdo da aula em um deck YAML; o validador confere o deck e só então a biblioteca `senai_slides` monta a apresentação `.pptx`. Critérios de aceite em EARS (Easy Approach to Requirements Syntax).

Padrões EARS usados:
- **Sempre:** O <sistema> DEVE <resposta>.
- **Evento:** QUANDO <gatilho>, o <sistema> DEVE <resposta>.
- **Indesejado:** SE <condição>, ENTÃO o <sistema> DEVE <resposta>.
- **Opcional:** ONDE <recurso>, o <sistema> DEVE <resposta>.

## Glossary

- **Deck**: arquivo YAML em `slides/` com o conteúdo de uma apresentação.
- **Slide de conteúdo**: cada item da lista `slides` do deck; capa, agenda, divisórias e encerramento são montados à parte.
- **Layout**: forma de um slide de conteúdo (`topicos`, `cartoes`, `diagrama`...).
- **Modo**: `resumido` (frases curtas) ou `aprofundado` (explicações e notas mais longas).
- **Ilustração**: imagem gerada pela Amazon Bedrock a partir do campo `imagem`.
- **Validador**: `python -m senai_slides.validador`; **gerador**: `senai_slides.gerador.gerar`.

## Requirements

### Requirement 1: Ler e checar o deck

**História:** Como professor, quero que o arquivo do deck seja conferido antes de qualquer desenho, para saber exatamente o que corrigir.

#### Acceptance Criteria

1. QUANDO o validador receber um arquivo `.yaml` ou `.yml`, o validador DEVE ler o arquivo em UTF-8 e aceitar só os campos do deck: `nome`, `titulo`, `subtitulo`, `uc`, `modo`, `tags`, `logo_curso`, `imagem`, `notas_capa`, `secoes` e `slides`.
2. SE o YAML não puder ser lido, ENTÃO o validador DEVE informar a linha aproximada do problema e sugerir aspas e indentação.
3. SE o arquivo não estiver em UTF-8, ENTÃO o validador DEVE pedir para salvá-lo em UTF-8.
4. O validador DEVE aceitar só os layouts `topicos`, `cartoes`, `numeros`, `processo`, `linha_do_tempo`, `comparacao`, `grafico`, `destaque`, `tabela`, `ilustracao` e `diagrama`, e em cada layout só os campos que ele usa.
5. SE um slide tiver campo desconhecido, campo obrigatório faltando, valor que não é texto ou quantidade de itens fora do layout, ENTÃO o validador DEVE dizer o número do slide de conteúdo, o layout e o campo.
6. SE um ícone não estiver na lista de `icones.py`, ENTÃO o validador DEVE acusar erro e sugerir nomes parecidos.
7. SE o deck estiver no formato antigo (`tipo:` em cada slide), ENTÃO o validador DEVE dar um único erro explicando o formato novo.

### Requirement 2: Limites de texto

**História:** Como professor, quero que o texto caiba no modelo SENAI, para não ter slide poluído nem texto cortado.

#### Acceptance Criteria

1. O validador DEVE limitar o título a 60 caracteres na capa, 50 nos slides de conteúdo e 30 no `diagrama`, e o subtítulo a 80.
2. O validador DEVE limitar o texto dos itens a 70 caracteres no modo `resumido` e a 170 no `aprofundado` (70 no `diagrama`).
3. O validador DEVE contar caracteres depois de juntar espaços repetidos.
4. SE um texto passar do limite, ENTÃO o validador DEVE informar o tamanho atual, o limite e o texto a encurtar.
5. O gerador DEVE reduzir a fonte de cada caixa até o texto caber, inclusive quando uma palavra sozinha não cabe na largura, e conseguir montar qualquer deck aprovado pelo validador, mesmo no pior caso dos limites.

### Requirement 3: Roteiro da apresentação

#### Acceptance Criteria

1. O gerador DEVE montar a capa no início e o encerramento no fim; a lista `slides` tem só os slides de conteúdo (de 1 a 20).
2. QUANDO o deck tiver 4 slides de conteúdo ou mais, o gerador DEVE incluir uma agenda com os títulos (ou com as seções, acima de 12 slides).
3. ONDE o deck tiver `secoes`, o gerador DEVE incluir uma divisória antes do primeiro slide de cada seção, e o validador DEVE exigir que cada slide use uma seção listada, que os slides de uma seção fiquem juntos e que toda seção tenha slides.

### Requirement 4: Saída

#### Acceptance Criteria

1. QUANDO o validador for chamado com `--gerar`, o gerador DEVE salvar em `outputs/<nome>/` o `.pptx` editável, uma prévia PNG de 1920x1080 por slide e um PDF, só para os decks sem erro.
2. O `.pptx` DEVE seguir o padrão SENAI 2026 de `identidade-visual.md`, sem fotos de pessoas nos fundos, ter notas do apresentador em cada slide e transição suave, e trazer textos e ícones editáveis.
3. SE algum deck tiver erro, ENTÃO o validador DEVE sair com código 1 e não gerar esse deck.
4. QUANDO receber uma pasta, o validador DEVE conferir todos os `.yaml` e `.yml` dela.

### Requirement 5: Avisos de conteúdo

**História:** Como professor, quero dicas sobre boas práticas, sem que elas me impeçam de gerar.

#### Acceptance Criteria

1. O validador DEVE emitir avisos, que não bloqueiam a geração, quando:
   - dois slides seguidos usarem o mesmo layout;
   - um deck com 5 slides ou mais usar menos de 4 layouts;
   - a capa não tiver `imagem`, ou um deck com 3 slides ou mais não tiver nenhum `ilustracao`;
   - dois slides tiverem o mesmo título;
   - um gráfico usar "Dados ilustrativos";
   - um slide do modo `aprofundado` não tiver `notas`.

### Requirement 6: Gráficos e dados

#### Acceptance Criteria

1. O layout `grafico` DEVE aceitar barras, barras horizontais, linhas e pizza (pizza com 1 série), com um valor numérico por categoria e a `fonte` obrigatória.
2. O agente DEVE usar só dados que conhece com segurança; valores aproximados levam "Dados ilustrativos" na fonte, e dados que o professor ainda vai levantar ficam como `[__]`.

### Requirement 7: Skill do Kiro

#### Acceptance Criteria

1. O projeto DEVE ter a skill `.kiro/skills/gerador-slides/SKILL.md`, com `name` e `description`.
2. QUANDO o professor pedir slides ou apresentação no Kiro, a skill DEVE escrever `slides/<nome>.yaml`, rodar o validador, corrigir os erros, gerar e conferir as prévias.
3. A skill DEVE usar as regras de `agente/AGENTE_SLIDES_SENAI.md`, sem duplicar os limites.

### Requirement 8: Hooks

#### Acceptance Criteria

1. QUANDO um arquivo `slides/*.yaml` ou `slides/*.yml` for salvo, o hook `Validar e gerar slides` DEVE rodar o validador com `--gerar`.
2. QUANDO uma task de spec terminar, o hook `Caça-segredos` DEVE procurar chaves `AKIA`/`ASIA`, atribuições de `aws_secret` e chaves da Bedrock nos arquivos do repositório fora do `.gitignore`.
3. SE o caça-segredos achar algo, ENTÃO ele DEVE sair com código 1 e mostrar arquivo e linha, sem imprimir o valor encontrado.

### Requirement 9: Agente portátil

#### Acceptance Criteria

1. O prompt `agente/AGENTE_SLIDES_SENAI.md` DEVE fazer qualquer IA de chat responder com um deck YAML no mesmo formato.
2. O exemplo do prompt DEVE passar no validador sem erros nem avisos e ser igual a `slides/exemplo.yaml`, e a lista de ícones do prompt DEVE ser igual à de `icones.py` (testado).
3. "N slides" no pedido do professor DEVEM ser N slides de conteúdo.

### Requirement 10: Layout diagrama

#### Acceptance Criteria

1. QUANDO o deck tiver um slide `diagrama`, a biblioteca DEVE desenhar o título num círculo central e cada item num cartão colorido em volta, com o ícone do item num círculo branco, seguindo `.kiro/steering/referencias/diagrama.png`.
2. A biblioteca DEVE colocar a primeira metade dos itens à esquerda e o resto à direita, com o laranja no primeiro item e o azul SENAI no último.
3. Textos e ícones do diagrama DEVEM continuar editáveis no PowerPoint.

### Requirement 11: Ilustrações geradas por IA

**História:** Como professor, quero imagens realistas sobre o assunto de cada slide, sem precisar procurar ou desenhar.

#### Acceptance Criteria

1. O deck DEVE aceitar `imagem` na capa e no layout `ilustracao`, como `foto: <palavras-chave>` (até 100 caracteres) ou `gerar: <cena>` (até 300); texto sozinho vale como `gerar`.
2. QUANDO a `imagem` for `foto`, o gerador DEVE usar a primeira foto do Wikimedia Commons que seja JPEG ou PNG, tenha 800 px ou mais de lado e licença CC0, domínio público, CC BY ou CC BY-SA, e DEVE pôr no slide o crédito com autor e licença. SE nenhuma servir, ENTÃO o gerador DEVE avisar no terminal e, com `--aceitar-custo`, criar a imagem por IA; sem essa opção, o slide fica sem imagem.
2a. QUANDO a `imagem` for `gerar`, o gerador DEVE criar uma imagem fotográfica pela Amazon Bedrock (Stability AI Style Guide, `photographic`), sem pixel art, e DEVE pôr no slide a legenda "Imagem gerada por IA".
3. O gerador DEVE guardar cada imagem em `outputs/<nome>/imagens/` e, QUANDO a mesma descrição e o mesmo estilo aparecerem de novo, DEVE usar o cache sem chamar a Bedrock.
4. SE a Bedrock recusar ou falhar, ENTÃO o validador DEVE mostrar a causa em português, não gerar aquele deck e manter no cache as imagens que deram certo.
5. ONDE o validador for chamado com `--sem-imagens`, o gerador DEVE montar a apresentação sem chamar a Bedrock; os slides `ilustracao` viram tópicos.
6. A credencial DEVE vir do `.env` (fora do git) ou da cadeia padrão da AWS, nunca do código ou do deck.
7. Nenhum teste automatizado DEVE chamar a AWS.
8. Antes de escrever o deck, a skill e o agente DEVEM perguntar ao professor se ele quer imagens (nenhuma, só fotos reais, fotos e imagens por IA ou só imagens por IA), com a estimativa de custo (cerca de US$ 0,07 por imagem criada), a menos que ele já tenha dito o que quer.
9. O validador DEVE mostrar, para cada deck sem erro, quantas imagens faltam buscar e criar, quantas já estão no cache e o custo aproximado.
10. O gerador SÓ DEVE chamar a Bedrock QUANDO o validador for chamado com `--aceitar-custo`. Sem essa opção, DEVE usar só as fotos reais e o cache e dizer quantas imagens por IA ficaram de fora e quanto custariam. O hook NÃO DEVE usar `--aceitar-custo`.
11. ONDE o deck tiver `imagens: false`, o validador DEVE recusar `imagem` na capa e o layout `ilustracao` e NÃO DEVE dar avisos de imagem.

### Fora de escopo

- Gráficos nativos do PowerPoint (hoje são imagens em alta resolução).
- Design system próprio por grupo (`tokens.json`).
- Hook de pre-commit do Git que bloqueia o commit (desafio extra).
