import React from "react";
import { PageName, SessionStatus } from "@/constants/enum";
import type {
  ApplyResult,
  ApplyValidationError,
} from "@/constants/enum";
import type { IItem, IPositionSummary } from "@/lib/common";
import type { RefObject } from "react";
import AgentTypingIndicator from "@/components/AgentTypingIndicator";
import ChatItemList from "@/components/chat/ChatItemList";
import ApplyOnboardingPanel from "@/components/chat/ApplyOnboardingPanel";
import InlineApplyMessages from "@/components/chat/InlineApplyMessages";
import ApplyResultDetail from "@/components/chat/ApplyResultDetail";

type ChatBodyProps = {
  currentPage: string;
  items: IItem[];
  positionItemKey: string | null;
  lastPositionSearchResultItemRef: RefObject<HTMLDivElement | null>;
  onJobtypeConfirm: (jobtypeNames: string[]) => void;
  showAgentTypingIndicator: boolean;
  isApplying: boolean;
  hasAgreedToTermsOfUse: boolean;
  onAgreeTerms: () => void;
  profileCompleted: boolean;
  profileRef: RefObject<HTMLDivElement | null>;
  applyLoading: boolean;
  applyResult: ApplyResult;
  applyError: ApplyValidationError;
  sessionStatus: SessionStatus;
  positionsApplySucceeded: Array<IPositionSummary>;
  positionsApplyFailed: Array<IPositionSummary>;
  bottomRef: RefObject<HTMLDivElement | null>;
};

export default function ChatBody({
  currentPage,
  items,
  positionItemKey,
  lastPositionSearchResultItemRef,
  onJobtypeConfirm,
  showAgentTypingIndicator,
  isApplying,
  hasAgreedToTermsOfUse,
  onAgreeTerms,
  profileCompleted,
  profileRef,
  applyLoading,
  applyResult,
  applyError,
  sessionStatus,
  positionsApplySucceeded,
  positionsApplyFailed,
  bottomRef,
}: ChatBodyProps) {
  return (
    <>
      <ChatItemList
        currentPage={currentPage}
        items={items}
        positionItemKey={positionItemKey}
        lastPositionSearchResultItemRef={lastPositionSearchResultItemRef}
        onJobtypeConfirm={onJobtypeConfirm}
      />
      {showAgentTypingIndicator && <AgentTypingIndicator />}
      {currentPage === PageName.Chat && isApplying && (
        <ApplyOnboardingPanel
          hasAgreedToTermsOfUse={hasAgreedToTermsOfUse}
          onAgreeTerms={onAgreeTerms}
          profileCompleted={profileCompleted}
          profileRef={profileRef}
        />
      )}
      <InlineApplyMessages
        currentPage={currentPage}
        isApplying={isApplying}
        applyLoading={applyLoading}
        applyResult={applyResult}
        applyError={applyError}
        profileCompleted={profileCompleted}
        sessionStatus={sessionStatus}
        applyResultDetail={
          <ApplyResultDetail
            positionsApplySucceeded={positionsApplySucceeded}
            positionsApplyFailed={positionsApplyFailed}
          />
        }
      />
      <div ref={bottomRef} />
    </>
  );
}
