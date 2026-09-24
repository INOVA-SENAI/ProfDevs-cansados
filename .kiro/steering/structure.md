---
inclusion: always
---

# Estrutura de Pastas

## Visão Geral

```
ProfDevs-cansados/
├── .kiro/                  # Configurações e diretrizes do Kiro
│   ├── steering/           # Arquivos de contexto e padrões do projeto
│   │   └── referencias/    # Imagens-modelo de layout (ex.: diagrama.png)
│   ├── skills/
│   │   └── gerador-slides/ # Skill que escreve o deck, valida e gera
│   ├── hooks/              # validar-slides.json e caca-segredos.json
│   └── specs/
│       └── gerador-slides/ # requirements.md, design.md, tasks.md
├── agente/
│   └── AGENTE_SLIDES_SENAI.md  # Regras e limites; prompt portátil para qualquer IA
├── senai_slides/           # Biblioteca
│   ├── validador.py        # Confere o deck YAML; CLI com --gerar
│   ├── gerador.py          # Deck validado -> chamadas da Apresentacao
│   ├── apresentacao.py     # Classe Apresentacao e desenho de cada tipo de slide
│   └── assets/             # Logos, barra lateral e modelo PDF oficiais do SENAI
├── slides/                 # Decks em YAML (um por aula); exemplo.yaml
├── scripts/
│   └── caca_segredos.py    # Procura chaves da AWS (usado pelo hook)
├── outputs/                # Slides gerados (gitignored)
├── tests/                  # Testes automatizados (pytest)
├── requirements.txt        # Instala o pacote (modo editável), pytest e ruff
├── pyproject.toml          # Pacote, pytest e ruff
└── README.md
```

## Descrição dos Diretórios

### `agente/`
O prompt do Agente de Slides SENAI. É o arquivo que o professor copia e cola em uma IA de chat. Ele contém a referência completa da biblioteca, os limites de texto e um exemplo, que é executado pelos testes.

### `senai_slides/`
Biblioteca Python. O `validador` confere o deck YAML e o `gerador` passa o conteúdo para a `Apresentacao`, que desenha cada slide com as medidas do modelo oficial, ajustando o tamanho da fonte para o texto caber.

### `slides/`
Decks das aulas, em YAML, escritos pela IA ou pelo professor. Salvar um arquivo aqui dispara o hook que valida e gera. Nome em `snake_case` (ex.: `nr10_aula1.yaml`).

### `senai_slides/assets/`
Arquivos oficiais da identidade visual SENAI (logo branco, logo azul, barra lateral e o modelo em PDF). Não editar: são a fonte de verdade da marca.

### `outputs/`
Slides gerados, em `outputs/<nome-da-aula>/`: `slide_01.png`, `slide_02.png`... e `<nome-da-aula>.pdf`. Não versionado.

### `tests/`
Testes da biblioteca, do validador, do exemplo do agente, da skill, dos hooks e do caça-segredos.

## Convenções de Nomenclatura

### Arquivos
<!-- Ex: kebab-case para arquivos, PascalCase para componentes... -->
- `snake_case` para arquivos Python (ex: `apresentacao.py`, `test_agente.py`)

### Pastas
<!-- Ex: lowercase, sem espaços... -->
- lowercase, sem espaços (ex: `agente`, `senai_slides`, `outputs`)

### Branches Git
<!-- Ex: feature/nome-da-feature, fix/descricao-do-bug... -->
- `feature/nome-da-feature`, `fix/descricao-do-bug`
