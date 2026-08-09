"use client";

import { useEffect, useMemo, useRef } from "react";
import type { AppDispatch } from "@/lib/store";
import { ChatHistoryRetrievalStatus, PageName, PagePath } from "@/constants/enum";
import { fetchApiData } from "@/utils/fetch";
import { setCurrentPage } from "@/lib/store/features/websocket/websocketSlice";

type Params = {
  currentPage: string;
  previousPage: string;
  positionID?: string | null;
  isConnected: boolean;
  historyRetrievalStatus: ChatHistoryRetrievalStatus;
  hasMoreHistory?: boolean;
  itemsLength: number;
  loadPreviousMessages: (force?: boolean) => void;
  dispatch: AppDispatch;
  router: {
    replace: (href: string) => void;
  };
};

export function useChatPageInitialization({
  currentPage,
  previousPage,
  positionID,
  isConnected,
  historyRetrievalStatus,
  hasMoreHistory,
  itemsLength,
  loadPreviousMessages,
  dispatch,
  router,
}: Params) {
  const pageInitializedRef = useRef<string>("");

  const pageKey = useMemo(() => {
    return `${currentPage}_${positionID || "main"}`;
  }, [currentPage, positionID]);

  useEffect(() => {
    if (!isConnected) {
      return;
    }

    console.debug(`init when page ${currentPage} is showing`);
    console.debug("previousPage", previousPage);
    console.debug("currentPage", currentPage);
    console.debug("pageInitializedRef", pageInitializedRef.current);

    if (pageInitializedRef.current === pageKey) {
      console.debug("ページ初期化済みのため、スキップ");
      return;
    }

    console.debug("ページ初期化");

    if (currentPage !== previousPage) {
      if (currentPage === PageName.Chat) {
        if (previousPage === "") {
          if (historyRetrievalStatus === ChatHistoryRetrievalStatus.Start) {
            loadPreviousMessages(true);
          }
        }
      } else if (currentPage === PageName.PositionDetail) {
        if (!positionID) {
          router.replace(PagePath.Chat);
        } else if (hasMoreHistory === undefined) {
          if (itemsLength === 0) {
            fetchApiData(
              `chat/${positionID}/exist`,
              "過去会話履歴存在チェック失敗",
            )
              .then((res) => {
                if (res.httpStatus === 200) {
                  loadPreviousMessages(true);
                }
              })
              .catch((e) => console.error("過去会話履歴存在チェック失敗", e));
          }
        }
      }

      pageInitializedRef.current = pageKey;
      dispatch(setCurrentPage(currentPage));
    }
  }, [
    router,
    pageKey,
    dispatch,
    previousPage,
    currentPage,
    positionID,
    isConnected,
    historyRetrievalStatus,
    loadPreviousMessages,
    hasMoreHistory,
    itemsLength,
  ]);
}
