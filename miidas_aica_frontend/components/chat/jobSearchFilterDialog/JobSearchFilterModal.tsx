"use client";

import { forwardRef } from "react";
import type { ReactNode } from "react";
import Button from "@mui/material/Button";
import Box from "@mui/material/Box";
import ButtonBase from "@mui/material/ButtonBase";
import Checkbox from "@mui/material/Checkbox";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import Slide from "@mui/material/Slide";
import useMediaQuery from "@mui/material/useMediaQuery";
import AddIcon from "@mui/icons-material/Add";
import RemoveCircleIcon from "@mui/icons-material/RemoveCircle";
import AddCircleIcon from "@mui/icons-material/AddCircle";
import ArrowBackIcon from "@mui/icons-material/ArrowBack";
import ChevronRightIcon from "@mui/icons-material/ChevronRight";
import AddressSelectionModal from "@/components/AddressSelectionModal";
import { TABLET_MEDIA_QUERY } from "@/lib/constants";
import { UseJobSearchFilterDialogState } from "@/components/chat/jobSearchFilterDialog/useJobSearchFilterDialogState";
import type { TransitionProps } from "@mui/material/transitions";

type Props = {
  state: UseJobSearchFilterDialogState;
};

type FooterCancelConfig = {
  cancelLabel: string;
  cancelStartIcon?: ReactNode;
  onCancel: () => void;
};

type FooterCancelButtonProps = Pick<
  FooterCancelConfig,
  "cancelLabel" | "cancelStartIcon"
>;

type FooterConfig =
  | (FooterCancelConfig & {
      showSubmit: false;
    })
  | (FooterCancelConfig & {
      showSubmit: true;
      onSubmit: () => void;
      submitDisabled: boolean;
      submitLabel: string;
    });

const createCancelButtonProps = (
  isSubModal: boolean,
): FooterCancelButtonProps => ({
  cancelLabel: isSubModal ? "戻る" : "キャンセル",
  cancelStartIcon: isSubModal ? <ArrowBackIcon /> : undefined,
});

const tabItems = [
  { key: "jobtype", label: "職種" },
  { key: "salary", label: "年収" },
  { key: "location", label: "勤務地" },
  { key: "detail", label: "その他" },
  { key: "keyword", label: "フリーワード" },
] as const;

const BottomSlideTransition = forwardRef(function BottomSlideTransition(
  props: TransitionProps & {
    children: React.ReactElement<unknown>;
  },
  ref: React.Ref<unknown>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

function BackHeader({
  title,
  counter,
  onBack,
}: {
  title: string;
  counter?: string | null;
  onBack: () => void;
}) {
  return (
    <Box className="chat-bottom-modal__sub-header-wrap">
      <Box className="chat-bottom-modal__sub-header">
        <ButtonBase
          className="chat-bottom-modal__back"
          aria-label="戻る"
          onClick={onBack}
        />
        <span className="chat-bottom-modal__sub-title">{title}</span>
      </Box>
      {counter ? (
        <div className="chat-bottom-modal__counter">{counter}</div>
      ) : null}
    </Box>
  );
}

function OptionRow({
  selected,
  emphasized = false,
  label,
  onClick,
  trailing,
}: {
  selected: boolean;
  emphasized?: boolean;
  label: string;
  onClick: () => void;
  trailing?: React.ReactNode;
}) {
  const showCheckmark = trailing == null && !emphasized;

  return (
    <Box
      role="button"
      tabIndex={0}
      className={`chat-bottom-modal__item${
        selected ? " is-selected" : ""
      }${emphasized ? " is-emphasized" : ""}`}
      onClick={onClick}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onClick();
        }
      }}
    >
      <span className="chat-bottom-modal__label">{label}</span>
      {trailing}
      {showCheckmark ? (
        <span
          className={`chat-bottom-modal__check${selected ? " is-visible" : ""}`}
        >
          ✓
        </span>
      ) : null}
    </Box>
  );
}

