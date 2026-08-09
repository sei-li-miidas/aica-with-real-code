import Box from "@mui/material/Box";
import React, { useCallback, useMemo, useState } from "react";

import PositionCardList from "@/components/PositionCardList";
import { ChatMessage } from "@/components/ChatMessage";
import RecommendationList from "@/components/positions/recommendations/RecommendationList";
import { ChatMessageRole } from "@/constants/enum";
import {
  IPositionSearchResultItem,
  IPositionRecommendation,
} from "@/lib/common";
import { updateMainChatExistingPositionSearchResultItem } from "@/lib/store/features/websocket/websocketSlice";
import { fetchApiData } from "@/utils/fetch";
import { useAppDispatch } from "@/lib/store/hooks";
import "./PositionSearchResult.scss";

interface IPositionSearchResultProps {
  item: IPositionSearchResultItem;
  loadMoreCallback?: () => void;
}

const PositionSearchResult = ({
  item,
  loadMoreCallback,
}: IPositionSearchResultProps) => {
  const EMPTY_RECS: readonly IPositionRecommendation[] = [] as const;
  const dispatch = useAppDispatch();
  const [loadingMore, setLoadingMore] = useState(false);
  const positions = useMemo(
    () => item.positionSearchResult?.Positions ?? [],
    [item.positionSearchResult],
  );

  const handleLoadMore = useCallback(async () => {
    if (positions.length === 0) {
      return;
    }

    if (loadMoreCallback) {
      loadMoreCallback();
    }

    setLoadingMore(true);
    try {
      const res = await fetchApiData(
        `positions/search/${item.positionSearchResult!.SearchKey}/${positions.length}`,
        "求人検索が失敗しました",
      );
      if (res.data?.Positions) {
        dispatch(
          updateMainChatExistingPositionSearchResultItem({
            itemId: item.itemId,
            newPositions: res.data.Positions,
          }),
        );
      }
    } catch {}
    setLoadingMore(false);
  }, [dispatch, positions, item, loadMoreCallback]);

  const more = item.positionSearchResult!.TotalPositionCount > positions.length;
  const recommendations =
    item.positionSearchResult?.Recommendations || EMPTY_RECS;
  const searchKey = item.positionSearchResult?.SearchKey || "";

  return (
    <div key={item.itemId} className="position-search-result">
      {positions.length > 0 && (
        <Box
          className="chat-message-container"
          key={item.itemId + "_positions"}
        >
          <PositionCardList searchKey={searchKey} positions={positions} />
          {more && (
            <Box className="load-more-container">
              <button
                onClick={handleLoadMore}
                disabled={loadingMore}
                className="load-more-button"
              >
                {loadingMore ? "読み込み中..." : "もっと見る"}
              </button>
            </Box>
          )}
        </Box>
      )}
      {positions.length === 0 && (
        <Box
          className="chat-message-container"
          key={item.itemId + "_no_positions"}
        >
          <ChatMessage
            showIcon={false}
            role={ChatMessageRole.Agent}
            message="申し訳ございません、ご希望の条件にピッタリの求人は見つかりませんでした。ただ、ご希望に近い条件の求人もございますので、それらの求人も含めてご提案させていただきます。"
          />
        </Box>
      )}
      {recommendations.length > 0 && (
        <Box
          className="chat-message-container"
          key={item.itemId + "_recommendations"}
        >
          <RecommendationList
            searchKey={searchKey}
            recommendations={recommendations}
          />
        </Box>
      )}
    </div>
  );
};

export default React.memo(PositionSearchResult);
