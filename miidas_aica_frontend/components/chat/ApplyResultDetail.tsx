"use client";

import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { IPositionSummary } from "@/lib/common";

type Props = {
  positionsApplySucceeded: Array<IPositionSummary>;
  positionsApplyFailed: Array<IPositionSummary>;
};

export default function ApplyResultDetail({
  positionsApplySucceeded,
  positionsApplyFailed,
}: Props) {
  const renderPositionItem = (
    position: IPositionSummary,
    succeeded: boolean,
  ) => {
    const statusText = succeeded ? "申し込みOK" : "申し込み失敗";

    return (
      <li
        key={`${succeeded ? "success" : "fail"}-${position.ID}`}
        className={`apply-result-detail__item ${succeeded ? "success" : "fail"}`}
      >
        <Typography
          variant="body2"
          component="a"
          href={`/positions/${position.ID}`}
          target="_blank"
          rel="noopener noreferrer"
          className="apply-result-detail__title"
        >
          {position.Title}
        </Typography>
        <Typography
          variant="body2"
          component="p"
          className={`apply-result-detail__status ${succeeded ? "success" : "fail"}`}
        >
          （{statusText}
          <Box
            component="span"
            aria-hidden="true"
            className="apply-result-detail__status-icon"
          >
            {succeeded ? "✅" : "❌"}
          </Box>
          ）
        </Typography>
      </li>
    );
  };

  return (
    <div className="apply-result-detail">
      <Typography
        variant="body2"
        color="text.secondary"
        className="apply-result-detail__message"
      >
        申し訳ありません。ミイダスには登録はできましたが、以下の求人への「話を聞いてみる」へのお申し込みがうまくいきませんでした。
        <br />
        <br />
        「話を聞いてみる」の申し込み状況：
      </Typography>
      <ul className="apply-result-detail__list">
        {positionsApplySucceeded.map((position) =>
          renderPositionItem(position, true),
        )}
        {positionsApplyFailed.map((position) =>
          renderPositionItem(position, false),
        )}
      </ul>
      <Typography
        variant="body2"
        color="text.secondary"
        className="apply-result-detail__message"
      >
        恐れ入りますが、申し込みに失敗した求人を再度開いて、求人画面から申し込みをお願いします。
      </Typography>
    </div>
  );
}
