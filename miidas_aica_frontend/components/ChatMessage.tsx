import "./ChatMessage.scss";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import Box from "@mui/material/Box";
import Miibo from "@/components/icons/Miibo";
import { ChatMessageRole } from "@/constants/enum";

export interface IChatMessageProps {
  showIcon: boolean;
  role: ChatMessageRole;
  message: string;
}

export function ChatMessage(props: IChatMessageProps) {
  return (
    <>
      {props.showIcon && props.role === ChatMessageRole.Agent && (
        <Box className="role agent">
          <Miibo />
        </Box>
      )}
      {props.role === ChatMessageRole.Agent && (
        <Box className="chat-message-content agent">
          <Markdown remarkPlugins={[remarkGfm]}>{props.message}</Markdown>
        </Box>
      )}
      {props.role === ChatMessageRole.User && (
        <Box className="chat-message-content user">{props.message}</Box>
      )}
    </>
  );
}
