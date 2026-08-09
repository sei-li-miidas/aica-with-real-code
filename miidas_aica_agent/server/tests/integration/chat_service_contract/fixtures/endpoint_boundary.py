"""エンドポイント境界の検証に使う fixture。

この fixture には、websocket と REST の entrypoint が concrete な
legacy chat service や hardcoded な agent model 値から分離されているかを
確認するために、endpoint module に含まれていてはいけない文字列を定義する。
"""

FORBIDDEN_IMPORT_STRINGS = (
    "from services.chat_service import ChatService",
    "services.chat_service",
)
FORBIDDEN_MODEL_LITERAL = "openai/gpt-4.1"
