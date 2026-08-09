import { type MFC, type ReactNode, type MouseEventHandler } from "react";
import { ICONS } from "@/constants/icon";
import SvgIcon from "@/components/utils/SvgIcon";
import { nl2br } from "@/utils/jsx";
import styles from "./ModalLayoutHeader.module.scss";

type Props = {
  title: ReactNode;
  subTitle?: ReactNode;
  onBack?: MouseEventHandler<HTMLButtonElement>;
  onClose?: MouseEventHandler<HTMLButtonElement>;
};

const ModalLayoutHeader: MFC<Props> = ({
  title,
  subTitle = null,
  onClose,
  onBack,
}) => {
  const titleContent = typeof title === "string" ? nl2br(title) : title;

  const backBtn = onBack && (
    <button
      className={styles.backBtn}
      type="button"
      aria-label="戻る"
      onClick={onBack}
    >
      <SvgIcon icon={ICONS.ARROW_LEFT} />
    </button>
  );

  const closeBtn = onClose && (
    <button
      className={styles.closeBtn}
      type="button"
      aria-label="閉じる"
      onClick={onClose}
    >
      <SvgIcon icon={ICONS.CROSS} />
    </button>
  );

  return (
    <header className={styles.header}>
      <h1 className={styles.title}>{titleContent}</h1>
      {subTitle}
      {backBtn}
      {closeBtn}
    </header>
  );
};

export default ModalLayoutHeader;
