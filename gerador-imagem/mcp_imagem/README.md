# Gerador de imagem 8bit / pixel art (servidor MCP)

Servidor MCP em Python com uma única tool, `gerar_imagem`. Ela gera uma imagem em **8bit** ou **pixel art** a partir de um texto, ou redesenha nesse estilo uma imagem local. A IA é a Amazon Bedrock (Stability AI Image Services), e o Pillow garante a grade de pixels e a paleta. Roda localmente via stdio em qualquer cliente MCP: Claude Code, Kiro, Claude Desktop, Cursor, VS Code e outros.

> **Agente de IA:** siga as seções 1 a 6 em ordem. Os comandos partem desta pasta (`gerador-imagem/mcp_imagem/`), salvo quando indicado. Só três coisas exigem o humano, e estão marcadas com 🧑: a conta AWS, o aceite dos termos pagos e o login.

---

## 1. A tool

`gerar_imagem(prompt, estilo="pixelart", imagem_referencia=None)`

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `prompt` | string | sim | O que desenhar. Qualquer idioma; inglês costuma funcionar melhor |
| `estilo` | `"8bit"` ou `"pixelart"` | não | `8bit`: grade de 64 px e 16 cores. `pixelart`: grade de 128 px e 32 cores |
| `imagem_referencia` | string (caminho local) | não | Imagem para redesenhar no estilo. Deve ter pelo menos 64 px de lado e proporção entre 1:2,5 e 2,5:1 |

**Retorno:** a imagem PNG inline, de cerca de 1024×1024, mais o texto `Imagem salva em <caminho absoluto>`. O arquivo fica em `outputs/`.
**Erros:** voltam como resultado de erro da tool, com a mensagem em português (ver seção 7).
**Tempo e custo:** cerca de 10 s por imagem. US$ 0,07 sem referência (Style Guide) e US$ 0,08 com referência (Style Transfer), preços de set/2026.

---

## 2. Pré-requisitos

- Python **3.10 ou mais novo** (`python3 --version`; no Windows, `py --version`)
- 🧑 Uma **conta AWS** onde seja possível usar a Amazon Bedrock. Contas novas ganham de US$ 100 a 200 em créditos, e a Bedrock é elegível.
- Opcional: **AWS CLI 2.32 ou mais nova**, para ativar os modelos e fazer login pelo terminal (seção 4)

---

## 3. Instalar

macOS / Linux:

```bash
cd gerador-imagem/mcp_imagem
python3 -m venv venv
venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
```

Windows (PowerShell):

```powershell
cd gerador-imagem\mcp_imagem
py -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Confirme que a instalação funcionou. Os testes não chamam a AWS e não custam nada:

```bash
venv/bin/python -m pytest -q          # esperado: "6 passed"
```

No Windows, troque `venv/bin/python` por `venv\Scripts\python.exe` em todos os comandos deste arquivo.

---

## 4. Configurar a AWS

### 4.1 🧑 Ativar os modelos Stability (uma vez por conta)

Este passo aceita os termos do AWS Marketplace, com cobrança por uso e sem reembolso. **Peça a confirmação do humano antes.**

Pelo console: abra a Amazon Bedrock, região **us-east-1**, e ative o acesso a um dos *Stability AI Image Services*. Um acordo libera os 13 serviços.

Pela CLI, já autenticada como administrador da conta:

```bash
M=stability.stable-image-style-guide-v1:0
TOKEN=$(aws bedrock list-foundation-model-agreement-offers --model-id $M --region us-east-1 --query 'offers[0].offerToken' --output text)
aws bedrock create-foundation-model-agreement --model-id $M --offer-token "$TOKEN" --region us-east-1
# Aguarde até imprimir AVAILABLE (leva de 1 a 3 minutos):
aws bedrock get-foundation-model-availability --model-id $M --region us-east-1 --query 'agreementAvailability.status' --output text
```

### 4.2 Credenciais: escolha uma opção

O servidor lê `gerador-imagem/mcp_imagem/.env` sozinho, a partir do próprio caminho. Não é preciso passar variáveis no cliente MCP.

**Opção A: chave de API da Bedrock no `.env` (recomendada; dura até 1 ano)**

🧑 O humano gera a chave no console da Bedrock (*API keys* → *long-term*). Também dá para criar pela CLI um usuário IAM que **só** consegue gerar imagens nesses dois modelos, o que **exige a confirmação do humano**, porque cria um usuário e uma credencial na conta:

```bash
ACC=$(aws sts get-caller-identity --query Account --output text)
U=mcp-imagem-bedrock
aws iam create-user --user-name $U
aws iam put-user-policy --user-name $U --policy-name gerar-imagem-stability --policy-document "{
  \"Version\": \"2012-10-17\",
  \"Statement\": [
    {\"Effect\": \"Allow\", \"Action\": \"bedrock:InvokeModel\", \"Resource\": [
      \"arn:aws:bedrock:*:$ACC:inference-profile/us.stability.stable-image-style-guide-v1:0\",
      \"arn:aws:bedrock:*:$ACC:inference-profile/us.stability.stable-style-transfer-v1:0\",
      \"arn:aws:bedrock:*::foundation-model/stability.stable-image-style-guide-v1:0\",
      \"arn:aws:bedrock:*::foundation-model/stability.stable-style-transfer-v1:0\"]},
    {\"Effect\": \"Allow\", \"Action\": \"bedrock:CallWithBearerToken\", \"Resource\": \"*\"}
  ]}"
