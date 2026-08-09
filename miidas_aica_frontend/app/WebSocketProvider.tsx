"use client";

import React, { useCallback, useEffect, useRef, useState } from "react";

import { CareerAgentAPI } from "@/lib/api";
import {
  createJobtypeSearchResultItem,
  createNormalMessageItem,
  createPositionSearchResultItem,
  formatResidenceAddress,
  createWorkflowItem,
  IMessageItem,
} from "@/lib/common";
import {
  ChatMessageRole,
  ChatRequestType,
  ChatResponseType,
  SocketStatus,
  chatResponseTypeToItemType,
  WorkflowDisplayType,
  isMessage,
  isPositionSearchResult,
  isJobtypeSearchResult,
  isWorkflow,
} from "@/constants/enum";
import { SESSION_KEY } from "@/constants/localStorage";
import { setSocket } from "@/lib/socket";
import {
  addMainChatNonMessageItem,
  addMainChatPositionSearchResultItem,
  addOrUpdateMainChatMessageItem,
  addOrUpdatePositionChatMessageItem,
  setModalWorkflow,
  setInlineWorkflow,
  saveSessionID,
  setConnected,
  setDisconnected,
  setSessionStatus,
  setSocketStatus,
  triggerHistoryRetrieval,
  updateMaintenanceMessage,
} from "@/lib/store/features/websocket/websocketSlice";
import {
  setActiveToolName,
  setJobtypes,
  setWorkLocations,
  setReady,
  setSalary,
  setPositionKeyword,
  clearPositionKeyword,
  setResidence,
  setRemoteWorkPossible,
  clearResidence,
  clearWorkLocations,
  clearRemoteWorkPossible,
  setOtherFilters,
  clearOtherFilters,
  clearSelectedFilterOptions,
  setSelectedFilterOptions,
  setSameOtherFilterJobtypes,
  clearSameOtherFilterJobtypes,
} from "@/lib/store/features/position_search/positionSearchSlice";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";

const RECONNECT_DELAY = 10000;

