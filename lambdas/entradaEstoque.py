import os, json, boto3
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

def lambda_handler(event, context):
    corpo = json.loads(event["body"]) if isinstance(event.get("body"), str) else event
    isbn = corpo.get("isbn")
    if not isbn:
        return resposta(400, {"erro": "informe o isbn"})
    quantidade = int(corpo.get("quantidade", 1))

    # cadastra o livro se for novo e soma ao estoque
    livro = livros.update_item(
        Key={"isbn": isbn},
        UpdateExpression=("SET estoque = if_not_exists(estoque, :zero) + :qtd, "
                          "titulo = if_not_exists(titulo, :tit), "
                          "autor = if_not_exists(autor, :aut)"),
        ExpressionAttributeValues={":qtd": quantidade, ":zero": 0,
                                   ":tit": corpo.get("titulo", isbn),
                                   ":aut": corpo.get("autor", "")},
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

    return resposta(200, {"isbn": isbn, "titulo": livro.get("titulo"),
                          "estoqueApos": int(livro["estoque"]) - len(avisados),
                          "clientesAvisados": avisados})
