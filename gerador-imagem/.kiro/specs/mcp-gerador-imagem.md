# Spec: MCP Gerador de Imagem por Tipo

---

## Overview

Um servidor MCP em Python expõe a tool `gerar_imagem`. Ela gera uma imagem em um estilo fixo (`8bit` ou `pixelart`) a partir de um texto, ou redesenha nesse estilo uma imagem enviada pelo usuário. Funciona no Kiro, no Claude Code ou em qualquer cliente MCP.

**Problema que resolve:**
Professores e alunos querem ilustrações no estilo retrô para aulas e slides direto do assistente de IA, sem abrir uma ferramenta de design.

**Solução proposta:**
Servidor MCP em `mcp_imagem/` que segue o padrão do gerador de slides. O prompt é montado em `prompts/`, a chamada à IA fica em `app/image_gen.py` e o pós-processamento com Pillow em `app/pixel_grid.py`. A IA é a Amazon Bedrock (Stability AI Image Services).

---

## Requirements

### Funcionais
- [x] RF01 - O usuário DEVE informar um prompt de texto
- [x] RF02 - O usuário PODE escolher o `tipo` de imagem (`8bit`, que é o padrão, ou `pixelart`), exposto como enum no schema da tool; novos tipos entram cadastrando um preset e uma imagem de referência
- [x] RF02b - O usuário PODE informar um `contexto` (onde ou para que a imagem será usada), que entra no prompt
- [x] RF03 - O usuário PODE enviar o caminho de uma imagem local para redesenhar no tipo escolhido
- [x] RF08 - **Obrigatório:** a imagem final DEVE ser PNG com fundo transparente (Remove Background da Stability e alfa binário no Pillow)
- [x] RF04 - Sem imagem de referência, o sistema DEVE usar o Style Guide com a imagem de estilo de `mcp_imagem/assets/estilos/`
- [x] RF05 - Com imagem de referência, o sistema DEVE usar o Style Transfer
- [x] RF06 - O sistema DEVE aplicar por código uma grade de pixels uniforme e uma paleta limitada (16 cores no `8bit`, 32 no `pixelart`)
- [x] RF07 - O sistema DEVE devolver a imagem inline e salvar o PNG em `mcp_imagem/outputs/`

### Não-funcionais
- [x] RNF01 - As credenciais AWS DEVEM vir do `.env` (`AWS_BEARER_TOKEN_BEDROCK`) ou da cadeia padrão da AWS, nunca do código
- [x] RNF02 - Erros de entrada e da Bedrock DEVEM chegar ao cliente como mensagem simples em português (`ToolError`), sem derrubar o servidor
- [x] RNF03 - A imagem de referência DEVE ser validada antes do envio: arquivo de imagem real, lado mínimo de 64 px, proporção entre 1:2,5 e 2,5:1, no máximo 2048 px

### Fora de escopo
- Hospedar o servidor na AWS (AgentCore Runtime) e guardar as imagens no S3. Fica para quando houver uso remoto.
- Tipos além de `8bit` e `pixelart` (a estrutura já permite cadastrá-los)
- Escolher a proporção da imagem (o padrão é 1:1)

---

## Tasks

- [x] **Task 1:** `prompts/tipo_prompt.py` com `Tipo`, `TIPOS` e `montar_prompt(prompt, tipo, contexto)`
- [x] **Task 2:** `app/image_gen.py`: Style Guide ou Style Transfer via `boto3` `invoke_model`
- [x] **Task 3:** `app/pixel_grid.py`: grade de pixels e paleta com Pillow
- [x] **Task 4:** `server.py`: tool MCP, validação da referência, conversão de erros para `ToolError`
- [x] **Task 5:** Imagens de estilo em `assets/estilos/`, desenhadas por código, sem arte de terceiros
- [x] **Task 6:** Testes de montagem do prompt e da grade de pixels
- [x] **Task 7:** Registro em `.kiro/settings/mcp.json` e `.mcp.json`
- [x] **Task 8:** Primeira chamada real à Bedrock (24/09/2026, ~10 s por imagem). A `fidelidade` baixou de 0,8/0,6 para 0,5/0,4 porque o modelo recopiava a cena de referência
- [ ] **Task 9:** Validar a nova `fidelidade` e testar o Style Transfer com uma foto real

---

## Notas de Design

Pesquisa feita em 24/09/2026 nas documentações oficiais, com o MCP de documentação da AWS:

- **Gemini:** nenhum modelo de imagem tem free tier na API. O mais barato é o `gemini-3.1-flash-lite-image`, a cerca de US$ 0,034 por imagem, e exige billing. Por isso a IA saiu da Gemini.
- **Nova Canvas:** está em Legacy, com fim de vida em 30/09/2026. Modelos em Legacy não aceitam clientes novos.
- **Stable Image Core e SD3.5 Large:** os model cards não existem mais na Bedrock.
- **Stability Style Guide e Style Transfer:** estão Active em us-east-1, us-east-2 e us-west-2. O Style Guide aceita `style_preset: "pixel-art"`. Usamos o perfil `us.` de inferência entre regiões.
- **Custo:** contas AWS novas recebem de US$ 100 a 200 em créditos, e a Bedrock é elegível.
- **Grade de pixels por código:** modelos de imagem desenham "pixel art" com pixels irregulares e bordas borradas. Mesmo princípio do logo: o que a IA faz mal, o código garante.
- **SDK de MCP:** `mcp` 2.x. O `FastMCP` virou `MCPServer`. Só `ToolError` expõe a mensagem de erro ao cliente; outras exceções chegam como erro genérico.

---

## Critérios de Aceite

- [x] O schema da tool expõe `tipo` (enum `8bit` / `pixelart`, padrão `8bit`) e `contexto`
- [x] PNG RGBA com fundo transparente e alfa binário: nos testes reais de 24/09/2026, os cantos saíram transparentes, com 62% e 68% da área transparente
- [x] Sem referência, a chamada vai para o Style Guide com `style_preset` `pixel-art`; com referência, vai para o Style Transfer (teste ponta a ponta com a Bedrock simulada)
- [x] A imagem final tem blocos de pixel uniformes e no máximo N cores
- [x] Caminho inválido, arquivo que não é imagem, prompt vazio e falta de credenciais retornam mensagem clara
- [x] Uma imagem real gerada pela Bedrock em cada estilo, revisada visualmente
- [ ] Revisão visual depois da nova calibragem e do Style Transfer com foto real
