import requests, config

def dar_entrada():
    print("(campos em branco mantem o valor ja cadastrado)")
    isbn = input("ISBN: ").strip()
    corpo = {"isbn": isbn,
             "quantidade": int(input("Quantidade recebida [1]: ") or 1)}
    for campo, rotulo in [("titulo", "Titulo"), ("autor", "Autor"),
                          ("ano", "Ano"), ("preco", "Preco (ex: 24.90)")]:
        valor = input(f"{rotulo}: ").strip()
        if valor:
            corpo[campo] = valor
    r = requests.post(config.URL_ESTOQUE, timeout=30, json=corpo)
    if r.status_code != 200:
        print(f"Erro {r.status_code}: {r.text}")
        return
    dados = r.json()
    print(f"\n{dados['titulo']} — {dados.get('autor') or 'autor desconhecido'}"
          f" | ano: {dados.get('ano') or '-'} | preco: {dados.get('preco') or '-'}")
    print(f"Estoque disponivel: {dados['estoqueApos']}")
    avisados = dados["clientesAvisados"]
    print("Ninguem na lista de espera." if not avisados
          else f"Clientes avisados por e-mail: {', '.join(avisados)}")

if __name__ == "__main__":
    dar_entrada()
