# ProfDevs-cansados

Gerador de imagens de slide no padrão visual do **SENAI 2026**. Você escreve um tema (ex.: "Introdução à eletricidade"), escolhe o tipo de slide e recebe uma imagem pronta em 16:9, gerada por IA e com a logo oficial do SENAI.

> **Status:** em desenvolvimento. A estrutura e as regras do projeto estão definidas, mas **o código ainda não foi escrito**.

## Como o projeto funciona

1. O usuário digita o tema e escolhe o tipo de slide: **Capa**, **Conteúdo** ou **Divisória**.
2. O sistema monta um prompt com as regras visuais do SENAI (cores, fonte, layout).
3. A API de imagem da OpenAI gera o slide, deixando vazio o lugar da logo.
4. O código cola a logo oficial por cima com a biblioteca Pillow, porque a IA deforma logotipos.
5. A imagem aparece na tela e pode ser baixada em PNG.

**Stack:** Python, Streamlit, OpenAI (geração de imagem), Pillow, pytest.

## Trabalhamos com o Kiro

O projeto é organizado para o [Kiro](https://kiro.dev). Antes de mexer em qualquer coisa, leia a pasta `.kiro/`:

| Arquivo | O que tem |
|---|---|
| [.kiro/steering/product.md](.kiro/steering/product.md) | Objetivo e público do produto |
| [.kiro/steering/tech.md](.kiro/steering/tech.md) | Stack e dependências |
| [.kiro/steering/structure.md](.kiro/steering/structure.md) | Pastas e convenções de nomes |
| [.kiro/steering/identidade-visual.md](.kiro/steering/identidade-visual.md) | Cores, fonte e layout de cada tipo de slide do SENAI |
| [.kiro/specs/geracao-slide.md](.kiro/specs/geracao-slide.md) | Spec da funcionalidade principal, com a lista de tarefas |

Os arquivos de `steering/` são lidos pelo Kiro em toda sessão. Se uma regra mudar, atualize o arquivo correspondente.

## MCP gerador de imagens (8bit / pixel art)

Em [mcp_imagem/](mcp_imagem/) está um servidor MCP que gera imagens em 8bit ou pixel art pela Amazon Bedrock, a partir de um texto ou de uma imagem sua. Ele já está registrado no Kiro ([.kiro/settings/mcp.json](.kiro/settings/mcp.json)) e no Claude Code ([.mcp.json](.mcp.json)), junto com o MCP de documentação oficial da AWS.

**Instalar em outra máquina ou por outro agente de IA:** siga o [guia de instalação em mcp_imagem/README.md](mcp_imagem/README.md). Ele tem os passos em ordem, os comandos de verificação, o registro em cada cliente MCP e a tabela de erros.

## Identidade visual

- Azul SENAI `#164193`, laranja `#E8490F` e verde `#52AE32` (só em detalhes)
- Fonte Century Gothic
- Os arquivos oficiais ficam em [assets/senai/](assets/senai/): logos, barra lateral e o PDF do modelo. **Não edite esses arquivos.**

## O que já está pronto

- Configuração do Kiro: produto, stack, estrutura, identidade visual e spec
- Pastas do projeto e `.gitignore`
- Logos e modelo oficial do SENAI em `assets/senai/`

## O que falta para finalizar

**1. Código** (tarefas da [spec](.kiro/specs/geracao-slide.md))
- [ ] `prompts/slide_prompt.py`: monta o prompt de cada tipo de slide
- [ ] `app/image_gen.py`: chama a API de imagem da OpenAI
- [ ] `app/logo_overlay.py`: ajusta a imagem para 16:9 (1920x1080) e cola a logo oficial
- [ ] `app/main.py`: tela em Streamlit (tema, tipo, botão de gerar, imagem e download)

**2. Configuração**
- [ ] `requirements.txt` com `streamlit`, `openai`, `python-dotenv`, `pillow`, `pytest` e `ruff`
- [ ] `.env.example` mostrando a variável `OPENAI_API_KEY`

**3. Recursos que precisamos conseguir**
- [ ] Uma **chave da API da OpenAI** com crédito. Sem ela nada é gerado.
- [ ] Opcional: uma versão da logo branca recortada e com fundo transparente, para a Capa

**4. Acabamento**
- [ ] Testes em `tests/` (montagem do prompt e colagem da logo)
- [ ] Instruções de instalação e uso neste README

## Pontos de atenção

- **Formato do slide:** a OpenAI não gera exatamente em 16:9. O tamanho mais próximo é 1536x1024, então o código precisa cortar e redimensionar para 1920x1080.
- **Texto dentro da imagem:** a IA pode errar letras nos textos do slide. É uma limitação conhecida.
- **Python no Windows:** use `python` ou `py`. O comando `python3` pode abrir a Microsoft Store em vez do Python instalado.
- **Chave da API:** nunca coloque a chave no código nem faça commit do `.env`. Ele já está no `.gitignore`.

## Como contribuir

- Crie uma branch no formato `feature/nome-da-feature` ou `fix/descricao-do-bug`.
- Pegue uma tarefa da [spec](.kiro/specs/geracao-slide.md) e marque como feita quando terminar.
- Arquivos Python em `snake_case`; pastas em minúsculas e sem espaços.
