# Análise de Melhorias — Workflow Terra Vista

Análise cruzando o enunciado oficial do teste (critérios + pesos), o workflow real e o README.

## Veredito rápido

O fluxo está **funcional e bem pensado em tratamento de erro**, mas tem **3 lacunas que o enunciado testa de propósito** e uma **contradição entre o README e o workflow** que é arriscada na entrevista de 20–30 min ("você deve ser capaz de explicar cada parte"). A arquitetura atual, apesar do README ser todo sobre escala, **não escala de verdade para 800**.

---

## 1. Lacunas que custam pontos diretos (mapeadas ao edital)

**🔴 Sem deduplicação — critério 1 (25%) cita "duplicata" explicitamente**
O avaliador vai incluir *de propósito* "1 matrícula duplicada na lista". Seu fluxo não tem nenhuma lógica de dedupe. Hoje a duplicata é processada 2x e entra 2x na planilha. Isso é perda garantida.

**🔴 Sem retry — critério 3 (15%) exige "retry para falhas temporárias"**
`Download PDF` tem `onError: continueRegularOutput` (desvia), mas **não tem `retryOnFail`**. Um timeout/link-fora-do-ar momentâneo é tratado como erro permanente e mandado pra revisão manual. O enunciado separa "falha temporária (retry)" de "link quebrado (404)". Faltou o retry.

**🔴 `slice(0, 50)` hardcoded — contradiz "escalar a 800+ sem retrabalho"**
`workflow_terra_vista.json:33`: `const sliced = sanitized.slice(0, 50)`. Rodar os 800 exige editar o nó. O critério 3 avalia exatamente "prontidão para escala sem retrabalho".

**🟡 Sem persistência incremental — risco em execução de 4h**
`Consolidate AI Data` acumula tudo em `_state.results` e o XLSX só é escrito **no final**. Se cair no item 700 (e em 4h15 de execução isso é provável, ainda mais com túnel `lhr.life` efêmero), você perde tudo. Não há resume. Para "prontidão para escala" isso é frágil.

---

## 2. A contradição README ↔ workflow (o maior risco na entrevista)

O README afirma **3x** que usa Gemini **multimodal** — *"análise nativa e multimodal do PDF (sem a necessidade de extrair texto ou executar OCR)"*. Mas o workflow real faz `Extract PDF Text` (readPDF) e manda **texto** (`cleanText`) pro modelo. São coisas opostas. Um avaliador que abrir o JSON vai ver `$json.prompt` com texto extraído, não PDF binário.

**A boa notícia:** corrigir isso *para o lado multimodal* resolve vários problemas de uma vez:
- Hoje **33% dos imóveis (PDFs escaneados) são simplesmente abandonados** em `revisao_manual`. Gemini multimodal **lê a imagem direto** — você processaria esse 1/3 que hoje joga fora, sem OCR externo.
- Bate com a sua **própria conta de custo** no README (que já assume 5.000 tokens de PDF multimodal).
- **Simplifica o grafo**: remove `Extract PDF Text` + `If Text OK` + `Handle Scanned Error`.

Ou seja: ou você ajusta o README pra refletir a abordagem de texto (honesto, mas perde o diferencial e os 33%), ou torna o fluxo **de fato multimodal** (recomendo — é mais forte e já está "prometido").

---

## 3. Redesenho de arquitetura para escala real

A engenhosidade do loop manual com `_state` tem um custo: **o array inteiro + todos os resultados acumulados viajam por cada nó a cada iteração** (memória ~O(n²) para 800 docs). O padrão idiomático do n8n resolve dedupe + retry + resume + rate-limit de uma vez:

```
Trigger (Sheets/CSV)
  → Dedupe (Remove Duplicates por URL/nº matrícula)
  → Loop Over Items (Split in Batches, lote controlado)
      → Download PDF  [retryOnFail: 3, waitBetween]
      → AI Extraction (PDF binário → Gemini multimodal)  [retryOnFail]
      → Structured Output Parser (JSON garantido)
      → Append Row → Google Sheets   ← grava JÁ, linha a linha
  → (resume: pula linhas já presentes na planilha)
```

Ganhos por critério: **append incremental** = crash-safe + resume; **Remove Duplicates** = dedupe (25%); **retryOnFail** = retry (15%); **Split in Batches** = rate-limit natural; **Structured Output Parser** = menos JSON malformado (15% prompt). Isso ataca ~55% da nota.

---

## 4. Estrutura do repositório / projeto

