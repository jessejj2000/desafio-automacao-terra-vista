const http = require('https'); // usando https se o webhook for https
const xlsx = require('xlsx');

const WEBHOOK_URL = 'https://n8n.grupoellev.com.br/webhook/process-matriculas';

// Lê a planilha original
const workbook = xlsx.readFile('/home/jessegoncalves/problm/planilha_imoveis_consolidada_test.xlsx');
const sheetName = workbook.SheetNames[0];
const sheet = xlsx.utils.sheet_to_json(workbook.Sheets[sheetName]);

// Pega os 5 primeiros
const amostra = sheet.slice(0, 5).map(row => ({
    Link_Matricula_PDF: row.Link_Matricula_PDF || row.URL_origem,
    CIDADE: row.CIDADE
})).filter(row => row.Link_Matricula_PDF); // remove vazios

const payload = { body: amostra };
const dataString = JSON.stringify(payload);

const options = {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(dataString),
        'User-Agent': 'Mozilla/5.0 (Node.js)'
    }
};

console.log(`Disparando webhook em ${WEBHOOK_URL} para ${amostra.length} imóveis...`);

const req = http.request(WEBHOOK_URL, options, (res) => {
    console.log(`Status HTTP: ${res.statusCode}`);
    const chunks = [];
    res.on('data', (chunk) => {
        chunks.push(chunk);
    });
    res.on('end', () => {
        const buffer = Buffer.concat(chunks);
        if (res.headers['content-type'] && res.headers['content-type'].includes('spreadsheet')) {
            require('fs').writeFileSync('/home/jessegoncalves/problm/planilha_5_imoveis.xlsx', buffer);
            console.log('Planilha salva com sucesso em planilha_5_imoveis.xlsx');
        } else {
            console.log(buffer.toString());
        }
    });
});

req.on('error', (error) => {
    console.error('Erro:', error);
});

req.write(dataString);
req.end();
