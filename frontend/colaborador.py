import requests, config

def dar_entrada():
    isbn = input("ISBN: ")
    titulo = input("Titulo (so para livro novo): ")
    autor = input("Autor (so para livro novo): ")
    quantidade = int(input("Quantidade recebida [1]: ") or 1)
    r = requests.post(config.URL_ESTOQUE, timeout=30,
                      json={"isbn": isbn, "titulo": titulo,
                            "autor": autor, "quantidade": quantidade})
    if r.status_code != 200:
        print(f"Erro {r.status_code}: {r.text}")
        return
    dados = r.json()
    print(f"\n{dados['titulo']} — estoque disponivel: {dados['estoqueApos']}")
    avisados = dados["clientesAvisados"]
    print("Ninguem na lista de espera." if not avisados
          else f"Clientes avisados por e-mail: {', '.join(avisados)}")

if __name__ == "__main__":
    dar_entrada()
