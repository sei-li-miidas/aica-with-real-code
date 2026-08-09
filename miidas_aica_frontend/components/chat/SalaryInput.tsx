"use client";

import { Button } from "@mui/material";

type SalaryInputProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  autoFocus?: boolean;
};

export default function SalaryInput({
  value,
  onChange,
  onSubmit,
  autoFocus,
}: SalaryInputProps) {
  return (
    <div className="chat-bottom-modal__salary">
      <div className="chat-bottom-modal__salary-field">
        <input
          className="chat-bottom-modal__salary-input"
          placeholder="500"
          inputMode="numeric"
          type="number"
          autoFocus={autoFocus}
          value={value}
          onChange={(event) =>
            onChange(event.target.value.replace(/\D/g, ""))
          }
        />
        <span className="chat-bottom-modal__salary-suffix">万〜</span>
      </div>
      <Button
        variant="contained"
        className="chat-bottom-modal__salary-submit"
        onClick={onSubmit}
      >
        反映する
      </Button>
    </div>
  );
}