- **🔴 LGPD — a planilha está commitada no git.** O edital diz literalmente *"não publique os PDFs nem a planilha em repositório público... apague tudo após o processo"*. `git ls-files` mostra `planilha_imoveis_consolidada_test.xlsx` rastreada. Se esse repo for pro GitHub, é violação direta de um item que **vale ponto** (critério 6). Remova do tracking e coloque no `.gitignore`.
- **🟡 Falta a seção LGPD no README principal.** Você tem menções de LGPD no bônus IPTU, mas não a "Observação sobre dados pessoais" da missão principal (confidencialidade, acesso restrito, exclusão). O critério 6 cita "cuidados com dados pessoais reconhecidos".
- **🟡 Referência quebrada:** o README manda rodar `node scratch/trigger_webhook.js`, mas `scratch/` não existe. Crie o script ou ajuste o texto.
- **Organização sugerida** (separa entregáveis, protege dados):
  ```
  terra-vista/
  ├── workflow/terra_vista.json
  ├── proxy/proxy.js
  ├── scripts/trigger_webhook.js      ← hoje quebrado
  ├── docs/README.md
  ├── docs/analise-iptu.md            ← bônus pede "documento de análise" separado
  ├── data/                           ← .gitignored (planilha fica aqui, fora do git)
  └── .gitignore                      ← + *.xlsx, data/
  ```
  O edital trata o bônus IPTU como **documento próprio** ("Documento de análise, 1 a 3 páginas") — hoje está embutido no README. Separar deixa os dois entregáveis nítidos.

---

## 5. Prioridade se for mexer (ordem de retorno por ponto)

1. **Dedupe + retry + tirar o `slice(50)`** → destrava 40% da nota e são mudanças pequenas
2. **Resolver a contradição multimodal** (idealmente virar multimodal de verdade → recupera os 33% escaneados)
3. **Tirar a planilha do git + seção LGPD** → ponto fácil e evita problema ético
4. **Append incremental / resume** → robustez real para os 800

---

# Execução da Refatoração (resultado)

## ✅ Feito e verificado

**Bugs corrigidos no `workflow_terra_vista.json`** (confirmados lendo o arquivo de volta):

| Fix | Antes | Depois |
|---|---|---|
| 🔴 Loop saída **done** (idx 0) | → Download PDF | → **Generate Output XLSX** ✓ |
| 🔴 Loop saída **loop** (idx 1) | → Generate XLSX | → **Download PDF** ✓ |
| 🔴 Dedupe `compare` | `"fields"` (inválido) | `"selectedFields"` ✓ |
| 🟡 Retry no Gemini | ausente | `retryOnFail: 3 / 5s` ✓ |

**README alinhado ao multimodal** — distribuição, tempo e custo descreviam a abordagem antiga. Recalculado: ~757 PDFs vão ao Gemini (nativos **+** escaneados, sem mais 33% em revisão manual), tempo ~**6h20** (escaneado agora custa 30s, não 2s) e custo ~**$0.33 / R$1.78**. Totais do comparativo também recalculados.

**Validado no n8n via MCP:**
```
{ "valid": true, "nodeCount": 11 }
```
O `validate_workflow` confirmou o design corrigido — incluindo o wiring do loop, que no SDK fica explícito como `.onDone(generateXlsx)` e `.onEachBatch(downloadPdf…)`, exatamente a semântica que estava invertida no JSON.

## Para colocar no ar

O único caminho de deploy via MCP é `create_workflow_from_code`, que **(a)** cria um workflow com **ID novo** (o ativo continua sendo o `GoReM1W65uebzAMu`) e **(b)** subiria a versão SDK usada na validação, com **prompt encurtado** — e o prompt completo vale 15% da nota. Subir essa versão seria um downgrade.

Caminho fiel de publicar o **artefato exato** (com o prompt inteiro) — importar o JSON pela UI do n8n:

> Abrir o workflow **Terra Vista** → menu **⋮** → **Import from File** → selecionar `workflow_terra_vista.json` → **Save** (e reativar). Substitui a arquitetura antiga pela corrigida, mantendo o mesmo ID e o webhook `process-matriculas`.

## Pendência importante

O fluxo refatorado **ainda não rodou de ponta a ponta** — só foi validado estruturalmente. Depois de importar, rodar `node scripts/trigger_webhook.js` com proxy/túnel ativos e conferir a planilha de saída. Esse é o teste real que o avaliador vai fazer.

**Git:** não tocado. Correções no working tree, sem commit; remoção da planilha segue staged localmente. Nada foi para o GitHub.
