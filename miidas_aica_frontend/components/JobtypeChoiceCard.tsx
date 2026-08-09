"use client";

import "./JobtypeChoiceCard.scss";
import React, { useCallback, useMemo, useState } from "react";
import { Box, Button, Checkbox } from "@mui/material";
import JobtypeHelpDialog from "@/components/chat/jobSearchFilterDialog/JobtypeHelpDialog";
import type { KeyValue } from "@/types/utility-types";

export type JobtypeChoiceCardProps = {
  /** 検索時のフリーワード。未指定または空文字の場合は汎用文言を表示。 */
  searchKeyword?: string;
  /** 表示する職種一覧（表示ラベルは`ID`、?アイコンのポップアップは`Name`）。 */
  jobtypes: KeyValue[];
  /**
   * 選択値（職種`ID`配列）を親から渡す「制御コンポーネント」用。
   * これを指定した場合、選択状態は親が管理し、このコンポーネント内部では選択値を保持しません。
   */
  value?: string[];
  /** 下部の確定ボタンのラベル。未指定時は`"決定"`。 */
  confirmLabel?: string;
  /**
   * 選択が変わったときに呼ばれます（引数は職種`ID`配列）。
   * 制御/非制御どちらの使い方でも呼ばれます。
   */
  onChange?: (selectedIds: string[]) => void;
  /**
   * 確定ボタン押下時に呼ばれます（引数は職種`ID`配列）。
   * 未選択の場合は呼ばれません。
   */
  onConfirm?: (selectedIds: string[]) => void;
};

type State = {
  internalValue: string[];
  popupOpen: boolean;
  popupJobtype: KeyValue | null;
};

const JobtypeChoiceCard = ({
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  searchKeyword,
  jobtypes,
  value,
  confirmLabel = "職種を決定する",
  onChange,
  onConfirm,
}: JobtypeChoiceCardProps) => {
  const [internalValue, setInternalValue] = useState<State["internalValue"]>(
    [],
  );
  const [popupOpen, setPopupOpen] = useState<State["popupOpen"]>(false);
  const [popupJobtype, setPopupJobtype] = useState<State["popupJobtype"]>(null);

  const isControlled = value !== undefined;
  const selectedIds = useMemo(() => {
    return isControlled ? (value ?? []) : internalValue;
  }, [internalValue, isControlled, value]);

  const handleToggle = useCallback(
    (jobtypeId: string) => {
      const nextSelectedIds = selectedIds.includes(jobtypeId)
        ? selectedIds.filter((id) => id !== jobtypeId)
        : [...selectedIds, jobtypeId];
      onChange?.(nextSelectedIds);
      if (!isControlled) {
        setInternalValue(nextSelectedIds);
      }
    },
    [isControlled, onChange, selectedIds],
  );

  const handleHelpClick = useCallback((jobtype: KeyValue) => {
    setPopupOpen(true);
    setPopupJobtype(jobtype);
  }, []);

  const handlePopupClose = useCallback(() => {
    setPopupOpen(false);
    setPopupJobtype(null);
  }, []);

  const handleConfirm = useCallback(() => {
    if (selectedIds.length === 0) return;
    onConfirm?.(selectedIds);
  }, [onConfirm, selectedIds]);

  return (
    <>
      <Box className="jobtype-choice-card-shell">
        <Box className="jobtype-choice-card-intro chat-message-content agent">
          <Box component="p" className="jobtype-choice-card-intro-text">
            これまでお聞きした希望内容を踏まえて、あなたとマッチ度が高い職種をピックアップしました。
          </Box>
          <Box component="p" className="jobtype-choice-card-intro-text">
            職種の右にある
            <span className="jobtype-choice-card-intro-help">?</span>
            を押すと、その職種の仕事内容を見ることができます。
          </Box>
          <Box component="p" className="jobtype-choice-card-intro-text">
            少しでも興味がありましたら、職種にチェックを入れて「職種を決定する」ボタンを押してください。
          </Box>
        </Box>

        <Box className="jobtype-choice-card">
          <Box className="jobtype-choice-card-list">
            {jobtypes.map((jobtype, index) => {
              const isSelected = selectedIds.includes(jobtype.ID);
              return (
                <Box
                  key={`${jobtype.ID}_${index}`}
                  onClick={() => handleToggle(jobtype.ID)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      handleToggle(jobtype.ID);
                    }
                  }}
                  role="checkbox"
                  aria-checked={isSelected}
                  tabIndex={0}
                  className={`jobtype-choice-card-item${isSelected ? " jobtype-choice-card-item-selected" : ""}`}
                >
                  <Checkbox
                    checked={isSelected}
                    value={jobtype.ID}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleToggle(jobtype.ID);
                    }}
                    className="jobtype-choice-card-checkbox"
                    icon={
                      <span className="jobtype-choice-card-checkbox-icon" />
                    }
                    checkedIcon={
                      <span className="jobtype-choice-card-checkbox-icon jobtype-choice-card-checkbox-icon-checked" />
                    }
                  />
                  <Box component="span" className="jobtype-choice-card-label">
                    {jobtype.ID}
                  </Box>
                  <Box
                    component="button"
                    type="button"
                    aria-label={`${jobtype.ID} の詳細`}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleHelpClick(jobtype);
                    }}
                    className="jobtype-choice-card-help"
                  >
                    ?
                  </Box>
                </Box>
              );
            })}
          </Box>

          <Box className="jobtype-choice-card-actions">
            <Button
              variant="contained"
              disabled={selectedIds.length === 0}
              onClick={handleConfirm}
              className="jobtype-choice-card-confirm"
            >
              {confirmLabel}
            </Button>
          </Box>
        </Box>
      </Box>

      <JobtypeHelpDialog
        open={popupOpen}
        target={popupJobtype?.ID ?? ""}
        description={popupJobtype?.Name}
        onClose={handlePopupClose}
      />
    </>
  );
};

export default React.memo(JobtypeChoiceCard);