export default function WebSocketProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const wsRef = useRef<CareerAgentAPI | null>(null);

  const dispatch = useAppDispatch();
  const maintenanceMessage = useAppSelector(
    (state) => state.websocket.maintenanceMessage,
  );

  const updatePositionSearchFilters = useCallback(
    (payload: any) => {
      console.debug("filters", payload);
      const filters = payload?.SearchFilters ?? payload;
      const locations = filters?.Locations ?? {};

      if (typeof payload?.ToolName === "string" && payload.ToolName) {
        dispatch(setActiveToolName(payload.ToolName));
      }

      // 職種
      dispatch(setJobtypes(filters?.Jobtypes ?? {}));

      // 希望年収
      dispatch(setSalary(Number(filters?.Salary) || 0));

      if (
        typeof filters?.PositionKeyword === "string" &&
        filters.PositionKeyword.trim()
      ) {
        dispatch(setPositionKeyword(filters.PositionKeyword));
      } else {
        dispatch(clearPositionKeyword());
      }

      // 居住地と通勤可能エリア
      if (locations.Residence) {
        dispatch(
          setResidence({
            residence: formatResidenceAddress(locations.Residence.Address),
            residencePrefectureName:
              locations.Residence.Address?.PrefectureName,
            residenceCityName: locations.Residence.Address?.CityName,
            commutingAreas: locations.Residence.CommutingAreas ?? [],
          }),
        );
      } else {
        dispatch(clearResidence());
      }

      // 希望勤務地
      if (locations.WorkLocations) {
        dispatch(setWorkLocations(locations.WorkLocations));
      } else {
        dispatch(clearWorkLocations());
      }

      const remoteWorkPossible = locations.RemoteWorkPossible;
      if (typeof remoteWorkPossible === "boolean") {
        dispatch(setRemoteWorkPossible(remoteWorkPossible));
      } else {
        dispatch(clearRemoteWorkPossible());
      }

      if (filters?.OtherFilters) {
        dispatch(setOtherFilters(filters.OtherFilters));
      } else {
        dispatch(clearOtherFilters());
      }

      if (filters?.SelectedFilterOptions) {
        dispatch(setSelectedFilterOptions(filters.SelectedFilterOptions));
      } else {
        dispatch(clearSelectedFilterOptions());
      }

      if (
        payload?.JobtypeNamesWithSameSearchFilters &&
        typeof payload.JobtypeNamesWithSameSearchFilters === "object"
      ) {
        dispatch(
          setSameOtherFilterJobtypes(payload.JobtypeNamesWithSameSearchFilters),
        );
      } else {
        dispatch(clearSameOtherFilterJobtypes());
      }

      dispatch(setReady(true));
    },
    [dispatch],
  );

  const addOrUpdateMessageItem = useCallback(
    (item: IMessageItem, positionID: string | null) => {
      if (positionID) {
        dispatch(
          addOrUpdatePositionChatMessageItem({
            newItem: item,
            positionID: positionID,
          }),
        );
      } else {
        dispatch(addOrUpdateMainChatMessageItem(item));
      }
    },
    [dispatch],
  );

  const updateItems = useCallback(
    (e: Record<string, unknown>) => {
      const itemType = chatResponseTypeToItemType(
        e.response_type as ChatResponseType,
      );
      const messageID = e.message_id as string;
      const message = e.message as string;
      const positionID = e.position_id as string | null;

      if (isMessage(itemType)) {
        const newItem = createNormalMessageItem(
          e.role as ChatMessageRole,
          messageID,
          message,
        );
        addOrUpdateMessageItem(newItem, positionID);
      } else if (isPositionSearchResult(itemType)) {
        try {
          const newItem = createPositionSearchResultItem(messageID, message);
          dispatch(addMainChatPositionSearchResultItem(newItem));

          const positionSearchPayload = newItem.positionSearchResult as {
            SearchFilters?: unknown;
          };
          if (positionSearchPayload.SearchFilters) {
            updatePositionSearchFilters(positionSearchPayload);
          }
        } catch (error) {
          console.error(
            `Failed to handle position search result for message ${messageID}`,
            error,
          );
        }
      } else if (isJobtypeSearchResult(itemType)) {
        const newItem = createJobtypeSearchResultItem(messageID, message);
        dispatch(addMainChatNonMessageItem(newItem));
      } else if (isWorkflow(itemType)) {
        try {
          const newItem = createWorkflowItem(messageID, message);
          if (newItem.workflowDefinition.displayType === WorkflowDisplayType.Modal) {
            dispatch(setModalWorkflow(newItem));
          } else if (newItem.workflowDefinition.displayType === WorkflowDisplayType.Inline) {
            dispatch(addMainChatNonMessageItem(newItem));
            dispatch(setInlineWorkflow(newItem));
          }
        } catch (error) {
          console.error(
            `Failed to handle workflow item for message ${messageID}`,
            error,
          );
        }
      } else {
        // 過去履歴取得はRESTful APIを利用するので、ここではPositionSearchLinkのメッセージ来るはずがない
        console.error(
          `Unknown item type '${itemType}' for message ${messageID}`,
          e,
        );
      }
    },
    [addOrUpdateMessageItem, updatePositionSearchFilters, dispatch],
  );

  const onResponseStart = useCallback(
    (e: Record<string, unknown>) => {
      console.debug("onResponseStart", e);

      dispatch(updateMaintenanceMessage(null));

      dispatch(saveSessionID(e.session_id as string));
      dispatch(setSessionStatus(e.session_status as number));
      console.debug(`session status: ${e.session_status}`);
      dispatch(setSocketStatus(SocketStatus.MessageReceiving));
      console.debug(`websocket status: ${SocketStatus.MessageReceiving}`);

      updateItems(e);
    },
    [dispatch, updateItems],
  );

  const onResponseDelta = useCallback(
    (e: Record<string, unknown>) => {
      console.debug("onResponseDelta", e);

      updateItems(e);
    },
    [updateItems],
  );

  const onResponseEnd = useCallback(
    (e: Record<string, unknown>) => {
      console.debug("onResponseEnd", e);

      dispatch(setSessionStatus(e.session_status as number));
      console.debug(`session status: ${e.session_status}`);
      dispatch(setSocketStatus(SocketStatus.MessageReceived));
      console.debug(`websocket status: ${SocketStatus.MessageReceived}`);

      if (e.request_type === ChatRequestType.RestartChat) {
        // 会話再開なので、過去会話履歴取得
        dispatch(triggerHistoryRetrieval(null));
      }
    },
    [dispatch],
  );

  const onResponseError = useCallback(
    (e: Record<string, unknown>) => {
      console.error("onResponseError", e);

      const isMaintenance = e.is_maintenance === true;
      if (isMaintenance) {
        // インフラがmiidas.jpやcorp.miidas.jpなどのドメインアクセスをすべてメンテ用ページに強制移動させます
        // AICAはパスベースになったので、本体と同じ仕組みでメンテモードになります
        const message = e.message as string;
        dispatch(updateMaintenanceMessage(message));
        return;
      }

      if (typeof e.session_status === "number") {
        dispatch(setSessionStatus(e.session_status as number));
      }

      dispatch(setSocketStatus(SocketStatus.ErrorReceived));
      console.debug(`websocket status: ${SocketStatus.ErrorReceived}`);
    },
    [dispatch],
  );

  const [reconnect, setReconnect] = useState(false);
  const sessionStatus = useAppSelector(
    (state) => state.websocket.sessionStatus,
  );

  const sessionStatusRef = useRef(sessionStatus);
  useEffect(() => {
    sessionStatusRef.current = sessionStatus;
  }, [sessionStatus]);

  // 直接にsessionStatusを利用するより、sessionStatusRefを利用するのは、下記の理由です。
  // sessionStatusを直接利用すると、sessionStatusが変わるたびに、onClosedは再作成されます。
  // そのため、ws.on("close", onClosed);に登録されたonClosedと別のメソッドになりますので、
  // websocketが切断したときに、再作成されたonClosedが呼び出されなくなります。
  // そのため、再接続もできなくなります。
  const onClosed = useCallback(() => {
    console.debug(`[onClosed]websocket status: ${SocketStatus.Disconnected}`);
    console.debug(`[onClosed]session status: ${sessionStatusRef.current}`);
    dispatch(setDisconnected());

    console.warn("[WebSocket] closed, reconnecting in 10s");
    if (!maintenanceMessage) {
      setTimeout(() => setReconnect(true), RECONNECT_DELAY);
    }
  }, [dispatch, maintenanceMessage]);

  const onError = useCallback(
    (error: any) => {
      console.error("[onError]Connection error:", error);
      dispatch(setDisconnected());

      console.warn("[WebSocket] error happened, reconnecting in 10s");
      if (!maintenanceMessage) {
        setTimeout(() => setReconnect(true), RECONNECT_DELAY);
      }
    },
    [dispatch, maintenanceMessage],
  );

  const connect = useCallback(async () => {
    if (maintenanceMessage) {
      console.log("メンテモードなので、接続しません。");
      return;
    }

    if (wsRef.current?.isConnected()) {
      console.log("[WebSocket] already connected");
      dispatch(setSocketStatus(SocketStatus.Connected));
      return;
    }

    const ws = new CareerAgentAPI({
      url: process.env.NEXT_PUBLIC_AGENT_ENDPOINT || "",
      debug: process.env.NODE_ENV !== "production",
    });
    wsRef.current = ws;

    ws.on("close", onClosed);
    ws.on("error", onError);
    ws.on("server.response.start", onResponseStart);
    ws.on("server.response.delta", onResponseDelta);
    ws.on("server.response.end", onResponseEnd);
    ws.on("server.response.error", onResponseError);

    const sessionID = localStorage.getItem(SESSION_KEY);
    try {
      await ws.connect(sessionID);
      setSocket(ws);
      dispatch(setConnected(sessionID));
      console.debug(`websocket status: ${SocketStatus.Connected}`);
    } catch (error) {
      dispatch(setDisconnected());

      console.error("[WebSocket] connection failed:", error);
      setTimeout(() => setReconnect(true), RECONNECT_DELAY);
    }
  }, [
    // Lintエラー対応のためだけで、実はどれも変わらないので、re-runは発生しないはず
    dispatch,
    maintenanceMessage,
    onClosed,
    onError,
    onResponseStart,
    onResponseDelta,
    onResponseEnd,
    onResponseError,
  ]);

  const disconnect = useCallback(() => {
    const ws = wsRef.current;
    ws?.disconnect();
    dispatch(setDisconnected());
    console.debug(`websocket status: ${SocketStatus.Disconnected}`);

    ws?.off("close", onClosed);
    ws?.off("error", onError);
    ws?.off("server.response.start", onResponseStart);
    ws?.off("server.response.delta", onResponseDelta);
    ws?.off("server.response.end", onResponseEnd);
    ws?.off("server.response.error", onResponseError);

    wsRef.current = null;
  }, [
    dispatch,
    onClosed,
    onError,
    onResponseStart,
    onResponseDelta,
    onResponseEnd,
    onResponseError,
  ]);

  useEffect(() => {
    connect();

    const handleUnload = () => {
      disconnect();
    };
    window.addEventListener("beforeunload", handleUnload);
    return () => {
      console.debug(`[useEffect]cleanup`);
      disconnect();
      window.removeEventListener("beforeunload", handleUnload);
    };
  }, [connect, disconnect]);

  useEffect(() => {
    if (!reconnect) {
      return;
    }

    setReconnect(false);
    wsRef.current?.off("close", onClosed);
    wsRef.current?.off("error", onError);

    dispatch(setSocketStatus(SocketStatus.Reconnecting));
    console.debug(`websocket status: ${SocketStatus.Reconnecting}`);
    connect();
  }, [dispatch, reconnect, onClosed, onError, connect]);

  return children;
}
