---
inclusion: always
---

# Stack Tecnológica

> **Status:** Stack definida. A IA escreve o conteúdo em um deck YAML, o validador confere e a biblioteca `senai_slides` monta um `.pptx` editável no modelo SENAI 2026. As APIs externas são o Wikimedia Commons (fotos reais, sem chave nem custo) e a Amazon Bedrock (imagens criadas por IA).

## Linguagens
- Python 3.10 ou mais novo

## Frontend
- Nenhum. A interface é o chat do Kiro (skill `gerador-slides`) ou a IA de chat escolhida pelo professor, usando o prompt de `agente/AGENTE_SLIDES_SENAI.md`.

## Backend
- Nenhum servidor próprio. A biblioteca `senai_slides` roda localmente, na máquina do professor.
- Montagem do `.pptx`: portada do gerador de slides do repositório icrcode/teste-kiro (licença MIT, `LICENSES/teste-kiro.txt`).
- Fotos reais: API do Wikimedia Commons (`action=query`, busca em arquivos), com `urllib`, sem chave. Só entram fotos JPEG ou PNG com 800 px ou mais de lado e licença CC0, domínio público, CC BY ou CC BY-SA; o crédito vai no slide.
- Imagens criadas: Amazon Bedrock, Stability AI Style Guide (`us.stability.stable-image-style-guide-v1:0`) com `style_preset: photographic`, fidelidade 0,1 e uma referência de estilo neutra gerada pelo código (degradê de luz, sem pessoas), chamado com `boto3`. É o gerador de imagens da branch `prof/joao-borges`. Cerca de US$ 0,07 e 10 s por imagem.
- Cache das duas em `outputs/<aula>/imagens/`.

## Banco de Dados
- Nenhum

## Ferramentas de Build
- setuptools (via `pyproject.toml`); instalação com `pip install -r requirements.txt`, que instala o pacote em modo editável

## Linting e Formatação
- ruff (`ruff check .` e `ruff format .`)

## Testes
- pytest: validador, montagem de todos os layouts, prévia, imagens, exemplo do prompt do agente, lista de ícones do prompt, skill e hooks do Kiro e caça-segredos

## Infraestrutura / Deploy
- Nenhuma. Cada professor clona o repositório e roda localmente.
- Conta AWS com os modelos da Stability AI ativos em us-east-1 (README, seção Imagens e custos).

## Outras Dependências Relevantes
- `python-pptx` e `lxml`: montam o `.pptx`, com transições e animações
- `matplotlib` e `numpy`: gráficos em alta resolução, na fonte Open Sans
- `Pillow`: ícones, logos, fundos, recorte das imagens, prévia PNG e PDF
- `PyYAML`: lê o deck (`yaml.safe_load`, nunca `yaml.load`)
- `boto3[crt]`: chama a Amazon Bedrock (o `[crt]` permite usar o `aws login`)
- `python-dotenv`: lê a credencial `AWS_BEARER_TOKEN_BEDROCK` do `.env`
- Fontes em `senai_slides/assets/fonts/`: Open Sans e uma versão reduzida do Material Symbols Rounded, só com os ícones de `icones.py`. Para acrescentar um ícone, gere a fonte de novo a partir do arquivo completo do Google com o `fontTools`

## Regra para mudanças no formato ou nos limites
Qualquer mudança nos layouts, nos campos do deck, nos limites de `senai_slides/validador.py` ou na lista de `senai_slides/icones.py` DEVE ser refletida em `agente/AGENTE_SLIDES_SENAI.md`, que é a referência da skill e do prompt portátil. Os testes falham se o exemplo ou a lista de ícones do prompt divergirem do código.

## Comandos
- Validar: `python -m senai_slides.validador slides/<nome>.yaml`
- Validar e gerar: `python -m senai_slides.validador slides/<nome>.yaml --gerar`. Mostra quantas imagens faltam e quanto custam, e só usa as fotos reais (grátis) e o cache
- Gerar criando as imagens por IA (cobradas), depois de o professor aprovar o custo: `... --gerar --aceitar-custo`
- Gerar sem nenhuma imagem, nem as do cache (sem internet): `... --gerar --sem-imagens`
- Não instalar a Open Sans no Windows: `... --gerar --sem-instalar-fontes`
- Procurar segredos: `python scripts/caca_segredos.py`

## Credenciais e testes
- A credencial da Bedrock fica só no `.env` (fora do git). Nunca no código, no deck, no chat ou em log.
- Nada é cobrado sem `--aceitar-custo`. O hook não usa essa opção, e a skill e o agente perguntam ao professor sobre as imagens, com a estimativa de custo, antes de escrever o deck.
- Nenhum teste chama a AWS nem a internet: `tests/conftest.py` troca a Bedrock e o Wikimedia Commons por versões falsas em todos os testes.
