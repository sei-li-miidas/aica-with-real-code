from fastapi import Request, WebSocket


def get_client_ip(connection: Request | WebSocket) -> str:
    """
    アクセス元のIPアドレスを取得する
    ALBを経由しているため、X-Forwarded-Forヘッダーを優先的に利用する
    Args:
        connection: RequestまたはWebSocketオブジェクト
    Returns:
        str: アクセス元のIPアドレス
    """
    x_forwarded_for = connection.headers.get("X-Forwarded-For")

    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    if connection.client:
        return connection.client.host

    return "Unknown"
