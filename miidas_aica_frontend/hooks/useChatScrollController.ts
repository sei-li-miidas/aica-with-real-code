"use client";

import { useEffect, RefObject } from "react";
import { ScrollEventType } from "@/constants/enum";

type Params = {
  scrollEventType: ScrollEventType;
  scrollEventId: string | number | null;
  positionItemKey?: string | null;
  topRef: RefObject<HTMLDivElement | null>;
  bottomRef: RefObject<HTMLDivElement | null>;
  scrollContainerRef: RefObject<HTMLDivElement | null>;
  lastPositionSearchResultItemRef: RefObject<HTMLDivElement | null>;
  profileRef: RefObject<HTMLDivElement | null>;
};

export function useChatScrollController({
  scrollEventType,
  scrollEventId,
  positionItemKey,
  topRef,
  bottomRef,
  scrollContainerRef,
  lastPositionSearchResultItemRef,
  profileRef,
}: Params) {
  useEffect(() => {
    if (
      scrollEventType === ScrollEventType.Connected ||
      scrollEventType === ScrollEventType.Disconnected ||
      scrollEventType === ScrollEventType.JobSearchFilterRetrieving ||
      scrollEventType === ScrollEventType.NewUserMessage ||
      scrollEventType === ScrollEventType.NewAgentMessage
    ) {
      requestAnimationFrame(() => {
        const container = scrollContainerRef.current;
        if (container) {
          container.scrollTo({
            top: container.scrollHeight,
            behavior: "smooth",
          });
        } else {
          bottomRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "end",
          });
        }
      });
    } else if (
      scrollEventType === ScrollEventType.PreviousMessagesLoading ||
      scrollEventType === ScrollEventType.PreviousMessagesLoaded
    ) {
      requestAnimationFrame(() => {
        topRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    } else if (scrollEventType === ScrollEventType.NewPositionSearchResult) {
      if (lastPositionSearchResultItemRef.current) {
        requestAnimationFrame(() => {
          lastPositionSearchResultItemRef.current?.scrollIntoView({
            behavior: "smooth",
            block: "start",
            inline: "nearest",
          });
        });
      }
    } else if (scrollEventType === ScrollEventType.BackFromPositionDetail) {
      if (positionItemKey) {
        requestAnimationFrame(() => {
          const positionItemNode = document.getElementById(positionItemKey);
          if (positionItemNode) {
            positionItemNode.scrollIntoView({
              behavior: "smooth",
              block: "start",
              inline: "nearest",
            });
          }
        });
      }
    } else if (scrollEventType === ScrollEventType.ProfileSaved) {
      requestAnimationFrame(() => {
        profileRef.current?.scrollIntoView({
          behavior: "smooth",
          block: "start",
          inline: "nearest",
        });
      });
    }
  }, [
    scrollEventType,
    scrollEventId,
    positionItemKey,
    topRef,
    bottomRef,
    scrollContainerRef,
    lastPositionSearchResultItemRef,
    profileRef,
  ]);
}
