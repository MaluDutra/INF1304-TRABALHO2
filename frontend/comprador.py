import requests, config
from datetime import datetime

def formatar_pedido(dados):
    """pedidoId "<data ISO>#<8 hex>" -> "078595A3 (14/11/2026 as 21:09)" no fuso local"""
    iso, _, codigo = dados["pedidoId"].partition("#")
    try:
        quando = datetime.fromisoformat(dados.get("criadoEm") or iso).astimezone()
        return f"{codigo.upper()} ({quando:%d/%m/%Y} às {quando:%H:%M})"
    except ValueError:
        return codigo.upper() or dados["pedidoId"]

def listar():
    livros = requests.get(config.URL_CATALOGO, timeout=15).json()
    print()
    for livro in livros:
        estoque = int(livro["estoque"])
        marca = f"{estoque} em estoque" if estoque > 0 else "SEM ESTOQUE"
        extras = " | ".join(x for x in [str(livro.get("ano") or ""),
                                         f"R$ {livro['preco']}" if livro.get("preco") else ""] if x)
        print(f"  [{livro['isbn']}] {livro['titulo']} — {livro.get('autor','')}"
              f"{' | ' + extras if extras else ''} ({marca})")
    return livros

def pedir():
    nome = input("Seu nome: ")
    email = input("Seu e-mail (o mesmo inscrito no topico SNS): ")
    isbn = input("ISBN do livro desejado: ")
    r = requests.post(config.URL_PEDIDO, timeout=15,
                      json={"nome": nome, "email": email, "isbn": isbn})
    if r.status_code == 200:
        dados = r.json()
        print(f"\n{dados['mensagem']}\nPedido: {formatar_pedido(dados)}")
        print(f"Status: {dados['status']}")
    else:
        print(f"Erro {r.status_code}: {r.text}")

if __name__ == "__main__":
    while True:
        print("\n=== Sebo PUC — Comprador ===")
        print("1) Ver acervo\n2) Pedir um livro\n0) Sair")
        opcao = input("> ").strip()
        if opcao == "1": listar()
        elif opcao == "2": pedir()
        elif opcao == "0": break