CHAVE=$(aws iam create-service-specific-credential --user-name $U --service-name bedrock.amazonaws.com --credential-age-days 365 --query 'ServiceSpecificCredential.ServiceCredentialSecret' --output text)
printf 'AWS_BEARER_TOKEN_BEDROCK=%s\nAWS_REGION=us-east-1\n' "$CHAVE" > .env && chmod 600 .env && unset CHAVE
```

Nunca imprima a chave nem faça commit do `.env`, que já está no `.gitignore`.

**Opção B: login do humano, sem chave**

Deixe `AWS_BEARER_TOKEN_BEDROCK` vazio no `.env` e rode `aws configure set region us-east-1 && aws login`. 🧑 O humano aprova no navegador. A sessão dura 12 h e o boto3 a renova sozinho. Depois disso, é preciso refazer o `aws login`.

---

## 5. Registrar no cliente MCP

Use **caminhos absolutos**. Descubra os dois caminhos de dentro de `gerador-imagem/mcp_imagem`:

```bash
echo "$PWD/venv/bin/python"   # PYTHON
echo "$PWD/server.py"         # SERVER
```

No Windows, o Python fica em `...\mcp_imagem\venv\Scripts\python.exe`.

| Cliente | Como registrar |
|---|---|
| **Claude Code** (todos os projetos) | `claude mcp add --scope user gerador-imagem -- PYTHON SERVER` |
| **Kiro** | Em `~/.kiro/settings/mcp.json` (todas as pastas) ou `.kiro/settings/mcp.json` (um workspace), com o bloco JSON abaixo |
| **Claude Desktop** | Em `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) ou `%APPDATA%\Claude\claude_desktop_config.json` (Windows), com o bloco JSON abaixo. Depois, reinicie o app |
| **Cursor** | Em `~/.cursor/mcp.json`, com o bloco JSON abaixo |
| **VS Code** (Copilot / agent mode) | Em `.vscode/mcp.json`, com o mesmo conteúdo, mas trocando a chave `mcpServers` por `servers` e acrescentando `"type": "stdio"` |

Bloco JSON. Ao editar um arquivo que já existe, **acrescente** a entrada dentro de `mcpServers` sem apagar as outras:

```json
{
  "mcpServers": {
    "gerador-imagem": {
      "command": "PYTHON",
      "args": ["SERVER"]
    }
  }
}
```

Este repositório já traz `gerador-imagem/.mcp.json` (Claude Code) e `gerador-imagem/.kiro/settings/mcp.json` (Kiro) com caminhos relativos. Eles valem quando `gerador-imagem/` é aberta como pasta do projeto.

Os clientes web (ChatGPT, claude.ai) só aceitam MCP remoto, por URL HTTPS. Este servidor roda localmente, então **não funciona** neles.

---

## 6. Verificar

**a) O servidor sobe e expõe a tool.** Não chama a AWS e não custa nada:

