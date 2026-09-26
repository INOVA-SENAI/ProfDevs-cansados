# Implementation Plan: Gerador de slides SENAI

## Overview

Tasks em ondas: cada onda depende da anterior; as tasks dentro de uma onda são independentes e podem rodar em paralelo (Run all Tasks). As ondas 1 a 5 construíram a primeira versão (PNG e PDF desenhados pelo Pillow); a onda 6 trocou a montagem pelo `.pptx` do teste-kiro, mantendo o validador, o agente, o diagrama e as imagens.

## Tasks

### Onda 1

- [x] 1. Ler e checar o YAML
  - `validar_arquivo` em `senai_slides/validador.py`: YAML quebrado com número de linha, arquivo fora de UTF-8, campos do deck
  - _Requisitos: 1.1–1.3_

### Onda 2

- [x] 2. Limites de texto; espaços repetidos não contam; teste de pior caso
  - _Requisitos: 2.1–2.5_
- [x] 3. Limite de 20 slides de conteúdo
  - _Requisitos: 3.1_
- [x] 4. Gerador e opção `--gerar`, que só gera deck sem erro
  - _Requisitos: 4.1, 4.3, 4.4_

### Onda 3

- [x] 5. Avisos de conteúdo e testes
  - _Requisitos: 5.1_
- [x] 6. Skill `gerador-slides` (`.kiro/skills/gerador-slides/SKILL.md`)
  - _Requisitos: 7.1–7.3_
- [x] 7. Hooks `validar-slides.json` e `caca-segredos.json` + `scripts/caca_segredos.py`
  - _Requisitos: 8.1–8.3_
- [x] 8. Agente portátil em YAML, com exemplo igual a `slides/exemplo.yaml`
  - _Requisitos: 9.1–9.2_

### Onda 4

- [x] 9. Layout `diagrama`, no modelo de `.kiro/steering/referencias/diagrama.png`
  - _Requisitos: 10.1–10.2_

### Onda 5

- [x] 10. Ilustrações pelo gerador de imagens da branch `prof/joao-borges`
  - `senai_slides/imagens.py`: Style Guide, grade de pixels, erros em português, `.env`, cache, 2 chamadas em paralelo, retentativa adaptativa, `--sem-imagens`
  - Caça-segredos acusa chave da Bedrock; Bedrock falsa em `tests/conftest.py`
  - _Requisitos: 8.2, 11.1–11.7_

### Onda 6

- [x] 11. Montagem em `.pptx` com o gerador do repositório icrcode/teste-kiro (MIT)
  - `tema.py` (paleta, fontes, ícones, peças, capa, agenda, divisória, encerramento) e `layouts.py` (9 layouts e gráficos), portados e sem o estado global do `pyplot`
  - Ajuste de texto próprio (`tamanho_que_cabe`), no lugar do `fit_text` do python-pptx
  - Fonte de ícones reduzida para os ícones de `icones.py`
  - _Requisitos: 2.5, 3.1–3.3, 4.1–4.2_
- [x] 12. Layouts deste projeto no `.pptx`
  - `ilustracao` (itens e imagem da Bedrock) e `diagrama` (fundo em imagem, textos e ícones editáveis); imagem na capa; logo do curso opcional
  - _Requisitos: 10.1–10.3, 11.1, 11.5_
- [x] 13. Validador do formato novo
  - Campos por layout, quantidade de itens, limites por modo, ícones com sugestão, gráficos, tabelas, seções, formato antigo, avisos
  - _Requisitos: 1.1–1.7, 2.1–2.4, 3.3, 5.1, 6.1_
- [x] 14. Prévia e PDF a partir do `.pptx` (`previa.py`)
  - _Requisitos: 4.1_
- [x] 15. Agente, skill, README, steering e spec no formato novo; contexto de criação do teste-kiro (níveis, variedade de layouts, dados com fonte) no prompt; lista de ícones testada
  - _Requisitos: 6.2, 7.2–7.3, 9.1–9.3_
- [x] 16. Conversão dos decks de `slides/` para o formato novo, mantendo o `nome` (e o cache de imagens)
  - _Requisitos: 1.7_

### Onda 7

- [x] 17. Imagens realistas no lugar da pixel art
  - `imagem: {foto: ...}` (Wikimedia Commons, com crédito) ou `{gerar: ...}` (Bedrock, `photographic`, legenda de IA); reserva por IA quando não há foto livre
  - Sai a colagem com fotos de alunos do modelo do teste-kiro; fundo azul em degradê
  - _Requisitos: 4.2, 11.1–11.2a_

### Onda 8

- [x] 18. Perguntar sobre as imagens e mostrar o custo
  - Skill e agente perguntam, antes de escrever, se o professor quer imagens, com a estimativa (US$ 0,07 por imagem criada)
  - Validador mostra `Imagens: ...` por deck; imagem por IA só com `--aceitar-custo` (o hook não usa); campo `imagens: false`
  - _Requisitos: 11.8–11.11_

## Task Dependency Graph

```json
{
  "waves": [
    {"wave": 1, "tasks": ["1"]},
    {"wave": 2, "tasks": ["2", "3", "4"]},
    {"wave": 3, "tasks": ["5", "6", "7", "8"]},
    {"wave": 4, "tasks": ["9"]},
    {"wave": 5, "tasks": ["10"]},
    {"wave": 6, "tasks": ["11"]},
    {"wave": 7, "tasks": ["12", "13", "14"]},
    {"wave": 8, "tasks": ["15", "16"]},
    {"wave": 9, "tasks": ["17"]},
    {"wave": 10, "tasks": ["18"]}
  ]
}
```

## Notes

Pendente:

- [ ] Testar a skill no Kiro com um pedido real ("Gere uma aula de 8 slides sobre NR-12")
- [ ] Testar o prompt portátil em duas IAs de chat diferentes
- [ ] Revisar os ícones dos decks convertidos (receberam ícones genéricos)
- [ ] Gráficos nativos do PowerPoint
- [ ] Desafio extra: caça-segredos como pre-commit do Git
