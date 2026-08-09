import React, { type ReactNode, type MFC } from "react";
import { useModalScroll } from "@/hooks/useModalScroll";
import { type ValuesType } from "@/types/utility-types";
import { MODAL_SIZE } from "@/constants/modal";
import styles from "./ModalLayout.module.scss";

type Props = {
  header: ReactNode;
  footer?: ReactNode;
  children: ReactNode;
  pcSize?: ValuesType<typeof MODAL_SIZE>;
};

/**
 * モーダルのレイアウト
 */
const ModalLayout: MFC<Props> = ({
  header,
  footer = null,
  children,
  pcSize = MODAL_SIZE.MEDIUM,
}) => {
  const { bodyRef, isScrolling, bodyScrollTop, handleBodyScroll } =
    useModalScroll();

  const MODAL_SIZE_MAP = {
    [MODAL_SIZE.SMALL]: styles.pcSmall,
    [MODAL_SIZE.MEDIUM]: styles.pcMedium,
    [MODAL_SIZE.LARGE]: styles.pcLarge,
  };

  const borderCls = isScrolling && bodyScrollTop ? styles.border : false;

  const footerContent = footer && (
    <div className={`${styles.footerContent} ${borderCls}`}>{footer}</div>
  );

  return (
    <div className={`${styles.wrapper} ${MODAL_SIZE_MAP[pcSize]}`}>
      <div className={`${styles.headerContent} ${borderCls}`}>{header}</div>
      <div className={styles.body} ref={bodyRef} onScroll={handleBodyScroll}>
        {children}
      </div>
      {footerContent}
    </div>
  );
};

export default ModalLayout;
