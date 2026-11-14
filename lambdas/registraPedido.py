import os, json, uuid, boto3
from datetime import datetime, timezone

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
    isbn, email = corpo.get("isbn"), corpo.get("email")
    nome = corpo.get("nome", "")
    if not isbn or not email:
        return resposta(400, {"erro": "informe isbn e email"})

    livro = livros.get_item(Key={"isbn": isbn}).get("Item")
    if not livro:
        return resposta(404, {"erro": "livro nao cadastrado"})

    disponivel = int(livro.get("estoque", 0)) > 0
    agora = datetime.now(timezone.utc).isoformat()
    pedido_id = f"{agora}#{uuid.uuid4().hex[:8]}"

    if disponivel:
        livros.update_item(
            Key={"isbn": isbn},
            UpdateExpression="SET estoque = estoque - :um",
            ConditionExpression="estoque > :zero",
            ExpressionAttributeValues={":um": 1, ":zero": 0})

    pedidos.put_item(Item={
        "isbn": isbn, "pedidoId": pedido_id, "email": email, "nome": nome,
        "status": "RESERVADO" if disponivel else "AGUARDANDO",
        "criadoEm": agora})

    sqs.send_message(QueueUrl=FILA, MessageBody=json.dumps({
        "tipo": "RESERVA" if disponivel else "ESPERA",
        "email": email, "nome": nome, "isbn": isbn,
        "titulo": livro.get("titulo", isbn), "pedidoId": pedido_id},
        ensure_ascii=False))

    return resposta(200, {
        "status": "RESERVADO" if disponivel else "AGUARDANDO",
        "pedidoId": pedido_id,
        "mensagem": "Exemplar disponivel. Voce recebera um e-mail para retirar na livraria."
                    if disponivel else
                    "Sem estoque no momento. Voce entrou na lista de espera."})
