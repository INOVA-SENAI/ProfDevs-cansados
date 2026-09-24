# Gerador de imagem 8bit / pixel art (servidor MCP)

Servidor MCP em Python com uma única tool, `gerar_imagem`. Ela gera um **PNG com fundo transparente** do tipo escolhido (hoje, **8bit** ou **pixel art**), a partir de um texto e de um contexto de uso, ou redesenha nesse tipo uma imagem local. A IA é a Amazon Bedrock (Stability AI Image Services), que gera a imagem e remove o fundo. O Pillow garante a grade de pixels, a paleta e a transparência sem bordas borradas. Roda localmente via stdio em qualquer cliente MCP: Claude Code, Kiro, Claude Desktop, Cursor, VS Code e outros.

> **Agente de IA:** siga as seções 1 a 6 em ordem. Os comandos partem desta pasta (`gerador-imagem/mcp_imagem/`), salvo quando indicado. Só três coisas exigem o humano, e estão marcadas com 🧑: a conta AWS, o aceite dos termos pagos e a credencial.
>
> **Toda instalação precisa de uma credencial AWS.** Cada imagem é cobrada na conta AWS dona da credencial, e a chave nunca fica no repositório. Sem ela, o servidor instala e lista a tool normalmente, mas toda geração responde `Falta uma credencial AWS válida`. Nesse caso, siga a seção 4.2. **Nunca peça nem aceite a chave pelo chat.**

---

## 1. A tool

`gerar_imagem(prompt, tipo="8bit", contexto=None, imagem_referencia=None)`

| Parâmetro | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `prompt` | string | sim | O que desenhar. Qualquer idioma; inglês costuma funcionar melhor |
| `tipo` | `"8bit"` ou `"pixelart"` | não (padrão `8bit`) | Tipo de imagem a criar. `8bit`: grade de 64 px e 16 cores. `pixelart`: grade de 128 px e 32 cores. A lista cresce conforme novos tipos são cadastrados (seção 8) |
| `contexto` | string | não | Onde ou para que a imagem será usada, ex.: `"ícone para slide de aula sobre eletricidade"`. Entra no prompt e orienta composição e detalhes |
| `imagem_referencia` | string (caminho local) | não | Imagem para redesenhar no tipo escolhido. Deve ter pelo menos 64 px de lado e proporção entre 1:2,5 e 2,5:1 |

**Retorno:** um PNG RGBA de cerca de 1024×1024, com **fundo transparente** (cada pixel é 100% opaco ou 100% transparente) e um único objeto centralizado. Vem inline, junto com o texto `PNG com fundo transparente salvo em <caminho absoluto>`. O arquivo fica em `outputs/`.
**Erros:** voltam como resultado de erro da tool, com a mensagem em português (ver seção 7).
**Tempo e custo:** de 10 a 15 s por imagem. Cada imagem faz duas chamadas pagas: a geração (US$ 0,07 no Style Guide, ou US$ 0,08 no Style Transfer, quando há referência) e a remoção de fundo (US$ 0,07). O total fica em **cerca de US$ 0,14 a 0,15 por imagem** (preços de set/2026).

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

🧑 O humano gera a chave no console da Bedrock (*API keys* → *long-term*). Também dá para criar pela CLI um usuário IAM que **só** consegue usar os três modelos do gerador (Style Guide, Style Transfer e Remove Background), o que **exige a confirmação do humano**, porque cria um usuário e uma credencial na conta:

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
      \"arn:aws:bedrock:*:$ACC:inference-profile/us.stability.stable-image-remove-background-v1:0\",
      \"arn:aws:bedrock:*::foundation-model/stability.stable-image-style-guide-v1:0\",
      \"arn:aws:bedrock:*::foundation-model/stability.stable-style-transfer-v1:0\",
      \"arn:aws:bedrock:*::foundation-model/stability.stable-image-remove-background-v1:0\"]},
    {\"Effect\": \"Allow\", \"Action\": \"bedrock:CallWithBearerToken\", \"Resource\": \"*\"}
  ]}"
