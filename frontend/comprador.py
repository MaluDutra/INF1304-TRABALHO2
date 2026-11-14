import requests, config

def listar():
    livros = requests.get(config.URL_CATALOGO, timeout=15).json()
    print()
    for livro in livros:
        estoque = int(livro["estoque"])
        marca = f"{estoque} em estoque" if estoque > 0 else "SEM ESTOQUE"
        print(f"  [{livro['isbn']}] {livro['titulo']} — {livro.get('autor','')} ({marca})")
    return livros

def pedir():
    nome = input("Seu nome: ")
    email = input("Seu e-mail (o mesmo inscrito no topico SNS): ")
    isbn = input("ISBN do livro desejado: ")
    r = requests.post(config.URL_PEDIDO, timeout=15,
                      json={"nome": nome, "email": email, "isbn": isbn})
    if r.status_code == 200:
        dados = r.json()
        print(f"\n{dados['mensagem']}\nPedido: {dados['pedidoId']}")
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
