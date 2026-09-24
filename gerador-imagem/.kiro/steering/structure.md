---
inclusion: always
---

# Estrutura de Pastas

## Visão Geral

```
gerador-imagem/
├── .kiro/              # Configurações e diretrizes do Kiro
│   ├── steering/       # Arquivos de contexto e padrões do projeto
│   ├── settings/       # mcp.json: MCPs do workspace
│   └── specs/          # Especificações de features
├── .mcp.json           # MCPs do projeto no Claude Code
├── senai/              # Logos oficiais, barra lateral e modelo PDF do SENAI
├── mcp_imagem/         # Servidor MCP de imagens 8bit/pixel art
└── README.md
```

O app de slides (spec `geracao-slide.md`) ainda não tem código. Quando for escrito, segue o mesmo padrão do `mcp_imagem/`: `app/`, `prompts/`, `tests/` e `outputs/`.

## Descrição dos Diretórios

### `senai/`
Arquivos oficiais da identidade visual SENAI (logos branco e azul, barra lateral, modelo de apresentação em PDF). Não editar — são a fonte de verdade da marca.

### `mcp_imagem/`
Servidor MCP independente do app de slides. Divide o código assim:
- `prompts/` monta o prompt; é uma função pura e testável;
- `app/` chama a IA e faz o pós-processamento com Pillow;
- `tests/` tem os testes (pytest);
- `outputs/` guarda as imagens geradas, fora do git.

`server.py` é o ponto de entrada. `assets/estilos/` guarda a imagem de referência de cada estilo, e é por ela que se troca o visual de um estilo. Tem `venv/`, `.env` e testes próprios. Rode tudo de dentro da pasta. Guia de instalação: `mcp_imagem/README.md`.

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