```bash
venv/bin/python - <<'EOF'
import asyncio
from pathlib import Path
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

async def main():
    py = Path("venv/bin/python").absolute()  # não use resolve(): ele sai do venv
    params = StdioServerParameters(command=str(py), args=[str(Path("server.py").resolve())])
    async with Client(params) as c:
        print([t.name for t in (await c.list_tools()).tools])

asyncio.run(main())
EOF
# esperado: ['gerar_imagem']
```

**b) Geração real.** Custa cerca de US$ 0,07; peça a confirmação do humano. Depois de reiniciar o cliente MCP, chame a tool:

> Use a tool gerar_imagem com prompt "um robô regando plantas" e estilo "8bit".

O esperado é uma imagem e a mensagem `Imagem salva em .../outputs/8bit-<data>.png`.

---

## 7. Erros comuns

| Mensagem (começo) | Causa | Solução |
|---|---|---|
| `Não foi possível chamar a Bedrock: Unable to locate credentials` | Sem credencial | Seção 4.2 |
| `A Bedrock recusou o pedido (AccessDeniedException): Your account is currently being verified` | Conta AWS nova ainda em verificação | Aguardar; costuma levar até 2 h |
| `A Bedrock recusou o pedido (AccessDeniedException)` (outros casos) | Modelos não ativados, ou chave sem permissão | Seções 4.1 e 4.2 |
| `A Bedrock recusou o pedido (ThrottlingException)` | Muitas chamadas seguidas | Esperar alguns segundos e tentar de novo |
| `A Bedrock não devolveu imagem (motivo: Filter reason: ...)` | Filtro de conteúdo da Stability | Reformular o prompt ou trocar a imagem |
| `Não foi possível abrir a imagem de referência` / `não é uma imagem válida` | Caminho errado ou arquivo que não é imagem | Passar o caminho absoluto de um PNG, JPEG ou WebP |
| `precisa ter pelo menos 64 px` / `proporção ... entre 1:2,5 e 2,5:1` | Imagem fora dos limites da Bedrock | Recortar ou redimensionar a imagem |
| O cliente não lista a tool | Caminho relativo ou cliente não reiniciado | Usar caminhos absolutos (seção 5) e reiniciar o cliente |

---

## 8. Como funciona e como alterar

```
mcp_imagem/
├── server.py                 # tool MCP: valida a entrada, orquestra e salva o PNG
├── prompts/estilo_prompt.py  # estilos (Estilo, ESTILOS) e montagem do prompt; função pura
├── app/image_gen.py          # única parte que fala com a Bedrock (Style Guide / Style Transfer)
├── app/pixel_grid.py         # Pillow: grade de pixels uniforme e paleta limitada
├── assets/estilos/           # imagem de referência de cada estilo (8bit.png, pixelart.png)
├── tests/                    # pytest, sem chamar a AWS
└── outputs/                  # imagens geradas (fora do git)
```

- **Mudar o visual de um estilo:** troque o PNG em `assets/estilos/`. Qualquer pixel art com pelo menos 64 px de lado serve.
- **Ajustar um estilo:** em `prompts/estilo_prompt.py`, `fidelidade` vai de 0 a 1 e controla o quanto a imagem copia a referência. Valores altos ignoram o prompt. `pixels` e `cores` controlam a grade e a paleta.
- **Criar um estilo novo:** acrescente o nome em `Estilo`, uma entrada em `ESTILOS` e o PNG `assets/estilos/<nome>.png`. O teste `test_todo_estilo_do_schema_tem_preset_e_imagem_de_referencia` confere que as três partes existem.
- **Lint:** `venv/bin/ruff check . && venv/bin/ruff format --check .`

### Por que Bedrock + Stability (pesquisa de 24/09/2026)

- **Gemini:** nenhum modelo de imagem tem free tier na API ([pricing](https://ai.google.dev/gemini-api/docs/pricing)).
- **Nova Canvas:** está em Legacy, com fim de vida em 30/09/2026, e não aceita clientes novos ([model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-canvas.html)).
- **Stable Image Core e SD3.5:** saíram da Bedrock.
- **Style Guide e Style Transfer:** estão Active, e o Style Guide aceita `style_preset: "pixel-art"` ([parâmetros](https://docs.aws.amazon.com/bedrock/latest/userguide/stable-image-services.html)).
