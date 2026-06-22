# SKILL.md — MCP Builder: Construção de Workflows n8n

## Objetivo desta Skill

Guia passo a passo para criar, modificar e validar workflows n8n usando o MCP Server do Claude Code.

## Fluxo Obrigatório de Construção

```
1. get_sdk_reference          → ler referência do SDK
2. get_workflow_best_practices → boas práticas da técnica usada
3. search_nodes               → descobrir nós necessários
4. get_node_types             → obter parâmetros exatos de cada nó
5. validate_node_config       → validar cada nó antes de conectar
6. validate_workflow          → validar o workflow completo
7. create_workflow_from_code  → criar na plataforma
```

> Nunca pular etapas. Nunca adivinhar nomes de parâmetros.

## Modificar Workflow Existente

```
1. get_workflow_details {id}  → baixar estado atual
2. Planejar operações de update
3. update_workflow {id, operations[]}  → aplicar atomicamente
```

### Operações disponíveis no update_workflow:
- `addNode` — adicionar novo nó
- `removeNode` — remover nó
- `updateNodeParameters` — atualizar múltiplos parâmetros de um nó
- `setNodeParameter` — atualizar um parâmetro específico
- `renameNode` — renomear nó
- `addConnection` — conectar dois nós
- `removeConnection` — desconectar nós
- `setNodeCredential` — definir credencial do nó
- `setNodePosition` — mover nó no canvas
- `setNodeDisabled` — habilitar/desabilitar nó
- `setNodeSettings` — configurar comportamento (onError, retry, etc)
- `setWorkflowMetadata` — atualizar nome, tags, etc

## Padrões Comuns (Terra Vista)

### Webhook → Loop de Itens → HTTP Request → Consolidar
O workflow Terra Vista processa matrículas em loop:
- **Webhook** recebe array de itens
- **Code** sanitiza URLs e inicializa estado do loop
- **If** verifica se há mais itens
- **HTTP Request** baixa PDF da matrícula atual
- **AI Agent** extrai dados do PDF
- **Code** avança o índice e acumula resultados
- **Loop back** volta para o If até esgotar itens
- **Respond to Webhook** retorna resultado consolidado

### Credenciais necessárias:
- OpenAI API (para nós de IA)
- HTTP Basic/Bearer (para PDFs protegidos)

## Dicas e Armadilhas

| Situação | O que fazer |
|---|---|
| Reconfigurar nó existente | Usar `updateNodeParameters`, NUNCA remove+add |
| Sub-nó (LLM, memory, tool) | Usar `setNodeSettings` para onError, pois o canvas não expõe isso |
| Workflow em produção | Sempre `validate_workflow` antes de `update_workflow` |
| Parâmetro com nome errado | Rodar `get_node_types` com discriminadores corretos |
| Testar sem afetar produção | Usar `prepare_test_pin_data` + `test_workflow` |

## Exemplo de Chamada: Criar Workflow Simples

```typescript
// Após get_sdk_reference e get_node_types:
import { createWorkflow, n8n } from '@n8n/workflow-sdk';

export default createWorkflow({
  name: 'Meu Workflow',
  nodes: [
    n8n.nodes.webhook({ path: 'meu-webhook' }),
    n8n.nodes.set({ values: { mensagem: 'ok' } }),
    n8n.nodes.respondToWebhook(),
  ],
});
```

## Arquivos de Referência

- Snapshot local do workflow: `/home/jessegoncalves/problm/workflow_terra_vista.json`
- Regras gerais do ambiente: `/home/jessegoncalves/problm/.agent/AGENTS.md`
