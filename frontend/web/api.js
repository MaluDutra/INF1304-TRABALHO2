// Chamadas às Lambdas (Function URLs).
// Os POST vão SEM "Content-Type: application/json": o navegador usa text/plain,
// o que evita a requisição OPTIONS (preflight) de CORS. As Lambdas fazem
// json.loads(event["body"]) de qualquer jeito e já devolvem
// Access-Control-Allow-Origin: *, então nada precisa ser configurado na AWS.

async function chamar(url, opcoes = {}, timeoutMs = 30000) {
  if (!url || /^https:\/\/(xxxx|yyyy|zzzz)\./.test(url)) {
    throw new Error("URL da Lambda não configurada. Edite frontend/web/config.js.");
  }
  const controle = new AbortController();
  const timer = setTimeout(() => controle.abort(), timeoutMs);
  let resp;
  try {
    resp = await fetch(url, { ...opcoes, signal: controle.signal });
  } catch (e) {
    if (e.name === "AbortError") throw new Error("A Lambda demorou demais para responder.");
    throw new Error("Não foi possível falar com a Lambda (rede ou CORS).");
  } finally {
    clearTimeout(timer);
  }
  const texto = await resp.text();
  let dados = null;
  try { dados = texto ? JSON.parse(texto) : null; } catch { /* resposta não-JSON */ }
  if (!resp.ok) {
    const msg = (dados && (dados.erro || dados.message)) || texto || resp.statusText;
    throw new Error(`Erro ${resp.status}: ${msg}`);
  }
  return dados;
}

function listarLivros() {
  return chamar(window.CONFIG.URL_CATALOGO, { method: "GET" }, 15000);
}

function fazerPedido({ nome, email, isbn }) {
  return chamar(window.CONFIG.URL_PEDIDO, {
    method: "POST",
    body: JSON.stringify({ nome, email, isbn }),
  }, 15000);
}

function darEntrada({ isbn, titulo, autor, quantidade }) {
  const corpo = { isbn, quantidade };
  // a Lambda usa if_not_exists, mas só mandamos título/autor se preenchidos
  if (titulo) corpo.titulo = titulo;
  if (autor) corpo.autor = autor;
  return chamar(window.CONFIG.URL_ESTOQUE, {
    method: "POST",
    body: JSON.stringify(corpo),
  }, 30000);
}

// utilidades compartilhadas pelas páginas
function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function guardar(chave, valor) { try { localStorage.setItem(chave, valor); } catch { } }
function lembrar(chave) { try { return localStorage.getItem(chave) || ""; } catch { return ""; } }
