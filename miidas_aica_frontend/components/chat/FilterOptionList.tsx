"use client";

import { IconButton } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";

type FilterOptionListProps = {
  options: string[];
  selectedOption: string;
  onSelect: (option: string) => void;
  onOpenHelp?: (option: string) => void;
  getHelpAriaLabel?: (option: string) => string;
};

export default function FilterOptionList({
  options,
  selectedOption,
  onSelect,
  onOpenHelp,
  getHelpAriaLabel,
}: FilterOptionListProps) {
  return (
    <div className="chat-bottom-modal__list">
      {options.map((option) => {
        const isSelected = option === selectedOption;
        return (
          <div
            key={option}
            role="button"
            tabIndex={0}
            className={`chat-bottom-modal__item${
              isSelected ? " is-selected" : ""
            }`}
            onClick={() => onSelect(option)}
            onKeyDown={(event) => {
              if (event.key === "Enter" || event.key === " ") {
                event.preventDefault();
                onSelect(option);
              }
            }}
          >
            <span className="chat-bottom-modal__label">{option}</span>
            <span className="chat-bottom-modal__actions">
              {onOpenHelp && (
                <IconButton
                  size="small"
                  aria-label={
                    getHelpAriaLabel ? getHelpAriaLabel(option) : `${option} の詳細`
                  }
                  onClick={(event) => {
                    event.stopPropagation();
                    onOpenHelp(option);
                  }}
                  className="chat-bottom-modal__item-help"
                >
                  <HelpOutlineIcon fontSize="small" />
                </IconButton>
              )}
              <span
                className={`chat-bottom-modal__check${
                  isSelected ? " is-visible" : ""
                }`}
                aria-hidden="true"
              >
                ✓
              </span>
            </span>
          </div>
        );
      })}
    </div>
  );
}
