"use client";

import "./Chat.scss";
import React, { useCallback, useEffect, useMemo, useRef } from "react";
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks";
import Box from "@mui/material/Box";
import { useRouter } from "next/navigation";
import { createNormalMessageItem } from "@/lib/common";
import {
  ChatHistoryRetrievalStatus,
  ChatMessageRole,
  ChatRequestType,
  PageName,
  PagePath,
  ScrollEventType,
  SessionStatus,
  SocketStatus,
} from "@/constants/enum";
import { sendWebSocketMessage } from "@/lib/socket";
import {
  addOrUpdateMainChatMessageItem,
  addOrUpdatePositionChatMessageItem,
  updateScrollEventType,
  setModalWorkflow,
  setInlineWorkflow,
} from "@/lib/store/features/websocket/websocketSlice";
import { saveTermsOfUseAgreement } from "@/lib/store/features/global_state/globalStateSlice";
import {
  addAppliedPosition,
  markSavedProfileRetrieved,
} from "@/lib/store/features/profile/profileSlice";
import PullToRefresh from "@/components/utils/PullToRefresh";
import {
  basicInfoCompleted,
  careerCompleted,
  educationCompleted,
  willCompleted,
} from "@/utils/profileUtils";
import { useVirtualKeyboardHeightCssVar } from "@/hooks/useVirtualKeyboardHeightCssVar";
import { useChatHistory } from "@/hooks/useChatHistory";
import { useChatScrollController } from "@/hooks/useChatScrollController";
import { useChatPageInitialization } from "@/hooks/useChatPageInitialization";
import { useApplyFinish } from "@/hooks/useApplyFinish";
import ChatFooter from "@/components/chat/ChatFooter";
import ChatBody from "@/components/chat/ChatBody";
import JobSearchFilterDialog from "@/components/chat/JobSearchFilterDialog";
import WorkflowModal from "@/components/workflow/WorkflowModal";
import { usePositionSearchFilterInitialization } from "@/hooks/usePositionSearchFilterInitialization";
import {
  getFooterMode,
  getHideFooterReason,
  isApplyingSession,
  isJobSearchFilterVisible,
  shouldShowAgentTypingIndicator,
} from "@/components/chat/chatViewModel";
import { WORKFLOW_IDS } from "@/constants/workflow";

export interface IChatProps {
  currentPage: string;
  positionID?: string | null;
}

