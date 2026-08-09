import { type MFC, type ReactNode } from "react";

import styles from "./TraitListItem.module.scss";

type Props = {
  itemKey: string;
  itemName: ReactNode;
  content?: ReactNode;
};

/**
 * トレイトのリスト形式表示
 */
const TraitListItem: MFC<Props> = ({
  itemKey,
  itemName,
  content = undefined,
}) => {
  // 表示する内容が無い場合は行そのものを非表示
  if (!content) {
    return null;
  }

  return (
    <div key={itemKey} className={styles.item}>
      <dt className={styles.itemName}>{itemName}</dt>
      <dd className={styles.content}>{content}</dd>
    </div>
  );
};

export default TraitListItem;
