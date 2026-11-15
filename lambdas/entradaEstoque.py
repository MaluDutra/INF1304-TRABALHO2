import os, json, boto3
from decimal import Decimal, InvalidOperation
from boto3.dynamodb.conditions import Key, Attr

dynamodb = boto3.resource("dynamodb")
livros = dynamodb.Table(os.environ["TABELA_LIVROS"])
pedidos = dynamodb.Table(os.environ["TABELA_PEDIDOS"])
sqs = boto3.client("sqs")
FILA = os.environ["FILA_NOTIFICACAO"]

def resposta(status, corpo):
    return {"statusCode": status,
            "headers": {"Content-Type": "application/json",
                        "Access-Control-Allow-Origin": "*"},
            "body": json.dumps(corpo, default=str, ensure_ascii=False)}

def vazio(valor):
    return valor is None or str(valor).strip() == ""

def lambda_handler(event, context):
    corpo = json.loads(event["body"]) if isinstance(event.get("body"), str) else event
    isbn = str(corpo.get("isbn") or "").strip()
    if not isbn:
        return resposta(400, {"erro": "informe o isbn"})
    try:
        quantidade = int(corpo.get("quantidade", 1))
        ano = None if vazio(corpo.get("ano")) else int(corpo["ano"])
        preco = None if vazio(corpo.get("preco")) else Decimal(str(corpo["preco"]))
    except (ValueError, InvalidOperation):
        return resposta(400, {"erro": "quantidade, ano e preco devem ser numeros"})
    if quantidade < 0 or (preco is not None and preco < 0):
        return resposta(400, {"erro": "quantidade e preco nao podem ser negativos"})

    # campos informados sobrescrevem; campos vazios mantem o valor atual
    # (livro novo sem titulo fica com o isbn como titulo)
    novos = {"titulo": None if vazio(corpo.get("titulo")) else str(corpo["titulo"]).strip(),
             "autor": None if vazio(corpo.get("autor")) else str(corpo["autor"]).strip(),
             "ano": ano, "preco": preco}
    sets = ["#estoque = if_not_exists(#estoque, :zero) + :qtd"]
    nomes = {"#estoque": "estoque"}
    valores = {":qtd": quantidade, ":zero": 0}
    for campo, valor in novos.items():
        if valor is not None:
            sets.append(f"#{campo} = :{campo}")
            nomes[f"#{campo}"] = campo
            valores[f":{campo}"] = valor
    if novos["titulo"] is None:
        sets.append("#titulo = if_not_exists(#titulo, :isbn)")
        nomes["#titulo"] = "titulo"
        valores[":isbn"] = isbn
    if novos["autor"] is None:
        sets.append("#autor = if_not_exists(#autor, :semAutor)")
        nomes["#autor"] = "autor"
        valores[":semAutor"] = ""

    # cadastra o livro se for novo, atualiza os dados informados e soma ao estoque
    livro = livros.update_item(
        Key={"isbn": isbn},
        UpdateExpression="SET " + ", ".join(sets),
        ExpressionAttributeNames=nomes,
        ExpressionAttributeValues=valores,
        ReturnValues="ALL_NEW")["Attributes"]

    # lista de espera daquele livro, em ordem de chegada
    espera = pedidos.query(
        KeyConditionExpression=Key("isbn").eq(isbn),
        FilterExpression=Attr("status").eq("AGUARDANDO"),
        ScanIndexForward=True).get("Items", [])

    avisados = []
    for pedido in espera[:quantidade]:
        sqs.send_message(QueueUrl=FILA, MessageBody=json.dumps({
            "tipo": "CHEGOU", "email": pedido["email"],
            "nome": pedido.get("nome", ""), "isbn": isbn,
            "titulo": livro.get("titulo", isbn),
            "pedidoId": pedido["pedidoId"]}, ensure_ascii=False))

        pedidos.update_item(
            Key={"isbn": isbn, "pedidoId": pedido["pedidoId"]},
            UpdateExpression="SET #s = :novo",
            ConditionExpression="#s = :antigo",
            ExpressionAttributeNames={"#s": "status"},
            ExpressionAttributeValues={":novo": "RESERVADO",
                                       ":antigo": "AGUARDANDO"})

        livros.update_item(
            Key={"isbn": isbn},
            UpdateExpression="SET estoque = estoque - :um",
            ExpressionAttributeValues={":um": 1})
        avisados.append(pedido["email"])

    estoque_apos = int(livro["estoque"]) - len(avisados)
    return resposta(200, {"isbn": isbn, "titulo": livro.get("titulo"),
                          "autor": livro.get("autor", ""),
                          "ano": livro.get("ano"), "preco": livro.get("preco"),
                          "estoque": estoque_apos, "estoqueApos": estoque_apos,
                          "clientesAvisados": avisados})
