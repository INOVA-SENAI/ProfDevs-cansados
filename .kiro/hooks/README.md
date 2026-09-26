# Hooks do Kiro

Hooks executam uma ação automaticamente quando um evento acontece no IDE. Cada hook é um arquivo JSON em `.kiro/hooks/`.

## Hooks deste projeto

| Arquivo | Gatilho | Ação | Objetivo |
|---|---|---|---|
| `validar-slides.json` | `FileSave` em `slides/*.yaml` ou `slides/*.yml` | `python -m senai_slides.validador slides/ --gerar` | Salvou o deck, validou e gerou a apresentação (`.pptx`, prévias e PDF) de todos os decks sem erro da pasta, com a estimativa de imagens e custo de cada um. Não cobra nada: entram as fotos reais (grátis) e as imagens que já estão no cache; as imagens por IA novas só são criadas rodando o validador com `--aceitar-custo`, depois de o professor aprovar o custo. Tempo limite de 300 s, para dar tempo de buscar as fotos |
| `caca-segredos.json` | `PostTaskExecution` | `python scripts/caca_segredos.py` | Nenhuma chave da AWS nem da Bedrock no repositório |

Os comandos usam o `python` do terminal do Kiro: deixe o `venv` do projeto selecionado como interpretador.

## Formato

```json
{
  "version": "v1",
  "hooks": [
    {
      "name": "Nome do hook",
      "trigger": "FileSave",
      "matcher": "regex-opcional",
      "action": { "type": "command", "command": "comando" },
      "timeout": 60
    }
  ]
}
```

- **trigger:** o evento que dispara o hook (tabela abaixo).
- **matcher:** regex opcional. Nos eventos de arquivo, é comparada com o caminho; nos de ferramenta, com o nome da ferramenta. Sem matcher, o hook sempre dispara.
- **action:** `command` roda um comando no terminal; `agent` injeta um `prompt` na conversa.
- **timeout:** só para `command`. 60 s por padrão; `0` desliga.

## Gatilhos

| Trigger | Quando dispara |
|---|---|
| `PromptSubmit` | Ao enviar uma mensagem ao agente (pode bloquear) |
| `AgentStop` | Quando o agente termina a resposta |
| `SessionStart` | Ao iniciar uma sessão (só IDE) |
| `PreToolUse` | Antes de uma ferramenta rodar (pode bloquear) |
| `PostToolUse` | Depois de uma ferramenta rodar |
| `FileCreate` | Ao criar um arquivo |
| `FileSave` | Ao salvar um arquivo |
| `FileDelete` | Ao apagar um arquivo |
| `PreTaskExecution` | Antes de uma task de spec começar (só IDE) |
| `PostTaskExecution` | Depois que uma task de spec termina (só IDE) |

Fonte: kiro.dev/docs/hooks. O teste `tests/test_kiro.py` confere que os hooks do projeto usam só esses gatilhos.
