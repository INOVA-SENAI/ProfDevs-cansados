---
inclusion: always
---

# Stack Tecnológica

> **Status:** Stack definida para o MVP do gerador de imagens de slide.

## Linguagens
<!-- Ex: TypeScript, Python, Go... -->
- Python

## Frontend
<!-- Ex: React 18, Vue 3, HTML/CSS/JS puro... -->
- Streamlit (app único: campo de prompt, botão de gerar, exibição e download da imagem)

## Backend
<!-- Ex: Node.js + Express, FastAPI, NestJS... -->
- Nenhum backend separado — a lógica (montagem de prompt e chamada à API de imagem) roda dentro do próprio app Streamlit

## Banco de Dados
<!-- Ex: PostgreSQL, MongoDB, SQLite... -->
- Nenhum (sem persistência de dados no MVP)

## Ferramentas de Build
<!-- Ex: Vite, Webpack, esbuild... -->
- Nenhuma (Python puro, sem etapa de build)

## Linting e Formatação
<!-- Ex: ESLint + Prettier, Biome... -->
- ruff

## Testes
<!-- Ex: Vitest, Jest, Playwright... -->
- pytest (cobrindo principalmente a lógica de montagem de prompt)

## Infraestrutura / Deploy
<!-- Ex: Vercel, Docker, AWS... -->
- Local para começar; Streamlit Community Cloud se precisar publicar

## Outras Dependências Relevantes
<!-- Liste pacotes ou libs importantes que o projeto usa -->
- `openai` (SDK para geração de imagem via gpt-image-1 / DALL-E 3)
- `python-dotenv` (leitura da chave de API a partir de variável de ambiente, nunca hardcoded)
- `Pillow` (sobreposição do logo oficial SENAI na imagem gerada pela IA)
