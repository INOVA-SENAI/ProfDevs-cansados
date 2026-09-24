# Requisitos: Gerador de slides SENAI

A IA escreve o conteúdo da aula em um deck YAML; o validador confere o deck e só então a biblioteca `senai_slides` desenha os slides. Critérios de aceite em EARS (Easy Approach to Requirements Syntax).

Padrões EARS usados:
- **Sempre:** O <sistema> DEVE <resposta>.
- **Evento:** QUANDO <gatilho>, o <sistema> DEVE <resposta>.
- **Indesejado:** SE <condição>, ENTÃO o <sistema> DEVE <resposta>.
- **Opcional:** ONDE <recurso>, o <sistema> DEVE <resposta>.

---

## Requisito 1: Ler e checar o deck

**História:** Como professor, quero que o arquivo do deck seja conferido antes de qualquer desenho, para saber exatamente o que corrigir.

1. QUANDO o validador receber um arquivo `.yaml` ou `.yml`, o validador DEVE ler o arquivo em UTF-8 e conferir que ele tem só os campos `nome` e `slides`.
2. SE o YAML não puder ser lido, ENTÃO o validador DEVE informar a linha aproximada do problema e sugerir aspas e indentação.
3. SE o arquivo não estiver em UTF-8, ENTÃO o validador DEVE pedir para salvá-lo em UTF-8.
4. O validador DEVE aceitar só os tipos `capa`, `divisoria`, `conteudo`, `diagrama` e `encerramento`, e só os campos de cada tipo (e, nos itens do diagrama, só `titulo` e `texto`).
5. SE um slide tiver campo desconhecido, campo obrigatório faltando ou valor que não é texto, ENTÃO o validador DEVE dizer o número do slide, o tipo e o campo.
6. SE o `nome` não tiver letras nem números, ENTÃO o validador DEVE acusar erro, porque ele vira o nome da pasta.

## Requisito 2: Limites de texto

**História:** Como professor, quero que o texto caiba no modelo SENAI, para não ter slide poluído nem texto cortado.

1. O validador DEVE limitar o título a 60 caracteres na capa, 40 na divisória, 50 no conteúdo e 30 no diagrama.
2. O validador DEVE aceitar de 2 a 5 tópicos por slide de conteúdo, com até 90 caracteres cada.
3. ONDE o slide de conteúdo tiver `destaque`, o validador DEVE limitar o destaque a 100 caracteres e os tópicos a no máximo 3.
4. O validador DEVE contar caracteres depois de juntar espaços repetidos, do mesmo jeito que o desenho faz.
5. SE um texto passar do limite, ENTÃO o validador DEVE informar o tamanho atual, o limite e o texto a encurtar.
6. O gerador DEVE conseguir desenhar qualquer deck aprovado pelo validador, mesmo no pior caso de todos os limites.
7. O validador DEVE aceitar de 3 a 6 itens por diagrama, cada um com `titulo` de até 20 caracteres e `texto` de até 70.

## Requisito 3: Ordem do deck

1. O validador DEVE exigir a `capa` como primeiro slide e o `encerramento` como último.
2. SE houver mais de uma `capa` ou mais de um `encerramento`, ENTÃO o validador DEVE acusar erro.

## Requisito 4: Tamanho do deck

1. SE o deck tiver mais de 20 slides, ENTÃO o validador DEVE acusar erro e sugerir dividir a aula em duas apresentações.

## Requisito 5: Avisos de conteúdo

**História:** Como professor, quero dicas sobre boas práticas do modelo, sem que elas me impeçam de gerar.

1. O validador DEVE emitir avisos, que não bloqueiam a geração, quando:
   - mais de 1 a cada 3 slides de conteúdo tiver destaque;
   - houver conteúdo ou diagrama antes da primeira divisória;
   - uma divisória não for seguida de um slide de conteúdo ou diagrama;
   - o título de um conteúdo estiver em CAIXA ALTA;
   - o destaque não terminar com ponto final;
   - dois slides tiverem o mesmo título.

## Requisito 6: Gerar só o que passou

1. QUANDO o validador for chamado com `--gerar`, o validador DEVE gerar PNGs e PDF em `outputs/<nome>/` só para os decks sem erro.
2. SE algum deck tiver erro, ENTÃO o validador DEVE sair com código 1 e não gerar esse deck.
3. QUANDO receber uma pasta, o validador DEVE conferir todos os `.yaml` e `.yml` dela.

## Requisito 7: Skill do Kiro

1. O projeto DEVE ter a skill `.kiro/skills/gerador-slides/SKILL.md`, com `name` e `description`.
2. QUANDO o professor pedir slides ou apresentação no Kiro, a skill DEVE escrever `slides/<nome>.yaml`, rodar o validador, corrigir os erros e gerar.
3. A skill DEVE usar as regras de `agente/AGENTE_SLIDES_SENAI.md`, sem duplicar os limites.

## Requisito 8: Hooks

1. QUANDO um arquivo `slides/*.yaml` ou `slides/*.yml` for salvo, o hook `Validar e gerar slides` DEVE rodar o validador com `--gerar`.
2. QUANDO uma task de spec terminar, o hook `Caça-segredos` DEVE procurar chaves `AKIA`/`ASIA` e atribuições de `aws_secret` nos arquivos do repositório fora do `.gitignore`.
3. SE o caça-segredos achar algo, ENTÃO ele DEVE sair com código 1 e mostrar arquivo e linha, sem imprimir o valor encontrado.

## Requisito 9: Agente portátil

1. O prompt `agente/AGENTE_SLIDES_SENAI.md` DEVE fazer qualquer IA de chat responder com um deck YAML no mesmo formato.
2. O exemplo do prompt DEVE passar no validador sem erros nem avisos e ser igual a `slides/exemplo.yaml` (testado).

## Requisito 10: Slide de diagrama

**História:** Como professor, quero um slide com um esquema visual, para mostrar etapas, pilares ou partes de um conceito sem uma lista de tópicos.

1. QUANDO o deck tiver um slide `diagrama`, a biblioteca DEVE desenhar o título num círculo central e cada item num cartão numerado em volta, seguindo o layout de `.kiro/steering/referencias/diagrama.png` com as cores da paleta SENAI.
2. A biblioteca DEVE colocar a primeira metade dos itens à esquerda e o resto à direita, na ordem do deck.
3. A biblioteca DEVE usar sempre o laranja no primeiro item e o azul SENAI no último, espalhando as outras cores da sequência entre eles.
4. O diagrama DEVE manter a barra lateral e a logo azul dos slides internos, sem encostar na logo nem na borda direita (testado).

## Fora de escopo

- Design system próprio por grupo (`tokens.json`) e saída em `.pptx`: fica para a parte da tarde do workshop.
- Hook de pre-commit do Git que bloqueia o commit (desafio extra).
