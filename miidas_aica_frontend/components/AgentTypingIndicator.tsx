"use client";

import React, { useEffect, useState } from "react";
import { Box } from "@mui/material";
import { ChatMessage } from "./ChatMessage";
import { ChatMessageRole } from "@/constants/enum";

export default function AgentTypingIndicator() {
  const [dots, setDots] = useState(".");

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => (prev.length < 3 ? prev + "." : "."));
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <Box className="chat-message-container message">
      <ChatMessage
        showIcon={true}
        role={ChatMessageRole.Agent}
        message={dots}
      />
    </Box>
  );
}
