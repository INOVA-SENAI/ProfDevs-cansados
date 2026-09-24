# Hooks do Kiro

Hooks permitem que o agente execute ações automaticamente quando eventos ocorrem no IDE.

## Como criar um Hook

Crie um arquivo JSON em `.kiro/hooks/<id>.json` seguindo o schema:

```json
{
  "version": "v1",
  "hooks": [{
    "name": "Nome do Hook",
    "trigger": "NomeDoEvento",
    "matcher": "regex-opcional",
    "action": {
      "type": "command",
      "command": "comando-a-executar"
    }
  }]
}
```

## Eventos disponíveis (triggers)

| Trigger | Quando dispara |
|---|---|
| `SessionStart` | Ao iniciar uma nova sessão no Kiro |
| `UserPromptSubmit` | Ao enviar uma mensagem ao agente |
| `PreToolUse` | Antes de uma ferramenta ser executada |
| `PostToolUse` | Após uma ferramenta ser executada |
| `PostFileSave` | Ao salvar um arquivo |
| `PostFileCreate` | Ao criar um novo arquivo |
| `PostFileDelete` | Ao deletar um arquivo |
| `PreTaskExec` | Antes de uma task de spec iniciar |
| `PostTaskExec` | Após uma task de spec ser concluída |
| `Stop` | Ao encerrar uma execução do agente |

## Tipos de ação

- **`command`** — executa um comando shell; recebe JSON via stdin com contexto da sessão
- **`agent`** — injeta um prompt estático no contexto do modelo

## Exemplo: Lint ao salvar arquivos TypeScript

```json
{
  "version": "v1",
  "hooks": [{
    "name": "Lint on Save",
    "trigger": "PostFileSave",
    "matcher": "\\.(ts|tsx)$",
    "action": {
      "type": "command",
      "command": "npm run lint"
    }
  }]
}
```

## Exemplo: Rodar testes após completar uma task

```json
{
  "version": "v1",
  "hooks": [{
    "name": "Run Tests After Task",
    "trigger": "PostTaskExec",
    "action": {
      "type": "command",
      "command": "npm run test -- --run"
    }
  }]
}
```
