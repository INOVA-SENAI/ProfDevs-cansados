---
name: gerador-slides
description: Gera apresentações de aula no padrão visual SENAI 2026, em PNG e PDF, escrevendo um deck em YAML que o validador confere e a biblioteca senai_slides desenha. Use quando pedirem slides, apresentação, aula em slides ou deck para uma turma do SENAI.
---

# Gerador de slides SENAI

Você escreve o **conteúdo** da aula em `slides/<nome>.yaml`. Quem desenha é a biblioteca `senai_slides`. Nunca escreva código de desenho, nunca edite `senai_slides/` nem `senai_slides/assets/`.

As regras de conteúdo, o formato do YAML e os limites de texto estão em `agente/AGENTE_SLIDES_SENAI.md`, seções 2, 3 e 4. Leia antes de escrever. O exemplo completo está em `slides/exemplo.yaml`.

## Passos

1. **Entenda o pedido.** Tema, curso ou turma e número de slides (padrão: de 8 a 12). Só pergunte antes de gerar se faltar o tema. Se o professor colar um trecho de apostila, use-o como fonte principal.
2. **Escreva o deck** em `slides/<nome>.yaml`, com `<nome>` em minúsculas e sem espaços (ex.: `slides/nr10_aula1.yaml`). Não sobrescreva um arquivo existente sem o professor pedir.
3. **Valide:** `python -m senai_slides.validador slides/<nome>.yaml`. Corrija todos os **erros** e rode de novo até passar. Leia os **avisos** e corrija os que fizerem sentido.
4. **Gere:** `python -m senai_slides.validador slides/<nome>.yaml --gerar`. Se o hook `Validar e gerar slides` estiver ativo, salvar o arquivo já gera sozinho.
5. **Responda ao professor** com:
   - quantos slides o deck tem e como ele está dividido;
   - o caminho do PDF em `outputs/<nome-da-aula>/`;
   - os avisos que você decidiu manter e por quê;
   - o que ele deve conferir: normas, valores técnicos e dados que você não tinha como confirmar.

## Regras

- Português do Brasil, com acentuação correta.
- Não invente números de normas, valores técnicos ou dados. Na dúvida, escreva de forma geral e avise no passo 5.
- Nenhum dado pessoal de aluno no deck.
- Se o validador acusar erro, não pule a validação: o gerador só desenha decks sem erro.