CHAVE=$(aws iam create-service-specific-credential --user-name $U --service-name bedrock.amazonaws.com --credential-age-days 365 --query 'ServiceSpecificCredential.ServiceCredentialSecret' --output text)
printf 'AWS_BEARER_TOKEN_BEDROCK=%s\nAWS_REGION=us-east-1\n' "$CHAVE" > .env && chmod 600 .env && unset CHAVE
```

Se a chave já existe, o humano a cola no `.env`: tira o `#` da linha `AWS_BEARER_TOKEN_BEDROCK=` e preenche. Nunca imprima a chave nem faça commit do `.env`, que já está no `.gitignore`.

**Opção B: login do humano, sem chave**

Mantenha a linha `AWS_BEARER_TOKEN_BEDROCK` comentada no `.env` e rode `aws configure set region us-east-1 && aws login`. 🧑 O humano aprova no navegador. A sessão dura 12 h e o boto3 a renova sozinho. Depois disso, é preciso refazer o `aws login`.

**Opção C: agente em ambiente na nuvem ou container** (Claude Code na web, Codespaces, CI)

Nesses ambientes não dá para rodar o `aws login`, e o container some ao fim da sessão.

1. 🧑 O humano cadastra a chave como variável de ambiente `AWS_BEARER_TOKEN_BEDROCK` nas configurações do ambiente. No Claude Code na web, o caminho é: menu do ambiente → *Edit* → variáveis de ambiente. Depois disso, abre uma sessão nova.
2. O agente grava a chave no `.env`, sem exibi-la. Assim o servidor a encontra seja qual for o cliente MCP:

```bash
[ -n "$AWS_BEARER_TOKEN_BEDROCK" ] && printf 'AWS_BEARER_TOKEN_BEDROCK=%s\nAWS_REGION=us-east-1\n' "$AWS_BEARER_TOKEN_BEDROCK" > .env && chmod 600 .env && echo "chave gravada" || echo "AWS_BEARER_TOKEN_BEDROCK não está no ambiente: peça ao humano (passo 1)"
```

**Como o servidor escolhe a credencial:** usa a variável de ambiente, se estiver preenchida. Se não estiver, usa o `.env`. Se nenhum dos dois tiver chave, cai no `aws login` ou no perfil padrão da AWS. Valores vazios são ignorados.

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

A chave AWS não precisa aparecer aqui, porque o servidor lê o `.env` pelo próprio caminho. Se o ambiente usa proxy e o cliente não repassa essas variáveis, acrescente à entrada `"env": {"HTTPS_PROXY": "...", "SSL_CERT_FILE": "..."}` com os valores do ambiente.

Este repositório já traz `gerador-imagem/.mcp.json` (Claude Code) e `gerador-imagem/.kiro/settings/mcp.json` (Kiro) com caminhos relativos. Eles valem quando `gerador-imagem/` é aberta como pasta do projeto.

Os clientes web (ChatGPT, claude.ai) só aceitam MCP remoto, por URL HTTPS. Este servidor roda localmente, então **não funciona** neles.

---

## 6. Verificar

**a) O servidor sobe e expõe a tool.** Não chama a AWS e não custa nada:

```bash
venv/bin/python - <<'EOF'
import asyncio, os
from pathlib import Path
from mcp.client import Client
from mcp.client.stdio import StdioServerParameters

async def main():
    py = Path("venv/bin/python").absolute()  # não use resolve(): ele sai do venv
    params = StdioServerParameters(
        command=str(py),
        args=[str(Path("server.py").resolve())],
        env=dict(os.environ),  # sem isto, proxy e certificados do ambiente não chegam ao servidor
    )
    async with Client(params) as c:
        print([t.name for t in (await c.list_tools()).tools])

asyncio.run(main())
EOF
# esperado: ['gerar_imagem']
```

Sem o `env`, o cliente stdio do SDK repassa ao servidor só `HOME`, `PATH` e mais algumas variáveis. Atrás de um proxy, isso dá erro de certificado SSL. Os clientes MCP (Claude Code, Kiro etc.) têm regras próprias; se lá faltar alguma variável, use o bloco `env` da configuração (seção 5).

