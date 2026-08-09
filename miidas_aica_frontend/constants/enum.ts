export enum ChatMessageRole {
  Agent = "assistant",
  User = "user",
}

export enum SocketStatus {
  Unknown,
  Disconnected,
  Connecting,
  Reconnecting,
  Connected,
  MessageSending,
  MessageSent,
  MessageReceiving,
  MessageReceived,
  ErrorReceived,
}

export enum SessionStatus {
  // 会話中
  Chatting = 10,
  // 会員登録中
  Registering = 100,
  // 面談応募中
  Applying = 110,
  // 会員登録済み
  Registered = 200,
  // 面談応募済み
  Applied = 210,
}

export enum Asset {
  MIIBO = "/assets/miibo.png",
}

export enum ApplyResult {
  BeforeApply = 0,
  Unknown = -999,
  InvalidSessionStatus = -10,
  RegisterAlready = 10,
  RegisterSuccess = 20,
  RegisterFail = 30,
  MeetingApplicationAlready = 40,
  MeetingApplicationSuccess = 50,
  MeetingApplicationFail = 60,
}

export enum ApplyValidationError {
  None = 0,
  DuplicateEmailOrPhone = 10,
  Other = 100,
}

export enum PageName {
  Chat = "Chat",
  PositionDetail = "PositionDetail",
  ProfileBasicInfo = "BasicInfo",
  ProfileCarrer = "Carrer",
  ProfileEducation = "Education",
  ProfileWill = "Will",
}

export enum PagePath {
  Chat = "/chat",
  PositionDetail = "/positions",
  ProfileBasicInfo = "/basic-info",
  ProfileCarrer = "/career",
  ProfileEducation = "/education",
  ProfileWill = "/will",
}

export enum SourceComponentNames {
  Position = "position",
  Recommendation = "recommendation",
}

export enum ChatRequestType {
  Start = "start",
  Chat = "chat",
  RestartChat = "restart_chat",
  LoadPreviousMessage = "load_previous_message",
  SummarizePosition = "summarize_position",
  JobTypesSelected = "job_types_selected",
  JobTypesClear = "job_types_clear",
  WorkflowAnswersSubmitted = "workflow_answers_submitted",
  WorkflowCancelled = "workflow_cancelled",
}

export enum ChatResponseType {
  Message = "message",
  PositionSearchResult = "position_search_result",
  PositionSearchLink = "position_search_link",
  JobtypeSearchResult = "jobtype_search_result",
  Workflow = "workflow",
  RestartWorkflow = "restart_workflow",
  Error = "error",
  End = "end",
}

export function chatResponseTypeToItemType(
  responseType: ChatResponseType,
): ItemType {
  switch (responseType) {
    case ChatResponseType.Message:
      return ItemType.ChatMessage;
    case ChatResponseType.PositionSearchResult:
      return ItemType.PositionSearchResult;
    case ChatResponseType.PositionSearchLink:
      return ItemType.PositionSearchLink;
    case ChatResponseType.JobtypeSearchResult:
      return ItemType.JobtypeSearchResult;
    case ChatResponseType.Workflow:
      return ItemType.Workflow;
    case ChatResponseType.Error:
      return ItemType.Error;
    case ChatResponseType.RestartWorkflow:
      // 履歴API専用タイプであり、Websocketでは送信されない想定。
      // Websocketで受信した場合はUnknownとして扱う。
      return ItemType.Unknown;
    default:
      return ItemType.Unknown;
  }
}

export enum ItemType {
  ChatMessage = "chat_message",
  PositionSearchResult = "position_search_result",
  PositionSearchLink = "position_search_link",
  JobtypeSearchResult = "jobtype_search_result",
  Workflow = "workflow",
  RestartWorkflowButton = "restart_workflow_button",
  Error = "error",
  Unknown = "unknown",
}

export function isMessage(itemType: ItemType): boolean {
  return itemType === ItemType.ChatMessage;
}

export function isPositionSearchResult(itemType: ItemType): boolean {
  return itemType === ItemType.PositionSearchResult;
}

export function isPositionSearchLink(itemType: ItemType): boolean {
  return itemType === ItemType.PositionSearchLink;
}

export function isJobtypeSearchResult(itemType: ItemType): boolean {
  return itemType === ItemType.JobtypeSearchResult;
}

export function isWorkflow(itemType: ItemType): boolean {
  return itemType === ItemType.Workflow;
}

export function isRestartWorkflowButton(itemType: ItemType): boolean {
  return itemType === ItemType.RestartWorkflowButton;
}

export enum ChatHistoryRetrievalStatus {
  NotStarted = "not_started",
  Start = "start",
  Loading = "loading",
  Finished = "finished",
}

export enum ScrollEventType {
  None,
  // 新しいユーザーメッセージ送信
  NewUserMessage,
  // 新しいAgentメッセージ受信
  NewAgentMessage,
  // ポジション検索ツール結果が来た
  NewPositionSearchResult,
  // ポジション詳細から戻ってきた
  BackFromPositionDetail,
  // 過去履歴取得中
  PreviousMessagesLoading,
  // 過去履歴取得完了
  PreviousMessagesLoaded,
  // ポジション検索条件取得
  JobSearchFilterRetrieving,
  // プロフィール保存できた
  ProfileSaved,
  // websocket切断
  Disconnected,
  // websocket接続済み
  Connected,
}

export enum WorkflowDisplayType {
  Modal = "modal",
  Inline = "inline",
}

export enum WorkflowStepSelectionType {
  Single = "single",
  Multiple = "multiple",
}
