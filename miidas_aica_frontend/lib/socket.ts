import { ChatRequestType, SocketStatus } from "@/constants/enum";
import { CareerAgentAPI } from "./api";
import type { AppDispatch } from "@/lib/store";
import { setSocketStatus } from "./store/features/websocket/websocketSlice";

let socket: CareerAgentAPI | null = null;

export const setSocket = (ws: CareerAgentAPI) => {
  socket = ws;
};

export const sendWebSocketMessage = (
  dispatch: AppDispatch,
  request_type: ChatRequestType,
  previousPage: string,
  currentPage: string,
  message?: string | null,
  positionID?: string | null,
  currentMessageId?: string | null,
  isVoice?: boolean | null,
): boolean => {
  if (socket && socket.isConnected()) {
    const input = {
      request_type: request_type,
      current_page: currentPage,
      previous_page: previousPage,
      message: message,
      position_id: positionID,
      current_message_id: currentMessageId,
      is_voice: isVoice,
    };
    console.debug("sendWebSocketMessage with input =", input);

    dispatch(setSocketStatus(SocketStatus.MessageSending));

    // WebSocketメッセージのペイロードで不要な空のフィールドを送信しないように、
    // 以下のreplacer関数でundefined、null、空文字列の値をフィルタリングします。
    socket?.send(
      JSON.stringify(input, (_, value) => {
        return value === undefined || value === null || value === ""
          ? undefined
          : value;
      }),
    );

    dispatch(setSocketStatus(SocketStatus.MessageSent));

    return true;
  } else {
    console.warn("[WebSocket] Tried to send but socket is not open");
    return false;
  }
};