export default function JobSearchFilterModal({ state }: Props) {
  const isDesktop = useMediaQuery(TABLET_MEDIA_QUERY, { noSsr: true });
  const {
    filterModalOpen,
    filterModalType,
    subModalType,
    selectedLocationCount,
    selectedDetailCount,
    selectedKeywordCount,
    selectedSalaryCount,
    selectedJobtypeValues,
    jobtypeOptions,
    jobtypeGroups,
    hasMultipleJobtypeGroups,
    showDetailChip,
    primaryLocationTitle,
    primaryLocationOptions,
    detailGroups,
    salaryDraft,
    keywordDraft,
    isSalaryValid,
    canApplyLocation,
    canSearchWithCurrentFilters,
    draftPrimaryLocations,
    draftOtherLocations,
    draftRemoteWorkPossible,
    draftOtherLocationOptions,
    draftDetailGroups,
    remoteWorkPossible,
    addressSelectionModalOpen,
    addressSelectionMode,
    setSubModalType,
    setAddressSelectionModalOpen,
    closeAllModals,
    openFilter,
    openJobtypeHelp,
    selectOtherJobtype,
    selectJobtype,
    setSalaryDraftValue,
    adjustSalaryDraft,
    applyJobtype,
    cancelJobtype,
    cancelJobtypeGroup,
    applySalary,
    cancelSalary,
    applyKeyword,
    cancelKeyword,
    setKeywordDraft,
    confirmGroupSwitch,
    cancelGroupSwitch,
    groupSwitchConfirmPending,
    toggleDraftPrimaryLocation,
    toggleDraftOtherLocation,
    toggleDraftRemoteWorkPossible,
    addOtherLocation,
    openResidenceAddressSelection,
    selectAddress,
    toggleDraftDetail,
    applyLocation,
    cancelLocation,
    cancelPrimaryLocationSubModal,
    cancelOtherLocationSubModal,
    applyDetail,
    cancelDetail,
  } = state;

  const topLevelTabItems = tabItems.filter(
    (item) => item.key !== "detail" || showDetailChip,
  );

  const tabCounts: Record<(typeof tabItems)[number]["key"], number> = {
    jobtype: selectedJobtypeValues.length,
    keyword: selectedKeywordCount,
    salary: selectedSalaryCount,
    location: selectedLocationCount,
    detail: selectedDetailCount,
  };

  const renderLocationContent = () => {
    if (subModalType?.type === "location-primary") {
      return (
        <>
          <div className="chat-bottom-modal__list">
            {primaryLocationOptions.map((option) => (
              <OptionRow
                key={option.value}
                selected={draftPrimaryLocations.includes(option.value)}
                label={option.label}
                onClick={() => toggleDraftPrimaryLocation(option.value)}
              />
            ))}
          </div>
        </>
      );
    }

    if (subModalType?.type === "location-other") {
      return (
        <>
          <ButtonBase
            className="chat-bottom-modal__add-button"
            onClick={addOtherLocation}
          >
            <AddIcon fontSize="small" />
            追加
          </ButtonBase>
          {draftOtherLocationOptions.length > 0 && (
            <div className="chat-bottom-modal__list">
              {draftOtherLocationOptions.map((option) => {
                return (
                  <OptionRow
                    key={option.Value}
                    selected={draftOtherLocations.includes(option.Value)}
                    label={option.Label}
                    onClick={() => toggleDraftOtherLocation(option.Value)}
                  />
                );
              })}
            </div>
          )}
        </>
      );
    }

    return (
      <div className="chat-bottom-modal__list">
        {primaryLocationOptions.length > 0 ? (
          <OptionRow
            selected={draftPrimaryLocations.length > 0}
            label={`${primaryLocationTitle}（${draftPrimaryLocations.length}件選択中）`}
            onClick={() => setSubModalType({ type: "location-primary" })}
            trailing={<ChevronRightIcon fontSize="small" />}
          />
        ) : (
          <ButtonBase
            className="chat-bottom-modal__item"
            onClick={openResidenceAddressSelection}
          >
            <span className="chat-bottom-modal__label">居住地入力</span>
            <ChevronRightIcon fontSize="small" />
          </ButtonBase>
        )}
        <OptionRow
          selected={draftOtherLocations.length > 0}
          label={
            draftOtherLocations.length > 0
              ? `その他勤務地（${draftOtherLocations.length}件選択中）`
              : "その他勤務地"
          }
          onClick={() => setSubModalType({ type: "location-other" })}
          trailing={<ChevronRightIcon fontSize="small" />}
        />
        {typeof remoteWorkPossible === "boolean" && (
          <OptionRow
            selected={Boolean(draftRemoteWorkPossible)}
            label="リモート可能"
            onClick={toggleDraftRemoteWorkPossible}
            trailing={
              <Checkbox
                checked={Boolean(draftRemoteWorkPossible)}
                size="small"
                sx={{ padding: 0 }}
                onClick={(event) => event.stopPropagation()}
                onChange={toggleDraftRemoteWorkPossible}
              />
            }
          />
        )}
      </div>
    );
  };

  const renderDetailContent = () => {
    if (subModalType?.type === "detail-item") {
      const group = detailGroups.find((item) => item.key === subModalType.key);
      if (!group) return null;
      return (
        <>
          <div className="chat-bottom-modal__list">
            {group.options.map((option) => (
              <OptionRow
                key={option.value}
                selected={(draftDetailGroups[group.key] ?? []).includes(
                  option.value,
                )}
                label={option.label}
                onClick={() => toggleDraftDetail(group.key, option.value)}
              />
            ))}
          </div>
        </>
      );
    }

    return (
      <div className="chat-bottom-modal__list">
        {detailGroups.map((group) => {
          const count = (draftDetailGroups[group.key] ?? []).length;
          return (
            <OptionRow
              key={group.key}
              selected={count > 0}
              label={
                count > 0 ? `${group.label}（${count}件選択中）` : group.label
              }
              onClick={() =>
                setSubModalType({ type: "detail-item", key: group.key })
              }
              trailing={<ChevronRightIcon fontSize="small" />}
            />
          );
        })}
      </div>
    );
  };

  const renderJobtypeContent = () => {
    if (filterModalType === "jobtype") {
      if (subModalType?.type === "jobtype-group") {
        const group = jobtypeGroups.find(
          (item) => item.toolName === subModalType.toolName,
        );
        if (!group) return null;

        return (
          <>
            <div className="chat-bottom-modal__list chat-bottom-modal__list--jobtype">
              {group.options.map((option) => (
                <OptionRow
                  key={option.value}
                  selected={selectedJobtypeValues.includes(option.value)}
                  label={option.label}
                  onClick={() => selectJobtype(option.value, group.toolName)}
                  trailing={
                    <Box
                      component="button"
                      type="button"
                      aria-label={`${option.label} の詳細`}
                      onClick={(event) => {
                        event.stopPropagation();
                        openJobtypeHelp(option);
                      }}
                      className="jobtype-choice-card-help"
                    >
                      ?
                    </Box>
                  }
                />
              ))}
            </div>
          </>
        );
      }

      if (hasMultipleJobtypeGroups) {
        return (
          <div className="chat-bottom-modal__list">
            {jobtypeGroups.map((group) => (
              <OptionRow
                key={group.toolName}
                selected={group.selected}
                label={
                  group.selectedCount > 0
                    ? `${group.label}（${group.selectedCount}件選択中）`
                    : group.label
                }
                onClick={() =>
                  setSubModalType({
                    type: "jobtype-group",
                    toolName: group.toolName,
                  })
                }
                trailing={<ChevronRightIcon fontSize="small" />}
              />
            ))}
            <OptionRow
              selected={false}
              emphasized
              label="上記以外の職種を検討したい"
              onClick={selectOtherJobtype}
            />
          </div>
        );
      }

      return (
        <div className="chat-bottom-modal__list chat-bottom-modal__list--jobtype">
          {jobtypeOptions.map((option) => (
            <OptionRow
              key={option.value}
              selected={selectedJobtypeValues.includes(option.value)}
              label={option.label}
              onClick={() => selectJobtype(option.value)}
              trailing={
                <Box
                  component="button"
                  type="button"
                  aria-label={`${option.label} の詳細`}
                  onClick={(event) => {
                    event.stopPropagation();
                    openJobtypeHelp(option);
                  }}
                  className="jobtype-choice-card-help"
                >
                  ?
                </Box>
              }
            />
          ))}
          <OptionRow
            selected={false}
            emphasized
            label="上記以外の職種を検討したい"
            onClick={selectOtherJobtype}
          />
        </div>
      );
    }

    if (filterModalType === "salary") {
      return (
        <div className="chat-bottom-modal__salary">
          <div className="chat-bottom-modal__salary-main">
            <span className="chat-bottom-modal__salary-prefix">おおよそ</span>
            <input
              className={`chat-bottom-modal__salary-input${
                isSalaryValid ? "" : " is-invalid"
              }`}
              inputMode="numeric"
              value={salaryDraft}
              onChange={(event) => setSalaryDraftValue(event.target.value)}
            />
            <span className="chat-bottom-modal__salary-suffix">万円以上</span>
          </div>
          <div className="chat-bottom-modal__salary-stepper-list">
            <div className="chat-bottom-modal__salary-stepper">
              <ButtonBase
                className="chat-bottom-modal__salary-stepper-button"
                onClick={() => adjustSalaryDraft(-10)}
              >
                <RemoveCircleIcon fontSize="small" />
              </ButtonBase>
              <span>10万円</span>
              <ButtonBase
                className="chat-bottom-modal__salary-stepper-button"
                onClick={() => adjustSalaryDraft(10)}
              >
                <AddCircleIcon fontSize="small" />
              </ButtonBase>
            </div>
            <div className="chat-bottom-modal__salary-stepper">
              <ButtonBase
                className="chat-bottom-modal__salary-stepper-button"
                onClick={() => adjustSalaryDraft(-50)}
              >
                <RemoveCircleIcon fontSize="small" />
              </ButtonBase>
              <span>50万円</span>
              <ButtonBase
                className="chat-bottom-modal__salary-stepper-button"
                onClick={() => adjustSalaryDraft(50)}
              >
                <AddCircleIcon fontSize="small" />
              </ButtonBase>
            </div>
          </div>
        </div>
      );
    }

    if (filterModalType === "keyword") {
      return (
        <div className="chat-bottom-modal__keyword">
          <label
            className="chat-bottom-modal__keyword-title"
            htmlFor="chat-bottom-modal-keyword-textarea"
          >
            フリーワード（複数入力可）
          </label>
          <textarea
            id="chat-bottom-modal-keyword-textarea"
            className="chat-bottom-modal__keyword-textarea"
            rows={8}
            placeholder={`例)
リモートワーク
資格取得支援
英語力を活かせる`}
            aria-describedby="chat-bottom-modal-keyword-note"
            value={keywordDraft}
            onChange={(event) => setKeywordDraft(event.target.value)}
          />
          <div
            id="chat-bottom-modal-keyword-note"
            className="chat-bottom-modal__keyword-note"
          >
            ※1行につき1フリーワードを入力してください
          </div>
        </div>
      );
    }

    if (filterModalType === "location") return renderLocationContent();
    if (filterModalType === "detail") return renderDetailContent();
    return null;
  };

  const subModalHeader = (() => {
    if (!subModalType) return null;
    if (subModalType.type === "location-primary") {
      return {
        title: primaryLocationTitle,
        counter: `${draftPrimaryLocations.length}件選択中`,
      };
    }
    if (subModalType.type === "location-other") {
      return {
        title: "その他の希望勤務地",
        counter: `${draftOtherLocations.length}件選択中`,
      };
    }
    if (subModalType.type === "detail-item") {
      const group = detailGroups.find((item) => item.key === subModalType.key);
      return group
        ? {
            title: group.label,
            counter: `${(draftDetailGroups[group.key] ?? []).length}件選択中`,
          }
        : null;
    }
    if (subModalType.type === "jobtype-group") {
      const group = jobtypeGroups.find(
        (item) => item.toolName === subModalType.toolName,
      );
      return group
        ? {
            title: group.label,
            counter:
              group.selectedCount > 0 ? `${group.selectedCount}件選択中` : null,
          }
        : null;
    }
    return null;
  })();

  const footerConfig: FooterConfig | null = (() => {
    if (!filterModalType) return null;
    if (subModalType?.type === "location-primary") {
      return {
        ...createCancelButtonProps(true),
        onCancel: cancelPrimaryLocationSubModal,
        showSubmit: false,
      };
    }
    if (subModalType?.type === "location-other") {
      return {
        ...createCancelButtonProps(true),
        onCancel: cancelOtherLocationSubModal,
        showSubmit: false,
      };
    }
    if (subModalType?.type === "detail-item") {
      return {
        ...createCancelButtonProps(true),
        // ここでは選択内容をドラフトに反映するだけで、確定は親モーダルの「この条件で検索する」ボタンで行う。
        onCancel: () => setSubModalType(null),
        showSubmit: false,
      };
    }
    if (subModalType?.type === "jobtype-group") {
      return {
        ...createCancelButtonProps(true),
        onCancel: cancelJobtypeGroup,
        showSubmit: false,
      };
    }
    switch (filterModalType) {
      case "jobtype":
        return {
          ...createCancelButtonProps(false),
          onCancel: cancelJobtype,
          onSubmit: applyJobtype,
          showSubmit: true,
          submitDisabled: !canSearchWithCurrentFilters,
          submitLabel: "この条件で検索する",
        };
      case "salary":
        return {
          ...createCancelButtonProps(false),
          onCancel: cancelSalary,
          onSubmit: applySalary,
          showSubmit: true,
          submitDisabled: !isSalaryValid || !canSearchWithCurrentFilters,
          submitLabel: "この条件で検索する",
        };
      case "location":
        return {
          ...createCancelButtonProps(false),
          onCancel: cancelLocation,
          onSubmit: applyLocation,
          showSubmit: true,
          submitDisabled: !canApplyLocation || !canSearchWithCurrentFilters,
          submitLabel: "この条件で検索する",
        };
      case "keyword":
        return {
          ...createCancelButtonProps(false),
          onCancel: cancelKeyword,
          onSubmit: applyKeyword,
          showSubmit: true,
          submitDisabled: !canSearchWithCurrentFilters,
          submitLabel: "この条件で検索する",
        };
      case "detail":
        return {
          ...createCancelButtonProps(false),
          onCancel: cancelDetail,
          onSubmit: applyDetail,
          showSubmit: true,
          submitDisabled: !canSearchWithCurrentFilters,
          submitLabel: "この条件で検索する",
        };
      default:
        return {
          ...createCancelButtonProps(false),
          onCancel: closeAllModals,
          onSubmit: closeAllModals,
          showSubmit: true,
          submitDisabled: false,
          submitLabel: "この条件で検索する",
        };
    }
  })();

  const handleDialogClose = () => {
    if (subModalType?.type === "location-primary") {
      cancelPrimaryLocationSubModal();
      return;
    }
    if (subModalType?.type === "location-other") {
      cancelOtherLocationSubModal();
      return;
    }
    if (subModalType?.type === "detail-item") {
      setSubModalType(null);
      return;
    }
    if (subModalType?.type === "jobtype-group") {
      cancelJobtypeGroup();
      return;
    }
    switch (filterModalType) {
      case "jobtype":
        cancelJobtype();
        return;
      case "salary":
        cancelSalary();
        return;
      case "location":
        cancelLocation();
        return;
      case "keyword":
        cancelKeyword();
        return;
      case "detail":
        cancelDetail();
        return;
      default:
        closeAllModals();
    }
  };

  const dialogSlots = isDesktop
    ? undefined
    : { transition: BottomSlideTransition };

  const dialogSlotProps = isDesktop
    ? undefined
    : {
        transition: {
          timeout: { enter: 240, exit: 200 },
        },
      };

  return (
    <>
      <Dialog
        open={filterModalOpen}
        onClose={handleDialogClose}
        className="chat-bottom-modal"
        slots={dialogSlots}
        slotProps={dialogSlotProps}
      >
        {subModalType && subModalHeader ? (
          <DialogTitle className="chat-bottom-modal__header chat-bottom-modal__header--sub">
            <BackHeader
              title={subModalHeader.title}
              counter={subModalHeader.counter}
              onBack={
                subModalType?.type === "location-primary"
                  ? cancelPrimaryLocationSubModal
                  : subModalType?.type === "location-other"
                    ? cancelOtherLocationSubModal
                    : subModalType?.type === "jobtype-group"
                      ? cancelJobtypeGroup
                      : () => setSubModalType(null)
              }
            />
          </DialogTitle>
        ) : !filterModalType ? null : (
          <DialogTitle className="chat-bottom-modal__header chat-bottom-modal__header--tabs">
            <div className="chat-bottom-modal__tabs" role="tablist">
              {topLevelTabItems.map((tab) => (
                <button
                  key={tab.key}
                  type="button"
                  role="tab"
                  aria-selected={filterModalType === tab.key}
                  className={`chat-bottom-modal__tab${
                    filterModalType === tab.key ? " is-active" : ""
                  }`}
                  onClick={() => openFilter(tab.key)}
                >
                  <span className="chat-bottom-modal__tab-label">
                    {tab.label}
                  </span>
                  {tabCounts[tab.key] > 0 && (
                    <span className="chat-bottom-modal__tab-count">
                      {tabCounts[tab.key]}
                    </span>
                  )}
                </button>
              ))}
            </div>
          </DialogTitle>
        )}
        <DialogContent
          className={`chat-bottom-modal__content${
            filterModalType === "keyword"
              ? " chat-bottom-modal__content--keyword"
              : ""
          }`}
        >
          {renderJobtypeContent()}
        </DialogContent>
        {footerConfig && (
          <div className="chat-bottom-modal__footer">
            <Button
              variant="outlined"
              className="chat-bottom-modal__cancel"
              onClick={footerConfig.onCancel}
              startIcon={footerConfig.cancelStartIcon}
            >
              {footerConfig.cancelLabel}
            </Button>
            {footerConfig.showSubmit ? (
              <Button
                variant="contained"
                className="chat-bottom-modal__submit"
                onClick={footerConfig.onSubmit}
                disabled={footerConfig.submitDisabled}
              >
                {footerConfig.submitLabel}
              </Button>
            ) : null}
          </div>
        )}
      </Dialog>
      <AddressSelectionModal
        hint={
          addressSelectionMode === "residence"
            ? "居住地を検索して設定できます"
            : "その他の希望勤務地を検索して追加できます"
        }
        open={addressSelectionModalOpen}
        onClose={() => setAddressSelectionModalOpen(false)}
        onSelect={selectAddress}
      />
      <Dialog open={!!groupSwitchConfirmPending} onClose={cancelGroupSwitch}>
        <DialogTitle>職種グループの切り替え</DialogTitle>
        <DialogContent>
          異なる職種グループを選択すると、現在選択中のグループは解除されます。続けますか？
        </DialogContent>
        <DialogActions>
          <Button onClick={cancelGroupSwitch}>キャンセル</Button>
          <Button variant="contained" onClick={confirmGroupSwitch}>
            続ける
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
}
