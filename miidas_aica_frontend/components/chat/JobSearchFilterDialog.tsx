"use client";

import FilterChipBar from "@/components/chat/jobSearchFilterDialog/FilterChipBar";
import JobSearchFilterModal from "@/components/chat/jobSearchFilterDialog/JobSearchFilterModal";
import JobtypeHelpDialog from "@/components/chat/jobSearchFilterDialog/JobtypeHelpDialog";
import { useJobSearchFilterDialogState } from "@/components/chat/jobSearchFilterDialog/useJobSearchFilterDialogState";
import { useAppSelector, selectPositionSearchReady } from "@/lib/store/hooks";

type Props = {
  visible: boolean;
};

export default function JobSearchFilterDialog({ visible }: Props) {
  const state = useJobSearchFilterDialogState();
  const positionSearchReady = useAppSelector(selectPositionSearchReady);

  if (!visible || !positionSearchReady) {
    return null;
  }

  return (
    <>
      <FilterChipBar
        totalCount={state.totalVisibleTabCount}
        onOpenFilter={() => state.openFilter("jobtype")}
      />
      <JobSearchFilterModal state={state} />
      <JobtypeHelpDialog
        open={state.jobtypeHelpOpen}
        target={state.jobtypeHelpTarget}
        description={state.jobtypeHelpDescription}
        onClose={() => state.setJobtypeHelpOpen(false)}
      />
    </>
  );
}
