"use client";

import { useCallback, useMemo } from "react";
import Box from "@mui/material/Box";
import { ChatMessage } from "@/components/ChatMessage";
import Miibo from "@/components/icons/Miibo";
import PositionSearchResult from "@/components/PositionSearchResult";
import PositionSearchLinkCard from "@/components/PositionSearchLinkCard";
import JobtypeChoiceCard from "@/components/JobtypeChoiceCard";
import WorkflowInlineItem from "@/components/workflow/WorkflowInlineItem";
import RestartWorkflowButton from "@/components/workflow/RestartWorkflowButton";
import {
  IItem,
  IMessageItem,
  IJobtypeSearchResultItem,
  IPositionSearchLinkItem,
  IPositionSearchResultItem,
  IRestartWorkflowButtonItem,
  IWorkflowItem,
} from "@/lib/common";
import {
  ChatMessageRole,
  PageName,
  isPositionSearchResult,
  isPositionSearchLink,
  isJobtypeSearchResult,
  isWorkflow,
  isRestartWorkflowButton,
} from "@/constants/enum";
import type { RefObject } from "react";

type Props = {
  currentPage: string;
  items: IItem[];
  positionItemKey?: string | null;
  lastPositionSearchResultItemRef: RefObject<HTMLDivElement | null>;
  onJobtypeConfirm: (jobtypeNames: string[]) => void;
};

export default function ChatItemList({
  currentPage,
  items,
  positionItemKey,
  lastPositionSearchResultItemRef,
  onJobtypeConfirm,
}: Props) {
  const displayItem = useCallback(
    (previousRole: string | null, item: IItem, isLast: boolean) => {
      if (isPositionSearchResult(item.itemType)) {
        const positionSearchResultItem = item as IPositionSearchResultItem;
        return (
          <div
            ref={
              !positionItemKey && isLast
                ? lastPositionSearchResultItemRef
                : null
            }
            key={positionSearchResultItem.itemId}
            className="position-search-container"
          >
            <Box className="role agent">
              <Miibo />
            </Box>
            <PositionSearchResult item={positionSearchResultItem} />
          </div>
        );
      } else if (isPositionSearchLink(item.itemType)) {
        const positionSearchLinkItem = item as IPositionSearchLinkItem;

        return (
          <Box className="chat-message-container message" key={item.itemId}>
            <Box className="role agent">
              <Miibo />
            </Box>
            <PositionSearchLinkCard item={positionSearchLinkItem} />
          </Box>
        );
      } else if (isJobtypeSearchResult(item.itemType)) {
        const jobtypeSearchResultItem = item as IJobtypeSearchResultItem;
        return (
          <Box className="chat-message-container message" key={item.itemId}>
            <Box className="role agent">
              <Miibo />
            </Box>
            <Box className="chat-message-jobtype-card">
              <JobtypeChoiceCard
                searchKeyword={jobtypeSearchResultItem.jobtypeSearchResult.Keyword}
                jobtypes={jobtypeSearchResultItem.jobtypeSearchResult.Jobtypes}
                onConfirm={onJobtypeConfirm}
              />
            </Box>
          </Box>
        );
      } else if (isWorkflow(item.itemType)) {
        const workflowItem = item as IWorkflowItem;
        return (
          <Box className="chat-message-container message" key={item.itemId}>
              <WorkflowInlineItem item={workflowItem} />
          </Box>
        );
      } else if (isRestartWorkflowButton(item.itemType)) {
        const restartItem = item as IRestartWorkflowButtonItem;
        return (
          <Box className="chat-message-container message" key={item.itemId}>
            <RestartWorkflowButton item={restartItem} />
          </Box>
        );
      } else {
        const messageItem = item as IMessageItem;
        return (
          <Box
            className="chat-message-container message"
            key={messageItem.itemId}
          >
            <ChatMessage
              showIcon={messageItem.role !== previousRole}
              role={messageItem.role as ChatMessageRole}
              message={messageItem.message}
            />
          </Box>
        );
      }
    },
    [lastPositionSearchResultItemRef, onJobtypeConfirm, positionItemKey],
  );

  const renderedItems = useMemo(() => {
    const result = items.map((chatMessage, i) => {
      const previousRole = i > 0 ? items[i - 1].role : null;
      return displayItem(previousRole, chatMessage, i === items.length - 1);
    });

    if (currentPage === PageName.PositionDetail) {
      result.unshift(
        <Box className="chat-message-container message" key="header-intro">
          <ChatMessage
            showIcon={true}
            role={ChatMessageRole.Agent}
            message="求人情報に関して、気になる点がございましたらご連絡ください。"
          />
        </Box>,
      );
    }

    return result;
  }, [currentPage, displayItem, items]);

  return <>{renderedItems}</>;
}
