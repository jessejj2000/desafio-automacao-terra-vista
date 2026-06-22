import json

# This points to the version we had saved in the file before anything
input_path = "/home/jessegoncalves/problm/workflow_terra_vista.json"
output_path = "/home/jessegoncalves/problm/workflow_terra_vista.json"

with open(input_path, 'r') as f:
    wf = json.load(f)

# The local JSON is just the nodes array, not {"data": {"nodes": []}} like the MCP response!
# Wait, let me check the format of workflow_terra_vista.json
if 'data' in wf:
    wf = wf['data']

# Remove the old custom loop nodes and extract nodes
nodes_to_remove = ["If (Has More Items)", "Set Current Item", "Extract Final Results", "Extract PDF Text", "If Text OK", "Handle Scanned Error", "Prepare AI Prompt", "AI Extraction", "Consolidate AI Data", "Google Vertex AI Chat Model", "Google Vertex Account"]

wf['nodes'] = [n for n in wf['nodes'] if n['name'] not in nodes_to_remove]

# 1. Update Sanitize URLs & Slice to remove the slice
for n in wf['nodes']:
    if n['name'] == 'Sanitize URLs & Slice':
        n['name'] = 'Sanitize URLs'
        # remove slice logic
        n['parameters']['jsCode'] = """const items = $input.all();
const body = items[0].json.body.body;
if (!Array.isArray(body)) {
  throw new Error("Input must be a JSON array in the request body");
}
const sanitized = body.map(data => {
  let url = data.Link_Matricula_PDF || "";
  url = url.replace(/,/g, '.');
  return {
    ...data,
    Link_Matricula_PDF: url,
    URL_origem: url,
    status_processamento: "pendente",
    data_hora: new Date().toISOString(),
    observacoes: ""
  };
});
return sanitized.map(s => ({ json: s }));"""

# 2. Add Remove Duplicates node
remove_duplicates_node = {
    "parameters": {
        "compare": "fields",
        "fieldsToCompare": "Link_Matricula_PDF",
        "options": {}
    },
    "id": "remove-duplicates-id",
    "name": "Remove Duplicates",
    "type": "n8n-nodes-base.removeDuplicates",
    "typeVersion": 1,
    "position": [400, 0]
}
wf['nodes'].append(remove_duplicates_node)

# 3. Add Loop node
loop_node = {
    "parameters": {
        "options": {}
    },
    "id": "loop-id",
    "name": "Loop",
    "type": "n8n-nodes-base.splitInBatches",
    "typeVersion": 3,
    "position": [600, 0]
}
wf['nodes'].append(loop_node)

# 4. Modify Download PDF
for n in wf['nodes']:
    if n['name'] == 'Download PDF':
        n['position'] = [800, 0]
        # Set Retry on Fail
        n['retryOnFail'] = True
        n['maxTries'] = 3
        n['waitBetweenTries'] = 2000

# 5. Add Prepare Gemini Payload and Call Gemini API (since the local JSON lacked the raw API node)
prepare_gemini_payload_node = {
    "parameters": {
        "jsCode": """const currentItem = $('Loop').item.json;
const base64Data = (await this.helpers.getBinaryDataBuffer(0, 'data')).toString('base64');
const promptText = "Analise o arquivo de matrícula de imóvel (PDF) fornecido e extraia as informações fiscais e de propriedade estritamente conforme as regras:\\n\\nREGRAS CRÍTICAS:\\n1. Extraia apenas dados LITERALMENTE presentes na matrícula. Não invente nenhum dado.\\n2. Se uma informação não estiver explícita, preencha o campo correspondente como \\\"não encontrado\\\".\\n3. Identifique se o imóvel sofreu execução por inadimplência (leilão extrajudicial, consolidação da propriedade por alienação fiduciária, adjudicação, arrematação). Se sim, extraia o(s) proprietário(s) anterior(es) afetado(s) e o número da averbação.\\n\\nRetorne a resposta estritamente no seguinte formato JSON. Não adicione nenhuma explicação extra ou Markdown:\\n{\\n  \\\"numero_matricula_cartorio\\\": \\\"número da matrícula e o cartório / ofício de registro de imóveis\\\",\\n  \\\"inscricao_municipal\\\": \\\"inscrição municipal/imobiliária do imóvel\\\",\\n  \\\"contribuinte\\\": \\\"contribuinte (titular vinculado)\\\",\\n  \\\"proprietarios_atuais\\\": [\\\"nome do proprietário 1\\\", \\\"nome do proprietário 2\\\"],\\n  \\\"indicador_execucao_inadimplencia\\\": true ou false,\\n  \\\"proprietarios_anteriores\\\": [\\\"nome do proprietário anterior 1\\\"] ou [],\\n  \\\"averbacao_execucao\\\": \\\"número ou descrição da averbação de consolidação/leilão\\\" ou \\\"não encontrado\\\",\\n  \\\"data_ultima_compra_venda\\\": \\\"data no formato DD/MM/AAAA\\\",\\n  \\\"valor_ultima_compra_venda\\\": \\\"valor em R$\\\",\\n  \\\"valor_avaliacao\\\": \\\"valor de avaliação em R$\\\",\\n  \\\"onus_gravames\\\": \\\"lista de ônus ativos (hipoteca, penhora, etc.) ou 'não encontrado'\\\"\\n}";

return [{
  json: {
    ...currentItem,
    geminiPayload: {
      contents: [
        {
          role: "user",
          parts: [
            {
              inlineData: {
                mimeType: "application/pdf",
                data: base64Data
              }
            },
            {
              text: promptText
            }
          ]
        }
      ]
    }
  }
}];"""
    },
    "id": "prepare-gemini-payload-id",
    "name": "Prepare Gemini Payload",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1200, 0]
}
wf['nodes'].append(prepare_gemini_payload_node)

