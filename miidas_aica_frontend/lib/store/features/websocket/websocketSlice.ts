import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { AppThunk } from "@/lib/store";
import {
  IItem,
  IMessageItem,
  IPositionSearchResultItem,
  IPositionSummary,
  IWorkflowItem,
} from "@/lib/common";
import {
  ChatHistoryRetrievalStatus,
  ChatMessageRole,
  ScrollEventType,
  SessionStatus,
  SocketStatus,
} from "@/constants/enum";
import { SESSION_KEY } from "@/constants/localStorage";

const updatePositionsFromSearchResult = (
  currentPositions: IPositionSummary[],
  newPositions: IPositionSummary[],
): {
  updatedPositions: IPositionSummary[];
  positionReferences: IPositionSummary[];
} => {
  const updatedPositions = [...currentPositions];

  newPositions.forEach((newPosition) => {
    const existingIndex = updatedPositions.findIndex(
      (pos) => pos.ID === newPosition.ID,
    );

    if (existingIndex !== -1) {
      // 既存ポジションを更新しますが、messagesはそのまま
      const { messages, ...positionWithoutMessages } = newPosition;
      void messages; // This explicitly tells ESLint the variable is intentionally used
      updatedPositions[existingIndex] = {
        ...updatedPositions[existingIndex],
        ...positionWithoutMessages,
        messages: updatedPositions[existingIndex].messages,
      };
    } else {
      // itemsが空の新規ポジション追加
      updatedPositions.push({
        ...newPosition,
        messages: [],
      });
    }
  });

  // 以前検索済みのポジションに差し替えます
  const positionReferences = newPositions.map((pos) => {
    const statePosition = updatedPositions.find((p) => p.ID === pos.ID);
    return statePosition || pos;
  });

  return { updatedPositions, positionReferences };
};

export interface IWebSocketState {
  sessionStatus: SessionStatus;
  socketStatus: SocketStatus;
  sessionID: string;
  // 会話履歴
  items: IItem[];
  // ユーザーへの提案ポジションリスト（ポジション検索結果＋おすすめ）
  positions: IPositionSummary[];
  currentPage: string;
  // 過去履歴取得ステータス（メインチャット用）
  mainHistoryRetrievalStatus: ChatHistoryRetrievalStatus;
  // 過去履歴はまだあるか（ポジション別）- positionID をキーとする
  positionHistoryRetrievalStatus: Record<string, ChatHistoryRetrievalStatus>;
  // 過去履歴はまだあるか（メインチャット用）
  mainChatHasMoreHistory: boolean;
  // 過去履歴はまだあるか（ポジション別）- positionID をキーとする
  positionHistoryState: Record<string, boolean>;
  // スクロールをトリガーするイベント
  scrollEventType: ScrollEventType;
  // スクロールイベントのシーケンス（同じType連続でも発火させるため）
  scrollEventId: number;
  // メンテモードに入ったときのメッセージ
  maintenanceMessage: null | string;
  // 現在実行中のモーダルワークフロー
  modalWorkflow: IWorkflowItem | null;
  // 現在実行中のインラインワークフロー
  inlineWorkflow: IWorkflowItem | null;
  // 押下済みで非表示にするワークフロー再実行ボタンの itemId リスト
  dismissedRestartWorkflowIds: string[];
}

const initialState: IWebSocketState = {
  sessionStatus: SessionStatus.Chatting,
  socketStatus: SocketStatus.Unknown,
  sessionID: "",
  // 会話履歴アイテム（メッセージアイテムか、ポジション検索結果アイテム）
  items: [],
  positions: [],
  currentPage: "",
  mainHistoryRetrievalStatus: ChatHistoryRetrievalStatus.NotStarted,
  positionHistoryRetrievalStatus: {},
  mainChatHasMoreHistory: false,
  positionHistoryState: {},
  scrollEventType: ScrollEventType.None,
  // scrollEventType更新時に、値が変わらない場合、イベントがトリガーされない。
  // そのため、イベントは常にトリガーされるようscrollEventIdを追加しました
  scrollEventId: 0,
  maintenanceMessage: null,
  modalWorkflow: null,
  inlineWorkflow: null,
  dismissedRestartWorkflowIds: [],
};

