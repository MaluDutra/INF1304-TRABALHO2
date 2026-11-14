import os, json, boto3
from datetime import datetime, timedelta

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

def numero_pedido(pedido_id):
    """Deixa o pedidoId apresentavel no e-mail.

    2026-11-14T18:40:12.345678+00:00#a1b2c3d4  ->  A1B2C3D4 (14/11/2026 as 15:40)
    O id guardado no DynamoDB continua o mesmo: so muda o que o cliente le.
    """
    if "#" not in pedido_id:
        return pedido_id
    criado, codigo = pedido_id.split("#", 1)
    try:
        # o timestamp e gravado em UTC; -3h para o horario de Brasilia
        quando = datetime.fromisoformat(criado) + timedelta(hours=-3)
    except ValueError:
        return codigo.upper()
    return f"{codigo.upper()} ({quando.strftime('%d/%m/%Y as %H:%M')})"


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
                                  pedidoId=numero_pedido(msg.get("pedidoId", "-"))),
            MessageAttributes={"email": {"DataType": "String",
                                         "StringValue": msg["email"]}})
        print(f"notificado {msg['email']} tipo={msg['tipo']}")
        enviados += 1
    return {"enviados": enviados}