call_gemini_api_node = {
    "parameters": {
        "method": "POST",
        "url": "https://us-central1-aiplatform.googleapis.com/v1/projects/project-112b24ea-45b3-459e-b56/locations/us-central1/publishers/google/models/gemini-2.5-flash:generateContent",
        "authentication": "predefinedCredentialType",
        "nodeCredentialType": "googleApi",
        "sendBody": True,
        "specifyBody": "json",
        "jsonBody": "={{ JSON.stringify($json.geminiPayload) }}",
        "options": {}
    },
    "id": "call-gemini-api-id",
    "name": "Call Gemini API",
    "type": "n8n-nodes-base.httpRequest",
    "typeVersion": 4.4,
    "position": [1400, 0],
    "credentials": {
        "googleApi": {
            "id": "3ChtMMbpuSHREvkv",
            "name": "Google Vertex Account HTTP"
        }
    },
    "onError": "continueRegularOutput"
}
wf['nodes'].append(call_gemini_api_node)

consolidate_ai_data_node = {
    "parameters": {
        "jsCode": """const currentItem = $('Loop').item.json;
let result = {};
try {
  const aiOutput = $('Call Gemini API').item.json.candidates[0].content.parts[0].text;
  let parsed = aiOutput;
  if (typeof parsed === 'string') {
    const jsonMatch = parsed.match(/\\{[\\s\\S]*\\}/);
    if (jsonMatch) {
      parsed = JSON.parse(jsonMatch[0]);
    } else {
      parsed = JSON.parse(parsed);
    }
  }
  result = {
    ...currentItem,
    ...parsed,
    status_processamento: "sucesso",
    observacoes: ""
  };
} catch (e) {
  result = {
    ...currentItem,
    status_processamento: "revisao_manual",
    observacoes: "Erro ao analisar resposta da IA: " + e.message
  };
}
return [{ json: result }];"""
    },
    "id": "consolidate-ai-data-id",
    "name": "Consolidate AI Data",
    "type": "n8n-nodes-base.code",
    "typeVersion": 2,
    "position": [1600, 0]
}
wf['nodes'].append(consolidate_ai_data_node)

# 7. Modify Handle Download Error
for n in wf['nodes']:
    if n['name'] == 'Handle Download Error':
        n['position'] = [1000, 200]
        n['parameters']['jsCode'] = """const currentItem = $('Loop').item.json;
return [{
  json: {
    ...currentItem,
    status_processamento: "revisao_manual",
    observacoes: "Link quebrado ou erro HTTP ao baixar o PDF após retentativas"
  }
}];"""

# 8. Rebuild connections entirely
wf['connections'] = {
    "Webhook": {
        "main": [[{"node": "Sanitize URLs", "type": "main", "index": 0}]]
    },
    "Sanitize URLs": {
        "main": [[{"node": "Remove Duplicates", "type": "main", "index": 0}]]
    },
    "Remove Duplicates": {
        "main": [[{"node": "Loop", "type": "main", "index": 0}]]
    },
    "Loop": {
        "main": [
            [{"node": "Download PDF", "type": "main", "index": 0}], # loop branch
            [{"node": "Generate Output XLSX", "type": "main", "index": 0}] # done branch
        ]
    },
    "Download PDF": {
        "main": [[{"node": "If Download OK", "type": "main", "index": 0}]]
    },
    "If Download OK": {
        "main": [
            [{"node": "Prepare Gemini Payload", "type": "main", "index": 0}],
            [{"node": "Handle Download Error", "type": "main", "index": 0}]
        ]
    },
    "Prepare Gemini Payload": {
        "main": [[{"node": "Call Gemini API", "type": "main", "index": 0}]]
    },
    "Call Gemini API": {
        "main": [[{"node": "Consolidate AI Data", "type": "main", "index": 0}]]
    },
    "Consolidate AI Data": {
        "main": [[{"node": "Loop", "type": "main", "index": 0}]]
    },
    "Handle Download Error": {
        "main": [[{"node": "Loop", "type": "main", "index": 0}]]
    }
}

# Fix missing node positions
for n in wf['nodes']:
    if n['name'] == 'If Download OK':
        n['position'] = [1000, 0]
    elif n['name'] == 'Generate Output XLSX':
        n['position'] = [800, -200]

with open(output_path, 'w') as f:
    json.dump(wf, f, indent=2)

print("Workflow patched and saved directly to workflow_terra_vista.json.")
