import os, json, boto3

livros = boto3.resource("dynamodb").Table(os.environ["TABELA_LIVROS"])

def lambda_handler(event, context):
    itens = livros.scan().get("Items", [])
    itens.sort(key=lambda x: x.get("titulo", ""))
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(itens, default=str, ensure_ascii=False),
    }
