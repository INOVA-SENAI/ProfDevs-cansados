---
inclusion: always
---

# Estrutura de Pastas

## Visão Geral

```
ProfDevs-cansados/
├── .kiro/              # Configurações e diretrizes do Kiro
│   ├── steering/       # Arquivos de contexto e padrões do projeto
│   ├── hooks/          # Automações e gatilhos do agente
│   └── specs/          # Especificações de features
├── assets/senai/       # Logos oficiais, barra lateral e modelo PDF do SENAI
├── app/                # App Streamlit (main.py, chamada à API de imagem)
├── prompts/            # Módulo que monta o prompt padronizado de "slide"
├── outputs/            # Imagens geradas (gitignored)
├── tests/              # Testes automatizados (pytest)
└── README.md
```

## Descrição dos Diretórios

### `assets/senai/`
Arquivos oficiais da identidade visual SENAI (logos branco e azul, barra lateral, modelo de apresentação em PDF). Não editar — são a fonte de verdade da marca.

### `app/`
Código do app Streamlit: interface (campo de prompt, botão de gerar, exibição e download) e integração com a API de geração de imagem.

### `prompts/`
Lógica de montagem do prompt final enviado à IA de imagem, incluindo as instruções fixas de formato (proporção 16:9, layout com título e conteúdo).

### `outputs/`
Imagens geradas pelos usuários. Não versionado (ver `.gitignore`).

### `tests/`
Testes automatizados, principalmente da lógica de montagem de prompt em `prompts/`.

## Convenções de Nomenclatura

### Arquivos
<!-- Ex: kebab-case para arquivos, PascalCase para componentes... -->
- `snake_case` para arquivos Python (ex: `image_gen.py`, `slide_prompt.py`)

### Pastas
<!-- Ex: lowercase, sem espaços... -->
- lowercase, sem espaços (ex: `app`, `prompts`, `outputs`)

### Branches Git
<!-- Ex: feature/nome-da-feature, fix/descricao-do-bug... -->
- `feature/nome-da-feature`, `fix/descricao-do-bug`
