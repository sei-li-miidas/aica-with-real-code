import { type MFC, type ReactNode, type MouseEventHandler } from "react";
import { type ValuesType } from "@/types/utility-types";
import { MODAL_BTN_VARIANTS } from "@/constants/modal";
import styles from "./ModalLayoutButton.module.scss";

type Props = {
  variant: ValuesType<typeof MODAL_BTN_VARIANTS>;
  onClick: MouseEventHandler<HTMLButtonElement>;
  disabled?: boolean;
  children: ReactNode;
};

const ModalLayoutButton: MFC<Props> = ({
  variant,
  onClick,
  disabled = false,
  children,
}) => {
  const BTN_STYLE_MAP = {
    [MODAL_BTN_VARIANTS.OUTLINED]: styles.outlined,
    [MODAL_BTN_VARIANTS.GRAY_FILL]: styles.grayFill,
    [MODAL_BTN_VARIANTS.BLUE_FILL]: styles.blueFill,
  };

  return (
    <button
      type="button"
      className={`${styles.button} ${BTN_STYLE_MAP[variant]}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
};

export default ModalLayoutButton;
