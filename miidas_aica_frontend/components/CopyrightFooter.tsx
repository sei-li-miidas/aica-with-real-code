import React from "react";
import styles from "./CopyrightFooter.module.scss";

/**
 * コピーライトフッターコンポーネント
 */
export default function CopyrightFooter() {
  return (
    <footer className={styles.wrapper}>
      <div className={styles.container}>
        <small className={styles.copyright}>
          Copyright&copy; MIIDAS CO., LTD. All Rights Reserved.
        </small>
      </div>
    </footer>
  );
}