const websocketSlice = createSlice({
  name: "websocket",
  initialState,
  reducers: {
    setSessionStatus(state, action: PayloadAction<SessionStatus>) {
      state.sessionStatus = action.payload;
    },
    setSocketStatus(state, action: PayloadAction<SocketStatus>) {
      state.socketStatus = action.payload;
    },
    setModalWorkflow: (state, action: PayloadAction<IWorkflowItem | null>) => {
      state.modalWorkflow = action.payload;
    },
    setInlineWorkflow: (state, action: PayloadAction<IWorkflowItem | null>) => {
      state.inlineWorkflow = action.payload;
    },
    dismissRestartWorkflowButton: (state, action: PayloadAction<string>) => {
      if (!state.dismissedRestartWorkflowIds.includes(action.payload)) {
        state.dismissedRestartWorkflowIds.push(action.payload);
      }
    },
    setConnected: (state, action: PayloadAction<string | null>) => {
      state.socketStatus = SocketStatus.Connected;
      state.sessionID = action.payload ?? "";
      state.scrollEventType = ScrollEventType.Connected;
      state.scrollEventId += 1;
    },
    setDisconnected: (state) => {
      state.socketStatus = SocketStatus.Disconnected;
      state.scrollEventType = ScrollEventType.Disconnected;
      state.scrollEventId += 1;
    },
    setSessionID: (state, action: PayloadAction<string>) => {
      state.sessionID = action.payload;
    },
    addOrUpdateMainChatMessageItem: (
      state,
      action: PayloadAction<IMessageItem>,
    ) => {
      // メインチャットのメッセージ追加/更新
      const newItem = action.payload;

      const existingIndex = state.items.findIndex(
        (item) => item.itemId === newItem.itemId,
      );

      if (existingIndex !== -1) {
        // 既存メッセージアイテムの更新
        const existingItem = state.items[existingIndex] as IMessageItem;
        state.items[existingIndex] = {
          ...existingItem,
          message: existingItem.message + newItem.message,
        } as IMessageItem;
      } else {
        // 新規メッセージアイテム追加
        state.items.push(newItem);
      }

      state.scrollEventType =
        newItem.role === ChatMessageRole.User
          ? ScrollEventType.NewUserMessage
          : ScrollEventType.NewAgentMessage;
      state.scrollEventId += 1;
    },
    addMainChatNonMessageItem: (state, action: PayloadAction<IItem>) => {
      // メインチャットにメッセージ以外のアイテムを追加
      const newItem = action.payload;
      const alreadyExists = state.items.some(
        (item) => item.itemId === newItem.itemId,
      );

      if (!alreadyExists) {
        state.items.push(newItem);
      }

      state.scrollEventType = ScrollEventType.NewAgentMessage;
      state.scrollEventId += 1;
    },
    addMainChatPositionSearchResultItem: (
      state,
      action: PayloadAction<IPositionSearchResultItem>,
    ) => {
      // メインチャットのポジション検索結果追加
      const newItem = action.payload;

      const { updatedPositions, positionReferences } =
        updatePositionsFromSearchResult(
          state.positions,
          newItem.positionSearchResult.Positions,
        );

      state.positions = updatedPositions;

      // 複数回のポジション検索結果に同じポジションが入っている可能性がありますので、
      // ユーザーへの提案ポジションリストより全体的に管理しているので、その中のポジションのreference利用
      newItem.positionSearchResult = {
        ...newItem.positionSearchResult,
        Positions: positionReferences,
      };

      // 新規アイテム追加
      state.items.push(newItem);

      state.scrollEventType = ScrollEventType.NewPositionSearchResult;
      state.scrollEventId += 1;
    },
    updateMainChatExistingPositionSearchResultItem: (
      state,
      action: PayloadAction<{
        itemId: string;
        newPositions: IPositionSummary[];
      }>,
    ) => {
      // メインチャットのポジション検索結果追加
      const { itemId, newPositions } = action.payload;

      const { updatedPositions, positionReferences } =
        updatePositionsFromSearchResult(state.positions, newPositions);

      state.positions = updatedPositions;

      const existingIndex = state.items.findIndex(
        (item) => item.itemId === itemId,
      );

      if (existingIndex !== -1) {
        const existingItem = state.items[
          existingIndex
        ] as IPositionSearchResultItem;
        // 既存ポジション検索結果アイテムの更新
        state.items[existingIndex] = {
          ...existingItem,
          positionSearchResult: {
            ...existingItem.positionSearchResult,
            Positions: [
              // 前回まで検索できたポジション
              ...existingItem.positionSearchResult.Positions,
              // 今回検索してきたポジション
              ...positionReferences,
            ],
          },
        } as IPositionSearchResultItem;
      }
    },
    replaceMainChatPositionSearchLink: (
      state,
      action: PayloadAction<IPositionSearchResultItem>,
    ) => {
      const newItem = action.payload;
      const existingIndex = state.items.findIndex(
        (item) => item.itemId === newItem.itemId,
      );

      if (existingIndex !== -1) {
        state.items[existingIndex] = newItem;
      }
    },
    addOrUpdatePositionChatMessageItem: (
      state,
      action: PayloadAction<{
        positionID: string;
        newItem: IMessageItem;
      }>,
    ) => {
      // ポジション詳細チャットの会話履歴更新
      const { newItem, positionID } = action.payload;

      // ユーザーへの提案ポジションリストからIDがaction.payload.positionIDのアイテムを探します。
      const positionIndex = state.positions.findIndex(
        (pos) => pos.ID.toString() === positionID,
      );

      if (positionIndex !== -1) {
        const position = state.positions[positionIndex];
        const existingIndex = position.messages.findIndex(
          (message) => message.itemId === newItem.itemId,
        );

        if (existingIndex !== -1) {
          // 既存アイテム更新
          state.positions[positionIndex].messages[existingIndex] = {
            ...state.positions[positionIndex].messages[existingIndex],
            message:
              state.positions[positionIndex].messages[existingIndex].message +
              newItem.message,
          };
        } else {
          // 新規アイテム追加
          state.positions[positionIndex].messages.push(newItem);
        }

        state.scrollEventType =
          newItem.role === ChatMessageRole.User
            ? ScrollEventType.NewUserMessage
            : ScrollEventType.NewAgentMessage;
        state.scrollEventId += 1;
      }
    },
    resetHistoryRetrieval: (state, action: PayloadAction<string | null>) => {
      const positionID = action.payload;
      if (positionID) {
        state.positionHistoryRetrievalStatus[positionID] =
          ChatHistoryRetrievalStatus.NotStarted;
      } else {
        state.mainHistoryRetrievalStatus =
          ChatHistoryRetrievalStatus.NotStarted;
      }
    },
    triggerHistoryRetrieval: (state, action: PayloadAction<string | null>) => {
      const positionID = action.payload;
      if (positionID) {
        state.positionHistoryRetrievalStatus[positionID] =
          ChatHistoryRetrievalStatus.Start;
      } else {
        state.mainHistoryRetrievalStatus = ChatHistoryRetrievalStatus.Start;
      }
    },
    startHistoryRetrieval: (state, action: PayloadAction<string | null>) => {
      const positionID = action.payload;
      if (positionID) {
        state.positionHistoryRetrievalStatus[positionID] =
          ChatHistoryRetrievalStatus.Loading;
      } else {
        state.mainHistoryRetrievalStatus = ChatHistoryRetrievalStatus.Loading;
      }
    },
    finishHistoryRetrieval: (state, action: PayloadAction<string | null>) => {
      const positionID = action.payload;
      if (positionID) {
        state.positionHistoryRetrievalStatus[positionID] =
          ChatHistoryRetrievalStatus.Finished;
      } else {
        state.mainHistoryRetrievalStatus = ChatHistoryRetrievalStatus.Finished;
      }
    },
    setHasMoreHistory: (
      state,
      action: PayloadAction<{
        positionID: string | null;
        hasMoreHistory: boolean;
      }>,
    ) => {
      const { positionID, hasMoreHistory } = action.payload;
      if (positionID) {
        // Position chat
        state.positionHistoryState[positionID] = hasMoreHistory;
      } else {
        // Main chat
        state.mainChatHasMoreHistory = hasMoreHistory;
      }
    },
    resetHistoryState: (state, action: PayloadAction<string | null>) => {
      const positionID = action.payload;
      if (positionID) {
        state.positionHistoryState[positionID] = true;
        state.positionHistoryRetrievalStatus[positionID] =
          ChatHistoryRetrievalStatus.NotStarted;
      } else {
        state.mainChatHasMoreHistory = true;
        state.mainHistoryRetrievalStatus =
          ChatHistoryRetrievalStatus.NotStarted;
      }
    },
    prependMainChatItem: (state, action: PayloadAction<IItem>) => {
      // メインチャットの会話履歴に過去のメッセージを追加
      const newItem = action.payload;
      const alreadyExists = state.items.some(
        (item) => item.itemId === newItem.itemId,
      );

      if (!alreadyExists) {
        state.items.unshift(newItem);
      }

      state.scrollEventType = ScrollEventType.PreviousMessagesLoading;
      state.scrollEventId += 1;
    },
    prependPositionChatItems: (
      state,
      action: PayloadAction<{ newItem: IMessageItem; positionID: string }>,
    ) => {
      // 過去のメッセージを先頭に1件追加するアクション
      const { newItem, positionID } = action.payload;

      // ポジション詳細チャットの会話履歴に過去のメッセージを追加
      const positionIndex = state.positions.findIndex(
        (pos) => pos.ID.toString() === positionID,
      );

      if (positionIndex !== -1) {
        const messages = state.positions[positionIndex].messages;
        const alreadyExists = messages.some(
          (message) => message.itemId === newItem.itemId,
        );

        if (!alreadyExists) {
          messages.unshift(newItem);
        }
      }

      state.scrollEventType = ScrollEventType.PreviousMessagesLoading;
      state.scrollEventId += 1;
    },
    setCurrentPage: (state, action: PayloadAction<string>) => {
      state.currentPage = action.payload;
    },
    updatePositions: (state, action: PayloadAction<IPositionSummary[]>) => {
      const { updatedPositions } = updatePositionsFromSearchResult(
        state.positions,
        action.payload,
      );
      state.positions = updatedPositions;
    },
    updateScrollEventType: (state, action: PayloadAction<ScrollEventType>) => {
      state.scrollEventType = action.payload;
      state.scrollEventId += 1;
    },
    updateMaintenanceMessage: (state, action: PayloadAction<null | string>) => {
      state.maintenanceMessage = action.payload;
    },
  },
});

export const saveSessionID =
  (sessionID: string): AppThunk =>
  (dispatch) => {
    localStorage.setItem(SESSION_KEY, sessionID);
    dispatch(websocketSlice.actions.setSessionID(sessionID));
  };

export const {
  setSessionStatus,
  setSocketStatus,
  setConnected,
  setDisconnected,
  setSessionID,
  addOrUpdateMainChatMessageItem,
  addMainChatNonMessageItem,
  addMainChatPositionSearchResultItem,
  updateMainChatExistingPositionSearchResultItem,
  replaceMainChatPositionSearchLink,
  addOrUpdatePositionChatMessageItem,
  updatePositions,
  resetHistoryRetrieval,
  triggerHistoryRetrieval,
  startHistoryRetrieval,
  finishHistoryRetrieval,
  setHasMoreHistory,
  resetHistoryState,
  prependMainChatItem,
  prependPositionChatItems,
  setCurrentPage,
  setModalWorkflow,
  setInlineWorkflow,
  dismissRestartWorkflowButton,
  updateScrollEventType,
  updateMaintenanceMessage,
} = websocketSlice.actions;
export default websocketSlice.reducer;
