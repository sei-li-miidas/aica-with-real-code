import React from "react";
import JobMatchDiagnosisWorkflow from "./JobMatchDiagnosisWorkflow";
import PositionChangeAnalyzeWorkflow from "./PositionChangeAnalyzeWorkflow";
import { IWorkflowItem } from "@/lib/common";
import { WORKFLOW_IDS } from "@/constants/workflow";

export interface WorkflowComponentProps {
  workflow: IWorkflowItem;
  onClose: () => void;
}

export const WORKFLOW_REGISTRY: Record<string, React.ComponentType<WorkflowComponentProps>> = {
  [WORKFLOW_IDS.JOB_MATCH_DIAGNOSIS]: JobMatchDiagnosisWorkflow,
  [WORKFLOW_IDS.POSITION_CHANGE_ANALYZE]: PositionChangeAnalyzeWorkflow,
};
