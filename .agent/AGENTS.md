# AGENTS.md — Regras Base do Ambiente n8n (Grupo Ellev)

## Identidade do Ambiente

- **Instância n8n:** https://n8n.grupoellev.com.br
- **API REST:** https://n8n.grupoellev.com.br/api/v1/
- **MCP Server:** https://n8n.grupoellev.com.br/mcp-server/http
- **Workflow principal:** Terra Vista (`id: GoReM1W65uebzAMu`)
- **Workflow ID MCP:** `inyyo2bPGQvA1xo0`

## Como o Agente Lê e Modifica Workflows

### Via MCP (preferencial)
O Claude Code usa o MCP Server do n8n configurado em `~/.claude/settings.json`.
Ferramentas disponíveis:
- `search_workflows` — buscar workflows por nome
- `get_workflow_details` — baixar JSON completo de um workflow
- `create_workflow_from_code` — criar novo workflow via SDK
- `update_workflow` — modificar nós e conexões de forma atômica
- `validate_workflow` — validar código antes de criar
- `execute_workflow` — disparar execução manual

### Via API REST (alternativa)
```
GET  /api/v1/workflows/{id}
POST /api/v1/workflows
PUT  /api/v1/workflows/{id}
Header: X-N8N-API-KEY: <chave gerada no painel n8n>
```
> A API key REST é diferente do token JWT do MCP. Gere em: Configurações → API → Criar chave.

### Via JSON local
Salvar o arquivo `.json` exportado do n8n em `/home/jessegoncalves/problm/` e informar o nome do arquivo. O agente lê, analisa e propõe modificações diretamente.

## Regras de Comportamento

1. **Nunca modificar um workflow em produção sem validar primeiro** — sempre usar `validate_workflow` antes de `update_workflow` ou `create_workflow_from_code`.
2. **Operações atômicas** — o `update_workflow` aplica todas as operações de uma vez; se uma falhar, nenhuma é aplicada. Planejar o conjunto completo antes de executar.
3. **Nunca usar removeNode + addNode para reconfigurar** — usar `updateNodeParameters` ou `setNodeParameter` para não desconectar sub-nós.
4. **Ler o SDK antes de escrever código** — chamar `get_sdk_reference` antes de criar qualquer workflow novo.
5. **Consultar boas práticas por técnica** — chamar `get_workflow_best_practices` para cada padrão usado (chatbot, scheduling, triage, etc).

## Estrutura do Projeto Local

```
/home/jessegoncalves/problm/
├── .agent/
│   ├── AGENTS.md                    ← este arquivo
│   └── skills/
│       └── mcp-builder/
│           └── SKILL.md             ← skill de construção de workflows
├── workflow_terra_vista.json        ← snapshot local do workflow Terra Vista
├── planilha_imoveis_consolidada_test.xlsx
├── server.js                        ← proxy/servidor Node.js local
├── proxy.js
└── .env                             ← variáveis de ambiente (não commitar segredos)
```

## Credenciais e Segredos

| Variável | Onde fica | Uso |
|---|---|---|
| MCP JWT Token | `~/.claude/settings.json` | Autenticar MCP Server |
| N8N_API_KEY | Painel n8n → Settings → API | Autenticar API REST |
| APP_ID / APP_SECRET | `.env` | Meta/WhatsApp Business API |
