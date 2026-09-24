---
inclusion: always
---

# Stack Tecnológica

> **Status:** Stack definida. Sem API externa e sem IA de imagem: a IA escreve o conteúdo em um deck YAML, o validador confere e a biblioteca `senai_slides` desenha os slides.

## Linguagens
<!-- Ex: TypeScript, Python, Go... -->
- Python 3.10 ou mais novo

## Frontend
<!-- Ex: React 18, Vue 3, HTML/CSS/JS puro... -->
- Nenhum. A interface é o chat do Kiro (skill `gerador-slides`) ou a IA de chat escolhida pelo professor, usando o prompt de `agente/AGENTE_SLIDES_SENAI.md`.

## Backend
<!-- Ex: Node.js + Express, FastAPI, NestJS... -->
- Nenhum. A biblioteca `senai_slides` roda localmente, na máquina do professor.

## Banco de Dados
<!-- Ex: PostgreSQL, MongoDB, SQLite... -->
- Nenhum

## Ferramentas de Build
<!-- Ex: Vite, Webpack, esbuild... -->
- setuptools (via `pyproject.toml`); instalação com `pip install -r requirements.txt`, que instala o pacote em modo editável

## Linting e Formatação
<!-- Ex: ESLint + Prettier, Biome... -->
- ruff (`ruff check .` e `ruff format .`)

## Testes
<!-- Ex: Vitest, Jest, Playwright... -->
- pytest, incluindo testes que validam e geram o exemplo do prompt do agente, conferem a skill e os hooks do Kiro e rodam o caça-segredos no repositório

## Infraestrutura / Deploy
<!-- Ex: Vercel, Docker, AWS... -->
- Nenhuma. Cada professor clona o repositório e roda localmente.

## Outras Dependências Relevantes
<!-- Liste pacotes ou libs importantes que o projeto usa -->
- `Pillow`: desenha os slides e gera PNG e PDF
- `PyYAML`: lê o deck (`yaml.safe_load`, nunca `yaml.load`)
- Fonte Century Gothic (já vem com o Windows/Office). Sem ela, a biblioteca usa Arial ou DejaVu Sans automaticamente.

## Regra para mudanças no formato ou nos limites
Qualquer mudança nos tipos de slide, nos campos do deck ou nos limites de `senai_slides/validador.py` DEVE ser refletida em `agente/AGENTE_SLIDES_SENAI.md`, que é a referência da skill e do prompt portátil.

## Comandos
- Validar: `python -m senai_slides.validador slides/<nome>.yaml`
- Validar e gerar: `python -m senai_slides.validador slides/<nome>.yaml --gerar`
- Procurar segredos: `python scripts/caca_segredos.py`
