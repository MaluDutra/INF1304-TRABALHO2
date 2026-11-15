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

function darEntrada({ isbn, titulo, autor, ano, preco, quantidade }) {
  const corpo = { isbn, quantidade };
  // só mandamos o que foi preenchido: campos ausentes mantêm o valor atual na tabela
  if (titulo) corpo.titulo = titulo;
  if (autor) corpo.autor = autor;
  if (ano !== "" && ano != null) corpo.ano = Number(ano);
  if (preco !== "" && preco != null) corpo.preco = Number(preco);
  return chamar(window.CONFIG.URL_ESTOQUE, {
    method: "POST",
    body: JSON.stringify(corpo),
  }, 30000);
}

// utilidades compartilhadas pelas páginas
function formatarPreco(preco) {
  if (preco == null || preco === "") return "";
  const n = Number(preco);
  return Number.isFinite(n) ? n.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) : "";
}

// pedidoId = "<data ISO>#<8 hex>"  ->  "078595A3 (14/11/2026 às 21:09)"
function formatarPedido(pedidoId, criadoEm) {
  const [iso, codigo] = String(pedidoId || "").split("#");
  const d = new Date(criadoEm || iso);
  if (!codigo) return String(pedidoId || "");
  if (isNaN(d)) return codigo.toUpperCase();
  const data = d.toLocaleDateString("pt-BR");
  const hora = d.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
  return `${codigo.toUpperCase()} (${data} às ${hora})`;
}

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
  }[c]));
}

function guardar(chave, valor) { try { localStorage.setItem(chave, valor); } catch { } }
function lembrar(chave) { try { return localStorage.getItem(chave) || ""; } catch { return ""; } }