export default function Chat({ currentPage, positionID }: IChatProps) {
  const router = useRouter();
  const dispatch = useAppDispatch();

  // 画面トップのRef
  const topRef = useRef<HTMLDivElement>(null);
  // 画面ボトムのRef
  const bottomRef = useRef<HTMLDivElement>(null);
  // チャットエリアのスクロールコンテナRef
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  // 一番最後の検索結果表示エリアのRef
  const lastPositionSearchResultItemRef = useRef<HTMLDivElement>(null);
  // プロフィール
  const profileRef = useRef<HTMLDivElement>(null);

  const globalState = useAppSelector((state) => state.globalState);
  const {
    // ユーザーが閲覧したポジション詳細カードのid
    positionItemKey,
    // ユーザーが利用規約に同意したかどうか
    hasAgreedToTermsOfUse,
  } = globalState;

  const websocketState = useAppSelector((state) => state.websocket);
  const { sessionStatus, socketStatus, scrollEventType, scrollEventId, modalWorkflow, inlineWorkflow } =
    websocketState;
  const previousPage = useAppSelector((state) => state.websocket.currentPage);

  const {
    itemsOfCurrentPage,
    hasMoreHistory,
    historyRetrievalStatus,
    loadPreviousMessages,
  } = useChatHistory({
    currentPage,
    positionID: positionID ?? null,
  });

  const isConnected = useMemo(
    () => socketStatus >= SocketStatus.Connected,
    [socketStatus],
  );

  // セッションステータス変更検知
  const oldSessionStatusRef = useRef<SessionStatus>(sessionStatus);

  const isApplying = useMemo(
    () => isApplyingSession(sessionStatus),
    [sessionStatus],
  );

  useEffect(() => {
    if (
      currentPage === PageName.PositionDetail &&
      isApplying &&
      oldSessionStatusRef.current === SessionStatus.Chatting
    ) {
      if (sessionStatus === SessionStatus.Applying) {
        // 応募ポジション追加
        dispatch(addAppliedPosition(positionID!));
      }

      // いま保存されたプロフィールがないはずので、サーバーから取得する必要がない
      dispatch(markSavedProfileRetrieved());
      // ポジションチャットサマリ作成リクエスト
      // TODO: チャットした場合のみ実施すべき
      sendWebSocketMessage(
        dispatch,
        ChatRequestType.SummarizePosition,
        PageName.PositionDetail,
        PageName.Chat,
        null,
        positionID,
      );

      // メインチャットへ戻る
      router.push(PagePath.Chat);

      // このときに、メインチャット画面の底部にスクロールすべき
      dispatch(
        updateScrollEventType(ScrollEventType.JobSearchFilterRetrieving),
      );
    }
  }, [dispatch, router, isApplying, sessionStatus, currentPage, positionID]);

  const profileState = useAppSelector((state) => state.profile);
  const { basicInfo, education, career, will } = profileState;

  const profileCompletionStatus = useMemo(() => {
    const profileCompleted = () => {
      if (!isApplying) {
        return false;
      }

      return (
        basicInfoCompleted(basicInfo) &&
        educationCompleted(education) &&
        careerCompleted(career) &&
        willCompleted(will)
      );
    };

    return {
      profileCompleted: profileCompleted(),
    };
  }, [basicInfo, education, career, will, isApplying]);

  const {
    apply,
    applyLoading,
    applyResult,
    applyError,
    positionsApplySucceeded,
    positionsApplyFailed,
  } = useApplyFinish(dispatch, sessionStatus);

  useChatPageInitialization({
    currentPage,
    previousPage,
    positionID,
    isConnected,
    historyRetrievalStatus,
    hasMoreHistory,
    itemsLength: itemsOfCurrentPage.length,
    loadPreviousMessages,
    dispatch,
    router,
  });

  useChatScrollController({
    scrollEventType,
    scrollEventId,
    positionItemKey,
    topRef,
    bottomRef,
    scrollContainerRef,
    lastPositionSearchResultItemRef,
    profileRef,
  });

  const sendUserInput = useCallback(
    (newValue: string, isVoice: boolean) => {
      console.debug("sendUserInput newValue =", newValue);

      const messageID = `input_${crypto.randomUUID()}`;
      const messageItem = createNormalMessageItem(
        ChatMessageRole.User,
        messageID,
        newValue,
      );
      if (positionID) {
        dispatch(
          addOrUpdatePositionChatMessageItem({
            newItem: messageItem,
            positionID: positionID,
          }),
        );
      } else {
        dispatch(addOrUpdateMainChatMessageItem(messageItem));
      }

      sendWebSocketMessage(
        dispatch,
        ChatRequestType.Chat,
        previousPage,
        currentPage,
        newValue,
        positionID,
        messageID,
        isVoice,
      );

      dispatch(updateScrollEventType(ScrollEventType.NewUserMessage));
    },
    [dispatch, previousPage, currentPage, positionID],
  );

  const sendJobtypeChoice = useCallback(
    (jobtypeNames: string[]) => {
      if (jobtypeNames.length === 0) return;
      const messageID = `input_${crypto.randomUUID()}`;
      sendWebSocketMessage(
        dispatch,
        ChatRequestType.JobTypesSelected,
        previousPage,
        currentPage,
        JSON.stringify(jobtypeNames),
        positionID,
        messageID,
        false,
      );
    },
    [currentPage, dispatch, positionID, previousPage],
  );

  const cancelWorkflow = useCallback(() => {
    if (!inlineWorkflow) return;

    const payload = JSON.stringify({
      workflow_id: inlineWorkflow.workflowDefinition.id,
    });
    const messageID = `developer_${crypto.randomUUID()}`;
    sendWebSocketMessage(
      dispatch,
      ChatRequestType.WorkflowCancelled,
      previousPage,
      currentPage,
      payload,
      null,
      messageID,
      false
    );

    dispatch(setInlineWorkflow(null));
  }, [inlineWorkflow, dispatch, previousPage, currentPage]);

  useVirtualKeyboardHeightCssVar();

  const viewStateInput = useMemo(
    () => ({
      currentPage,
      sessionStatus,
      socketStatus,
      applyLoading,
      profileCompleted: profileCompletionStatus.profileCompleted,
      isModalWorkflowActive: !!modalWorkflow,
      isInlineWorkflowActive: !!inlineWorkflow,
      isInitialMenuWorkflow: inlineWorkflow?.workflowDefinition?.id === WORKFLOW_IDS.INITIAL_MENU,
    }),
    [
      currentPage,
      sessionStatus,
      socketStatus,
      applyLoading,
      profileCompletionStatus.profileCompleted,
      modalWorkflow,
      inlineWorkflow,
    ],
  );

  const footerMode = useMemo(
    () => getFooterMode(viewStateInput),
    [viewStateInput],
  );
  const hideFooterReason = useMemo(
    () => getHideFooterReason(viewStateInput),
    [viewStateInput],
  );
  const showJobSearchFilter = useMemo(
    () => isJobSearchFilterVisible(viewStateInput),
    [viewStateInput],
  );
  const showAgentTypingIndicator = useMemo(
    () => shouldShowAgentTypingIndicator(socketStatus),
    [socketStatus],
  );
  usePositionSearchFilterInitialization({ currentPage, isConnected });

  return (
    <div className="chat-root">
      <div ref={topRef} />
      <PullToRefresh
        onRefresh={loadPreviousMessages}
        isLoading={
          historyRetrievalStatus === ChatHistoryRetrievalStatus.Loading
        }
        disabled={!isConnected || !hasMoreHistory}
        contentClassName={"chat-messages-list"}
        containerRef={scrollContainerRef}
        style={{ flex: 1 }}
        refreshText="引っ張って過去のメッセージを読み込み"
        releaseText="離して過去のメッセージを読み込み"
        loadingText="過去のメッセージを読み込み中..."
      >
        <ChatBody
          currentPage={currentPage}
          items={itemsOfCurrentPage}
          positionItemKey={positionItemKey}
          lastPositionSearchResultItemRef={lastPositionSearchResultItemRef}
          onJobtypeConfirm={sendJobtypeChoice}
          isApplying={isApplying}
          hasAgreedToTermsOfUse={hasAgreedToTermsOfUse}
          onAgreeTerms={() => dispatch(saveTermsOfUseAgreement())}
          profileCompleted={profileCompletionStatus.profileCompleted}
          profileRef={profileRef}
          showAgentTypingIndicator={showAgentTypingIndicator}
          applyLoading={applyLoading}
          applyResult={applyResult}
          applyError={applyError}
          sessionStatus={sessionStatus}
          positionsApplySucceeded={positionsApplySucceeded}
          positionsApplyFailed={positionsApplyFailed}
          bottomRef={bottomRef}
        />
      </PullToRefresh>
      <JobSearchFilterDialog visible={showJobSearchFilter} />
      {hideFooterReason === "visible" && (
        <Box
          className={`chat-footer ${
            currentPage === PageName.Chat ? "full-width" : ""
          }`}
        >
          <ChatFooter
            footerMode={footerMode}
            sessionStatus={sessionStatus}
            onApply={apply}
            onSendUserInput={sendUserInput}
            onCancelWorkflow={cancelWorkflow}
          />
        </Box>
      )}
      {modalWorkflow && (
        <WorkflowModal
          workflow={modalWorkflow}
          open={!!modalWorkflow}
          onClose={() => dispatch(setModalWorkflow(null))}
        />
      )}
    </div>
  );
}
