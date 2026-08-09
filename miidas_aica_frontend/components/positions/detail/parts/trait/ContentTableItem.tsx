import { type MFC, type ReactNode } from "react";

import styles from "./ContentTableItem.module.scss";

type Props = {
  itemKey: string;
  name: ReactNode;
  value?: ReactNode;
};

/**
 * トレイトの値を表形式の行で表示
 */
const ContentTableItem: MFC<Props> = ({ itemKey, name, value = undefined }) => {
  // 表示する内容が無い場合は行そのものを非表示
  if (!value) {
    return null;
  }

  return (
    <tr key={itemKey} className={styles.row}>
      <th className={styles.name}>{name}</th>
      <td className={styles.value}>{value}</td>
    </tr>
  );
};

export default ContentTableItem;
