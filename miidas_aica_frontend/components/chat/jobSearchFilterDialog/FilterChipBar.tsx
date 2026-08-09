"use client";

import React from "react";
import TuneIcon from "@mui/icons-material/Tune";

type Props = {
  totalCount: number;
  onOpenFilter: () => void;
};

export default function FilterChipBar({
  totalCount,
  onOpenFilter,
}: Props) {
  return (
    <button
      type="button"
      className="chat-floating-filter"
      aria-label="検索条件を変更"
      onClick={onOpenFilter}
    >
      <span className="chat-floating-filter__icon" aria-hidden="true">
        <TuneIcon fontSize="inherit" />
      </span>
      <span className="chat-floating-filter__label">絞り込み</span>
      <span className="chat-floating-filter__count">{totalCount}</span>
    </button>
  );
}
