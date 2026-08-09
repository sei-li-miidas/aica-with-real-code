"use client";

import { useEffect } from "react";
import { IWorkflowItem } from "@/lib/common";
import Dialog from "@mui/material/Dialog";
import DialogContent from "@mui/material/DialogContent";
import { WORKFLOW_REGISTRY } from "./registry";

interface Props {
  workflow: IWorkflowItem;
  open: boolean;
  onClose: () => void;
}

export default function WorkflowModal({
  workflow,
  open,
  onClose,
}: Props) {
  const WorkflowImplementation = WORKFLOW_REGISTRY[workflow.workflowDefinition.id];

  useEffect(() => {
    if (!WorkflowImplementation) {
      console.error(
        `Workflow component not found for workflow ID: ${workflow.workflowDefinition.id}`,
      );
      onClose();
    }
  }, [WorkflowImplementation, workflow.workflowDefinition.id, onClose]);

  if (!WorkflowImplementation) {
    return null;
  }

  return (
    <Dialog
      fullScreen
      open={open}
      onClose={() => {}}
      disableEscapeKeyDown
    >
      <DialogContent sx={{ p: 0 }}>
        <WorkflowImplementation
          workflow={workflow}
          onClose={onClose}
        />
      </DialogContent>
    </Dialog>
  );
}
