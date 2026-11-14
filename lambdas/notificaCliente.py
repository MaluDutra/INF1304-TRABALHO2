import os, json, boto3

sns = boto3.client("sns")
TOPICO = os.environ["TOPICO_ARN"]

MODELOS = {
    "RESERVA": ("Livraria: seu livro esta reservado",
        "Olá {nome},\n\nO livro \"{titulo}\" está disponível e foi reservado para você.\n"
        "Compareça à livraria em até 48 horas para efetivar a compra.\n\nPedido: {pedidoId}"),
    "ESPERA": ("Livraria: pedido registrado",
        "Olá {nome},\n\nO livro \"{titulo}\" está sem estoque no momento.\n"
        "Você entrou na lista de espera e será avisado assim que chegar um exemplar."),
    "CHEGOU": ("Livraria: o livro que voce queria chegou",
        "Olá {nome},\n\nChegou um exemplar de \"{titulo}\", reservado em seu nome.\n"
        "Compareça à livraria para efetivar a compra.\n\nPedido: {pedidoId}"),
}

def lambda_handler(event, context):
    enviados = 0
    for record in event["Records"]:
        msg = json.loads(record["body"])
        assunto, modelo = MODELOS[msg["tipo"]]
        sns.publish(
            TopicArn=TOPICO,
            Subject=assunto,
            Message=modelo.format(nome=msg.get("nome") or "cliente",
                                  titulo=msg["titulo"],
                                  pedidoId=msg.get("pedidoId", "-")),
            MessageAttributes={"email": {"DataType": "String",
                                         "StringValue": msg["email"]}})
        print(f"notificado {msg['email']} tipo={msg['tipo']}")
        enviados += 1
    return {"enviados": enviados}
