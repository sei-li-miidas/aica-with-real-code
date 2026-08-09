"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  Box,
  Link,
  Card,
  CardActionArea,
  CardMedia,
  CardContent,
  Collapse,
  Typography,
} from "@mui/material";
import { IPositionRecommendation, IPositionSummary } from "@/lib/common";
import { useAppDispatch } from "@/lib/store/hooks";
import { updatePositions } from "@/lib/store/features/websocket/websocketSlice";
import { useRouter } from "next/navigation";
import getRecommendationPositions from "./getRecommendation";
import { LOCALSTORAGE_SOURCE_COMPONENT_KEY } from "@/constants/localStorage";
import { registerPositionItemKey } from "@/lib/store/features/global_state/globalStateSlice";
import "./RecommendationItem.scss";
import { PagePath, SourceComponentNames } from "@/constants/enum";
import { useDummyImageLoader } from "@/utils/dummyImage";

interface IRecommendationItemProps {
  searchKey: string;
  recommendation: IPositionRecommendation;
}

export default function RecommendationItem({
  searchKey,
  recommendation,
}: IRecommendationItemProps) {
  const router = useRouter();
  const dispatch = useAppDispatch();
  const [loading, setLoading] = useState(true);
  const [positions, setPositions] = useState<IPositionSummary[]>([]);
  const [open, setOpen] = useState(false);
  const dummyImageData = useDummyImageLoader();

  useEffect(() => {
    getRecommendationPositions(searchKey, recommendation.Theme).then(
      (positionResult) => {
        if (positionResult.data?.Positions) {
          const fetchedPositions = positionResult.data.Positions;

          setPositions(fetchedPositions);

          dispatch(updatePositions(fetchedPositions));
        }
        setLoading(false);
      },
    );
  }, [searchKey, recommendation.Theme, dispatch]);

  const label = loading
    ? `${recommendation.Title}（検索中…）`
    : `${recommendation.Title}（${positions.length}件）`;

  const generateRecommendationItemKey = useMemo(() => {
    return searchKey + "-" + recommendation.Theme;
  }, [searchKey, recommendation]);

  const generatePositionItemKey = useCallback(
    (positionId: string) => {
      return generateRecommendationItemKey + "-" + positionId;
    },
    [generateRecommendationItemKey],
  );

  const handleClick = (id: string) => {
    // 分析用の項目を一時的にローカルストレージに保存
    localStorage.setItem(
      LOCALSTORAGE_SOURCE_COMPONENT_KEY,
      `${SourceComponentNames.Recommendation}_${recommendation.Theme}`,
    );
    // 詳細を閲覧するポジションのid
    dispatch(registerPositionItemKey(generatePositionItemKey(id)));
    router.push(`${PagePath.PositionDetail}/?positionId=${id}`);
  };

  return (
    <Box className="recommendation-item" id={generateRecommendationItemKey}>
      {loading || positions.length <= 0 ? (
        <Typography className="recommendation-label">{label}</Typography>
      ) : (
        <Link
          component="button"
          underline="none"
          onClick={() => setOpen(!open)}
          className={`recommendation-toggle${open ? " open" : ""}`}
        >
          {label}
        </Link>
      )}

      <Collapse in={open} unmountOnExit>
        {recommendation.Description && (
          <Typography
            variant="body2"
            color="text.secondary"
            className="recommendation-description"
          >
            {recommendation.Description}
          </Typography>
        )}
        <Box className="recommendation-row">
          {positions.map((position) => (
            <Card
              key={generatePositionItemKey(position.ID)}
              className="recommendation-card"
            >
              <CardActionArea onClick={() => handleClick(position.ID)}>
                {(position.Image || dummyImageData) && (
                  <CardMedia
                    component="img"
                    className="recommendation-card-media"
                    image={position.Image ? position.Image : dummyImageData}
                    onError={(e) => {
                      if (!dummyImageData) return;
                      (e.currentTarget as HTMLImageElement).src =
                        dummyImageData;
                    }}
                    alt={position.Title}
                  />
                )}
                {!position.Image && <Box className="no-image" />}
                <CardContent className="recommendation-card-content">
                  <Typography variant="subtitle2" noWrap>
                    {position.Title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {position.SalaryFrom ? `${position.SalaryFrom}万円～` : ""}
                    {position.SalaryTo}万円
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
}
