"use client";

import "./JobtypeHelpDialog.scss";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";

import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";

type Props = {
  open: boolean;
  target: string;
  description?: string;
  onClose: () => void;
};

export default function JobtypeHelpDialog({
  open,
  target,
  description,
  onClose,
}: Props) {
  const content = (description || "職種の説明は準備中です。").replace(
    /\r?\n/g,
    "  \n",
  );

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>{target}</DialogTitle>
      <DialogContent dividers>
        <div className="jobtype-help-dialog__markdown">
          <Markdown remarkPlugins={[remarkGfm]}>{content}</Markdown>
        </div>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>閉じる</Button>
      </DialogActions>
    </Dialog>
  );
}
