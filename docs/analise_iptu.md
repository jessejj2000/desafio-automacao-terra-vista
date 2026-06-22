# Estudo de Viabilidade Técnica - Automação de IPTU (RJ e São Gonçalo)

Para enriquecer a planilha de matrículas, mapeamos a viabilidade de consultar automaticamente débitos de IPTU usando a **Inscrição Municipal** (extraída por IA nas matrículas).

## 1. Município do Rio de Janeiro (Portal Carioca Digital)
* **Portal Oficial**: `https://carioca.rio/` ou `https://iptu.prefeitura.rio/`
* **Cenários de Consulta**:
  1. **Débitos Ordinários (Ano Corrente / Exercícios Recentes)**: A consulta e a emissão de guia podem ser feitas apenas informando a Inscrição Municipal (CL) e o Exercício.
  2. **Débitos Inscritos em Dívida Ativa**: Administrado pela PGM (Procuradoria Geral do Município). Exige login obrigatório via **Gov.br** (nível Prata/Ouro) ou cadastro com CPF do proprietário no ID Carioca.
* **Desafios e Bloqueios**:
  * **WAF/Cloudflare**: O portal da prefeitura do Rio utiliza proteção Cloudflare rigorosa, bloqueando requisições automatizadas diretas (HTTP requests simples).
  * **CAPTCHA**: Protegido por Google reCAPTCHA v2 ou hCaptcha na emissão de segundas vias de guias.
  * **Gov.br**: A automação de logins Gov.br é desencorajada por envolver 2FA (tokens via app ou SMS) e termos rígidos de segurança.
* **Arquitetura de Solução Proposta**:
  * Automação via **Playwright/Puppeteer** em Node.js rodando sob proxies residenciais.
  * Integração com serviço de quebra de captcha (ex: **2Captcha**, **CapSolver** ou **Anti-Captcha**) para resolver os desafios visuais automaticamente.
  * Consulta focada em Débitos Ordinários (segunda via de IPTU). Para débitos em Dívida Ativa, o fluxo deve desviar para uma fila de processamento humano (Human-in-the-Loop) ou integrar APIs privadas de terceiros que já possuam convênios integrados.

## 2. Município de São Gonçalo (Portal Semfi Fazenda)
* **Portal Oficial**: `https://semfi.pmsg.rj.gov.br/` (Siap e-GOV) ou Portal da Fazenda de São Gonçalo.
* **Cenários de Consulta**:
  * O sistema permite a emissão de Certidão de Débitos e consulta de Dívida Ativa de imóveis apenas com o número da Inscrição Municipal, sem exigir autenticação Gov.br.
* **Desafios e Bloqueios**:
  * **CAPTCHA Alfanumérico Simples**: Exibe uma imagem com texto distorcido de 4 a 5 caracteres para validação de formulário.
* **Arquitetura de Solução Proposta**:
  * Navegador headless (**Playwright**) acessando o formulário do portal municipal.
  * Captura da imagem do captcha e processamento via modelo local de OCR leve (ex: **Tesseract OCR** com biblioteca `pytesseract` ou modelo CNN treinado em Python) para resolver o captcha em milissegundos sem custo de API externa.
  * Extração da tabela de débitos diretamente do HTML da página ou download do PDF da Certidão Negativa/Positiva de Débitos.