**b) Geração real.** Custa cerca de US$ 0,14; peça a confirmação do humano. Depois de reiniciar o cliente MCP, chame a tool:

> Use a tool gerar_imagem com prompt "uma árvore frondosa", tipo "8bit" e contexto "ícone para slide de aula de biologia".

O esperado é a imagem e a mensagem `PNG com fundo transparente salvo em .../outputs/8bit-<data>.png`. Os cantos do PNG devem ser transparentes (alfa 0).

---

## 7. Erros comuns

| Mensagem (começo) | Causa | Solução |
|---|---|---|
| `... Falta uma credencial AWS válida` (com `Unable to locate credentials`, `UnrecognizedClientException`, `IncompleteSignatureException` ou `ExpiredTokenException`) | Sem credencial, com chave inválida ou com a sessão do `aws login` expirada | Seção 4.2. Em container ou nuvem, opção C |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Ambiente atrás de proxy, e as variáveis do proxy não chegaram ao servidor | Passar o ambiente para o servidor (nota da seção 6a) |
| `A Bedrock recusou o pedido (AccessDeniedException): Your account is currently being verified` | Conta AWS nova ainda em verificação | Aguardar; costuma levar até 2 h |
| `A Bedrock recusou o pedido (AccessDeniedException)` (outros casos) | Modelos não ativados, ou chave sem permissão para algum dos três modelos (inclusive o Remove Background) | Seções 4.1 e 4.2 |
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
├── prompts/tipo_prompt.py    # tipos (Tipo, TIPOS), contexto e montagem do prompt; função pura
├── app/image_gen.py          # única parte que fala com a Bedrock (gerar e remover fundo)
├── app/pixel_grid.py         # Pillow: grade de pixels, paleta e transparência binária
├── assets/estilos/           # imagem de referência de cada tipo (8bit.png, pixelart.png)
├── tests/                    # pytest, sem chamar a AWS
└── outputs/                  # imagens geradas (fora do git)
```

Fluxo: prompt + tipo + contexto → **Style Guide** (ou **Style Transfer**, se houver imagem de referência) → **Remove Background** → Pillow pixeliza e deixa a transparência binária → PNG em `outputs/`.

- **Mudar o visual de um tipo:** troque o PNG em `assets/estilos/`. Use um objeto isolado sobre **fundo branco liso**, com pelo menos 64 px de lado. O modelo copia a composição e as cores da referência: uma cena completa atrapalha a remoção do fundo, e uma paleta de uma cor só puxa tudo para essa cor.
- **Ajustar um tipo:** em `prompts/tipo_prompt.py`, `fidelidade` vai de 0 a 1 e controla o quanto a imagem copia a referência. Valores altos ignoram o prompt. `pixels` e `cores` controlam a grade e a paleta.
- **Criar um tipo novo:** acrescente o nome em `Tipo`, uma entrada em `TIPOS` e o PNG `assets/estilos/<nome>.png`. O teste `test_todo_tipo_do_schema_tem_preset_e_imagem_de_referencia` confere que as três partes existem. O novo tipo aparece sozinho como opção do parâmetro `tipo`.
- **Lint:** `venv/bin/ruff check . && venv/bin/ruff format --check .`

### Por que Bedrock + Stability (pesquisa de 24/09/2026)

- **Gemini:** nenhum modelo de imagem tem free tier na API ([pricing](https://ai.google.dev/gemini-api/docs/pricing)).
- **Nova Canvas:** está em Legacy, com fim de vida em 30/09/2026, e não aceita clientes novos ([model card](https://docs.aws.amazon.com/bedrock/latest/userguide/model-card-amazon-nova-canvas.html)).
- **Stable Image Core e SD3.5:** saíram da Bedrock.
- **Style Guide, Style Transfer e Remove Background:** estão Active, e o Style Guide aceita `style_preset: "pixel-art"` ([parâmetros](https://docs.aws.amazon.com/bedrock/latest/userguide/stable-image-services.html)).
