import React from "react";
import { Box, Typography } from "@mui/material";
import RecommendationItem from "./RecommendationItem";
import { IPositionRecommendation } from "@/lib/common";
import "./RecommendationList.scss";

interface IRecommendationListProps {
  searchKey: string;
  recommendations: readonly IPositionRecommendation[];
}

export default function RecommendationList({
  searchKey,
  recommendations,
}: IRecommendationListProps) {
  return (
    <Box className="recommendation-list">
      <Typography
        variant="h6"
        gutterBottom
        align="center"
        className="recommendation-list-title"
      >
        AIが提案するその他の検索条件
      </Typography>

      <Typography gutterBottom className="recommendation-list-subtitle">
        あなたの条件で検索している人は以下の条件でも探してます！
      </Typography>

      {recommendations.map((rec) => (
        <RecommendationItem
          key={rec.Theme}
          searchKey={searchKey}
          recommendation={rec}
        />
      ))}
    </Box>
  );
}
