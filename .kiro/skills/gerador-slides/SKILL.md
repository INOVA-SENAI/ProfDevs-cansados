---
name: gerador-slides
description: Gera apresentações de aula no padrão visual SENAI 2026 (.pptx editável, prévias PNG e PDF), escrevendo um deck em YAML que o validador confere e a biblioteca senai_slides monta, com ícones, gráficos e imagens realistas (fotos reais ou criadas por IA). Use quando pedirem slides, apresentação, aula em slides ou deck para uma turma do SENAI.
---

# Gerador de slides SENAI

Você escreve o **conteúdo** da aula em `slides/<nome>.yaml`. Quem monta a apresentação é a biblioteca `senai_slides`. Nunca escreva código de desenho, nunca edite `senai_slides/` nem `senai_slides/assets/`.

As regras de conteúdo, o formato do YAML, os layouts, os limites de texto e a lista de ícones estão em `agente/AGENTE_SLIDES_SENAI.md`, seções 1 a 5. Leia antes de escrever. O exemplo completo está em `slides/exemplo.yaml`.

## Passos

1. **Entenda o pedido.** Tema, curso ou unidade curricular, nível (resumido ou aprofundado) e quantos slides de conteúdo (padrão: 8). "N slides" são N slides de conteúdo: capa, agenda, divisórias e encerramento são montados sozinhos. Se faltar o tema, pergunte junto com a pergunta do passo 2. Se o professor colar um trecho de apostila, use-o como fonte principal.
2. **Pergunte sempre sobre as imagens, com a estimativa de custo,** antes de escrever o deck. Só pule a pergunta se o professor já disse o que quer. Conte a capa e cerca de 1 slide `ilustracao` a cada 3 de conteúdo (com 8 slides, umas 3 ou 4 imagens) e ofereça:
   - **sem imagens:** grátis (`imagens: false` no deck);
   - **só fotos reais** do Wikimedia Commons: grátis, com o crédito do autor no slide;
   - **fotos reais e imagens criadas por IA** nas cenas que dificilmente existem em foto livre: cerca de US$ 0,07 por imagem criada, com a quantidade e o total (ex.: "1 foto e 2 imagens por IA: cerca de US$ 0,14");
   - **só imagens criadas por IA:** quantidade × US$ 0,07.

   Espere a resposta antes de continuar.
3. **Escreva o deck** em `slides/<nome>.yaml`, com `<nome>` em minúsculas e sem espaços (ex.: `slides/nr10_aula1.yaml`). Não sobrescreva um arquivo existente sem o professor pedir. Varie os layouts. Com imagens, ponha uma `imagem` na capa e use `ilustracao` em cerca de 1 a cada 3 slides, dentro do que o professor escolheu: `foto:` (palavras-chave em inglês) quando o assunto existe de verdade, como equipamentos, lugares e situações reais; `gerar:` (uma frase em inglês) quando precisa de uma cena específica. Sem imagens, escreva `imagens: false` e não use `imagem` nem `ilustracao`.
4. **Valide:** `python -m senai_slides.validador slides/<nome>.yaml`. Corrija todos os **erros** e rode de novo até passar. Leia os **avisos** e corrija os que fizerem sentido. A linha `Imagens:` mostra quantas faltam buscar e criar e o custo; se passar do que o professor aprovou, troque `gerar:` por `foto:` ou pergunte de novo com o novo total.
5. **Gere:** `python -m senai_slides.validador slides/<nome>.yaml --gerar`, com `--aceitar-custo` só se o professor aprovou o custo das imagens por IA. Sem essa opção, nada é cobrado: entram só as fotos reais e o que já está no cache em `outputs/<nome-da-aula>/imagens/`. O hook `Validar e gerar slides` roda sem `--aceitar-custo`, então salvar o arquivo nunca cobra. Cada imagem criada leva uns 10 s. Se aparecer **"Falta uma credencial AWS válida"**, não tente resolver sozinho: avise o professor (README, seção Imagens e custos) e gere sem `--aceitar-custo` enquanto isso.
6. **Olhe as prévias** em `outputs/<nome-da-aula>/slide_NN.png`. Se alguma imagem não combinar com o assunto, troque só aquela `imagem` (outras palavras-chave na `foto`, ou `gerar` no lugar, se o professor aceitar o custo) e gere de novo. Se um texto ficou pequeno demais, encurte-o.
7. **Responda ao professor** com:
   - quantos slides de conteúdo o deck tem e como ele está dividido;
   - o caminho do `.pptx` (editável no PowerPoint) e do PDF em `outputs/<nome-da-aula>/`;
   - quantas fotos reais entraram e quantas imagens foram criadas por IA, com o custo aproximado, ou por que o deck saiu sem imagens;
   - os avisos que você decidiu manter e por quê;
   - o que ele deve conferir: normas, valores técnicos, dados que você não tinha como confirmar (marcados com `[__]` ou "Dados ilustrativos") e se as imagens mostram o que o slide diz.

## Regras

- Português do Brasil, com acentuação correta.
- Não invente números de normas, valores técnicos ou estatísticas. Na dúvida, escreva de forma geral, use `[__]` ou "Dados ilustrativos" e avise no passo 7.
- Nenhum dado pessoal de aluno no deck.
- Nunca use `--aceitar-custo` sem o professor aprovar o valor. Cada mudança numa `imagem` com `gerar:` cria e cobra uma imagem nova: não reescreva descrições que já estão boas.
- Nunca peça, mostre ou grave a chave da AWS: ela fica só no `.env`, que o professor preenche.
- Se o validador acusar erro, não pule a validação: o gerador só monta decks sem erro.
