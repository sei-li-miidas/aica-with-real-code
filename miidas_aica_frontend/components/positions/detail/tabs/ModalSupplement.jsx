import React from "react";
import PropTypes from "prop-types";

// 汎用モーダルコンポーネント
import Modal from "@/components/utils/Modal";

import Text2LinkWrapper from "@/components/positions/detail/parts/Text2LinkWrapper";
import styles from "./ModalSupplement.module.scss";

/**
 * ModalSupplement
 * 補足情報モーダルコンポーネント
 */
export default function ModalSupplement(props) {
  if (!props.display) return null;

  return (
    <Modal display>
      <div className={styles.wrapper}>
        <header className={styles.header}>
          <button
            type="button"
            className={styles.headerBtn}
            onClick={props.onCloseBtnClick}
            aria-label="Close"
          />
        </header>
        <Text2LinkWrapper className={styles.content} text={props.text} />
        <footer className={styles.footer}>
          <button
            type="button"
            className={styles.footerBtn}
            onClick={props.onCloseBtnClick}
          >
            閉じる
          </button>
        </footer>
      </div>
    </Modal>
  );
}

ModalSupplement.propTypes = {
  display: PropTypes.bool.isRequired,
  text: PropTypes.string.isRequired,
  onCloseBtnClick: PropTypes.func.isRequired,
};
