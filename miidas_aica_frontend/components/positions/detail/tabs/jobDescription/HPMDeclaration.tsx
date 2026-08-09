import { nl2br } from "@/utils/jsx";

import styles from "./HPMDeclaration.module.scss";

type Props = {
  text: string;
};

/**
 * 健康経営宣言の定型文表示
 */
export default function HPMDeclaration(props: Props) {
  return (
    <div className={styles.content}>
      <p className={styles.presetTextHeader}>
        ※健康経営宣言企業として、従業員等の健康保持・増進に取り組んでいます。
      </p>
      <p className={styles.presetTextIntroduction}>
        【健康宣言】
        <br />
        下記項目に取り組むことを宣言します。
      </p>
      <p className={styles.declarationText}>{nl2br(props.text)}</p>
    </div>
  );
}
