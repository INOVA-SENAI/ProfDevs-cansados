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
│   └── AGENTE_SLIDES_SENAI.md  # Regras, layouts, limites e ícones; prompt portátil para qualquer IA
├── senai_slides/           # Biblioteca
│   ├── validador.py        # Confere o deck YAML; CLI com --gerar
│   ├── gerador.py          # Roteiro, imagens e arquivos de saída
│   ├── tema.py             # Cores, fontes, ícones, peças do PowerPoint e slides fixos
│   ├── layouts.py          # Os 11 layouts de conteúdo e os gráficos
│   ├── diagrama.py         # Fundo do layout diagrama
│   ├── previa.py           # Prévia PNG e PDF a partir do .pptx
│   ├── imagens.py          # Imagens: fotos do Wikimedia Commons ou criadas na Amazon Bedrock, com cache
│   ├── icones.py           # Ícones Material Symbols permitidos
│   └── assets/             # Logos e fontes
├── slides/                 # Decks em YAML (um por aula); exemplo.yaml
├── scripts/
│   └── caca_segredos.py    # Procura chaves da AWS e da Bedrock (usado pelo hook)
├── outputs/                # Apresentações geradas (gitignored)
├── tests/                  # Testes automatizados (pytest)
├── LICENSES/               # Licença do código reaproveitado (teste-kiro, MIT)
├── .env.example            # Modelo do .env com a credencial da Bedrock (.env fica fora do git)
├── requirements.txt        # Instala o pacote (modo editável), pytest e ruff
├── pyproject.toml          # Pacote, pytest e ruff
└── README.md
```

## Descrição dos Diretórios

### `agente/`
O prompt do Agente de Slides SENAI. É o arquivo que o professor copia e cola em uma IA de chat. Contém as regras de conteúdo, o formato do deck, os layouts, os limites de texto, a lista de ícones e um exemplo, que é validado e gerado pelos testes.

### `senai_slides/`
Biblioteca Python. O `validador` confere o deck YAML; o `gerador` monta o roteiro (capa, agenda, divisórias, conteúdo e encerramento), busca ou cria as imagens e salva o `.pptx`, as prévias e o PDF. O desenho usa o `tema` e os `layouts`.

### `slides/`
Decks das aulas, em YAML, escritos pela IA ou pelo professor. Salvar um arquivo aqui dispara o hook que valida e gera. Nome em `snake_case` (ex.: `nr10_aula1.yaml`).

### `senai_slides/assets/`
Arquivos oficiais da identidade visual SENAI (logo SENAI, logo "Técnico DESI") e as fontes. Não editar: são a fonte de verdade da marca. A subpasta `.cache/` (gitignored) guarda ícones, logos e fundos preparados na primeira geração.

### `outputs/`
Apresentações geradas, em `outputs/<nome-da-aula>/`: `<nome-da-aula>.pptx`, `slide_01.png`, `slide_02.png`... e `<nome-da-aula>.pdf`. As imagens ficam em cache em `outputs/<nome-da-aula>/imagens/` (a imagem em `.jpg` e o crédito em `.json`), uma por `imagem` do deck; apagar essa pasta faz a próxima geração buscar e pagar por elas de novo. Não versionado.

### `tests/`
Testes do validador, da montagem de cada layout, da prévia, das imagens, do exemplo e dos ícones do agente, da skill, dos hooks e do caça-segredos.

## Convenções de Nomenclatura

### Arquivos
- `snake_case` para arquivos Python (ex: `layouts.py`, `test_agente.py`)

### Pastas
- lowercase, sem espaços (ex: `agente`, `senai_slides`, `outputs`)

### Branches Git
- `feature/nome-da-feature`, `fix/descricao-do-bug`
