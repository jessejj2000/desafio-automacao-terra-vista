const fs = require('fs');
const http = require('https'); // ou http dependendo do seu webhook

const WEBHOOK_URL = 'https://n8n.grupoellev.com.br/webhook/process-matriculas';

// Exemplo de carga de dados para testar a automação
const payload = {
  body: [
    {
      "Link_Matricula_PDF": "https://venda-imoveis.caixa.gov.br/editais/matricula/RJ/8444405265892.pdf",
      "CIDADE": "São Gonçalo"
    },
    {
      "Link_Matricula_PDF": "https://venda-imoveis.caixa.gov.br/editais/matricula/RJ/8787706287197.pdf",
      "CIDADE": "Rio de Janeiro"
    }
  ]
};

const dataString = JSON.stringify(payload);

const options = {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Content-Length': Buffer.byteLength(dataString),
    'User-Agent': 'Mozilla/5.0 (Node.js)'
  }
};

console.log(`Disparando webhook em ${WEBHOOK_URL}...`);

const req = http.request(WEBHOOK_URL, options, (res) => {
  console.log(`Status HTTP: ${res.statusCode}`);
  const chunks = [];
  res.on('data', (chunk) => {
    chunks.push(chunk);
  });
  res.on('end', () => {
    console.log('Resposta do Webhook Finalizada.');
    const buffer = Buffer.concat(chunks);
    if (res.headers['content-type'] && res.headers['content-type'].includes('spreadsheet')) {
      fs.writeFileSync('/home/jessegoncalves/problm/planilha_teste.xlsx', buffer);
      console.log('Planilha salva em planilha_teste.xlsx');
    } else {
      console.log(buffer.toString());
    }
  });
});

req.on('error', (error) => {
  console.error('Erro na requisição:', error);
});

req.write(dataString);
req.end();
