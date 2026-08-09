import { PageName, SessionStatus, SocketStatus } from "@/constants/enum";

export type ChatFooterMode =
  | "applyAction"
  | "input"
  | "reconnecting"
  | "inlineWorkflow";

export type HideFooterReason =
  | "applyLoading"
  | "applyingProfileIncomplete"
  | "modalWorkflow"
  | "initialMenuWorkflow"
  | "visible";

export type ChatFooterViewStateInput = {
  currentPage: string;
  sessionStatus: SessionStatus;
  socketStatus: SocketStatus;
  applyLoading: boolean;
  profileCompleted: boolean;
  isModalWorkflowActive: boolean;
  isInlineWorkflowActive: boolean;
  isInitialMenuWorkflow: boolean;
};

export function isApplyingSession(sessionStatus: SessionStatus): boolean {
  return (
    sessionStatus === SessionStatus.Applying ||
    sessionStatus === SessionStatus.Registering
  );
}

export function isJobSearchFilterVisible(
  input: ChatFooterViewStateInput,
): boolean {
  return (
    input.currentPage === PageName.Chat &&
    !isApplyingSession(input.sessionStatus) &&
    !input.applyLoading
  );
}

export function getFooterMode(input: ChatFooterViewStateInput): ChatFooterMode {
  if (
    input.currentPage === PageName.Chat &&
    isApplyingSession(input.sessionStatus) &&
    input.profileCompleted
  ) {
    return "applyAction";
  }

  if (input.socketStatus < SocketStatus.Connected) {
    return "reconnecting";
  }

  if (input.isInlineWorkflowActive) {
    return "inlineWorkflow";
  }

  return "input";
}

export function getHideFooterReason(
  input: ChatFooterViewStateInput,
): HideFooterReason {
  if (input.applyLoading) {
    return "applyLoading";
  }

  if (
    input.currentPage === PageName.Chat &&
    isApplyingSession(input.sessionStatus) &&
    !input.profileCompleted
  ) {
    return "applyingProfileIncomplete";
  }

  if (input.isModalWorkflowActive) {
    return "modalWorkflow";
  }

  if (input.isInitialMenuWorkflow && input.socketStatus >= SocketStatus.Connected) {
    // 初期メニューワークフローはフッターを表示しない（再接続中の表示は行う）
    return "initialMenuWorkflow";
  }

  return "visible";
}

export function shouldShowAgentTypingIndicator(
  socketStatus: SocketStatus,
): boolean {
  return (
    socketStatus === SocketStatus.MessageSending ||
    socketStatus === SocketStatus.MessageSent
  );
}
