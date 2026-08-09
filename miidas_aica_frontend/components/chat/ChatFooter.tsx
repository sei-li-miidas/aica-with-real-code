import React from "react";
import UserInput from "@/components/UserInput";
import ReconnectingIndicator from "@/components/ReconnectingIndicator";
import { SessionStatus } from "@/constants/enum";
import { Button } from "@mui/material";
import type { ChatFooterMode } from "@/components/chat/chatViewModel";

type ChatFooterProps = {
  footerMode: ChatFooterMode;
  sessionStatus: SessionStatus;
  onApply: () => void;
  onSendUserInput: (value: string, isVoice: boolean) => void;
  onCancelWorkflow: () => void;
};

export default function ChatFooter({
  footerMode,
  sessionStatus,
  onApply,
  onSendUserInput,
  onCancelWorkflow,
}: ChatFooterProps) {
  return (
    <div data-testid="chat-footer">
      {footerMode === "applyAction" && (
        <div className="apply-actions" data-testid="chat-footer-apply-action">
          <Button
            form="will-form"
            variant="contained"
            className="apply-button"
            onClick={onApply}
          >
            {sessionStatus == SessionStatus.Registering
              ? "ミイダスに登録する"
              : "ミイダスに登録してカジュアル面談を申し込む"}
          </Button>
        </div>
      )}

      {footerMode === "input" && (
        <div className="chat-footer__inner">
          <UserInput sendCallback={onSendUserInput} />
        </div>
      )}

      {footerMode === "reconnecting" && <ReconnectingIndicator />}

      {footerMode === "inlineWorkflow" && (
        <div className="workflow-actions">
          <Button
            variant="contained"
            className="cancel-button"
            onClick={onCancelWorkflow}
          >
            中断する
          </Button>
        </div>
      )}
    </div>
  );
}
