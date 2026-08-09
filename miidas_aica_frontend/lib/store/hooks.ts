import { useDispatch, useSelector, useStore } from "react-redux";
import { createSelector } from "@reduxjs/toolkit";
import type { AppDispatch, AppStore, RootState } from ".";
import { ChatHistoryRetrievalStatus } from "@/constants/enum";

// Use throughout your app instead of plain `useDispatch` and `useSelector`
export const useAppDispatch = useDispatch.withTypes<AppDispatch>();
export const useAppSelector = useSelector.withTypes<RootState>();
export const useAppStore = useStore.withTypes<AppStore>();

/**
 * Memoised selectors for position search state.
 * Add new selectors here as components need them rather than pre-emptively.
 */

const selectPositionSearchState = (state: RootState) => state.positionSearch;

export const selectPositionSearchReady = createSelector(
  [selectPositionSearchState],
  (positionSearch) => positionSearch.ready,
);

/**
 * positionID に基づいてチャット履歴がまだあるかを取得するカスタムフック
 * @param positionID - ポジションID（null の場合はメインチャット）
 */
export const useHasMoreHistory = (
  positionID: string | null,
): boolean | undefined => {
  return useAppSelector((state) => {
    if (positionID) {
      return state.websocket.positionHistoryState[positionID];
    }
    return state.websocket.mainChatHasMoreHistory;
  });
};

/**
 * positionID に基づいて履歴取得状態を取得するカスタムフック
 * @param positionID - ポジションID（null の場合はメインチャット）
 */
export const useHistoryRetrievalStatus = (
  positionID: string | null,
): ChatHistoryRetrievalStatus => {
  return useAppSelector((state) => {
    if (positionID) {
      return (
        state.websocket.positionHistoryRetrievalStatus[positionID] ??
        ChatHistoryRetrievalStatus.NotStarted
      );
    }
    return state.websocket.mainHistoryRetrievalStatus;
  });
};
