import { useCallback, useMemo } from "react";

import {
  useAppDispatch,
  useAppSelector,
  useHasMoreHistory,
  useHistoryRetrievalStatus,
} from "@/lib/store/hooks";
import {
  createJobtypeSearchResultItem,
  createNormalMessageItem,
  createPositionSearchLinkItem,
  createRestartWorkflowButtonItem,
  createWorkflowItem,
  IItem,
} from "@/lib/common";
import {
  ChatHistoryRetrievalStatus,
  ChatMessageRole,
  ChatResponseType,
  PageName,
  ScrollEventType,
  WorkflowDisplayType,
} from "@/constants/enum";
import {
  finishHistoryRetrieval,
  prependMainChatItem,
  prependPositionChatItems,
  setHasMoreHistory,
  setInlineWorkflow,
  startHistoryRetrieval,
  updateScrollEventType,
} from "@/lib/store/features/websocket/websocketSlice";
import { fetchApiData } from "@/utils/fetch";

interface UseChatHistoryOptions {
  currentPage: PageName | string;
  positionID?: string | null;
}

export const useChatHistory = ({
  currentPage,
  positionID,
}: UseChatHistoryOptions) => {
  const dispatch = useAppDispatch();
  const hasMoreHistory = useHasMoreHistory(positionID || null);
  const historyRetrievalStatus = useHistoryRetrievalStatus(positionID || null);
  const { items, positions } = useAppSelector((state) => state.websocket);

  const itemsOfCurrentPage = useMemo<IItem[]>(() => {
    if (currentPage === PageName.Chat) {
      return items;
    }

    if (!positionID) {
      return [];
    }

    const position = positions.find((pos) => pos?.ID.toString() === positionID);
    return position?.messages || [];
  }, [items, positions, currentPage, positionID]);

  /**
   * メインチャットまたはポジション詳細チャットの過去のチャットメッセージを読み込みます。
   *
   * @param init true: メインチャットページ初期ロードまたリロード
   * その場合、読み込み完了時にページの一番下にして、最新メッセージをユーザーに見せます。
   * デフォルト（メインチャットページ初期ロード以外の場合）は false のままにしてください。
   */
  const loadPreviousMessages = useCallback(
    (init = false) => {
      if (historyRetrievalStatus === ChatHistoryRetrievalStatus.Loading) {
        return;
      }

      dispatch(startHistoryRetrieval(positionID || null));

      let url = "chat/previous";
      if (positionID) {
        url += `/${positionID}`;
      }

      if (itemsOfCurrentPage.length > 0) {
        url += `?before_id=${itemsOfCurrentPage[0].itemId}`;
      }

      fetchApiData(url, "過去のメッセージ取得に失敗しました")
        .then((res) => {
          if (
            Array.isArray(res.data?.PreviousChatHistories) &&
            res.data.PreviousChatHistories.length > 0
          ) {
            for (const history of res.data.PreviousChatHistories) {
              try {
              if (positionID) {
                const item = createNormalMessageItem(
                  history.Role as ChatMessageRole,
                  history.MessageID,
                  history.Message,
                );
                dispatch(
                  prependPositionChatItems({ newItem: item, positionID }),
                );
              } else if (history.Type === ChatResponseType.Message) {
                const item = createNormalMessageItem(
                  history.Role as ChatMessageRole,
                  history.MessageID,
                  history.Message,
                );
                dispatch(prependMainChatItem(item));
              } else if (history.Type === ChatResponseType.PositionSearchLink) {
                const item = createPositionSearchLinkItem(
                  history.MessageID,
                  history.Message,
                );
                dispatch(prependMainChatItem(item));
              } else if (
                history.Type === ChatResponseType.JobtypeSearchResult
              ) {
                const item = createJobtypeSearchResultItem(
                  history.MessageID,
                  history.Message,
                );
                dispatch(prependMainChatItem(item));
              } else if (history.Type === ChatResponseType.RestartWorkflow) {
                // Message は JSON 文字列ではなく dict のまま届く
                const workflowItem = createWorkflowItem(
                  history.MessageID,
                  history.Message,
                );
                const displayType = workflowItem.workflowDefinition.displayType;
                if (displayType === WorkflowDisplayType.Inline) {
                  dispatch(prependMainChatItem(workflowItem));
                  dispatch(setInlineWorkflow(workflowItem));
                } else if (displayType === WorkflowDisplayType.Modal) {
                  dispatch(
                    prependMainChatItem(
                      createRestartWorkflowButtonItem(
                        history.MessageID,
                        workflowItem.workflowDefinition,
                      ),
                    ),
                  );
                } else {
                  console.error(
                    `Unknown workflow displayType for ${history.MessageID}`,
                  );
                }
              } else {
                console.error("Unknown message type.");
              }
              } catch (e) {
                console.error("Failed to process chat history item", history.MessageID, e);
              }
            }
          }

          dispatch(
            setHasMoreHistory({
              positionID: positionID || null,
              hasMoreHistory: res.data?.NoMoreUserMessageLeft === false,
            }),
          );
        })
        .catch((e) => console.error("過去のメッセージ取得に失敗しました", e))
        .finally(() => {
          dispatch(finishHistoryRetrieval(positionID || null));

          if (init) {
            dispatch(updateScrollEventType(ScrollEventType.Connected));
          }
        });
    },
    [dispatch, historyRetrievalStatus, itemsOfCurrentPage, positionID],
  );

  return {
    itemsOfCurrentPage,
    hasMoreHistory,
    historyRetrievalStatus,
    loadPreviousMessages,
  };
};
