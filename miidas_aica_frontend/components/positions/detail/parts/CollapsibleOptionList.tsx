import { type MFC, type ReactNode } from "react";

// 折りたたみ表示
import Collapse from "@/components/utils/Collapse";

import styles from "./CollapsibleOptionList.module.scss";

type Props = {
  content?: ReactNode;
};

/**
 * 折り畳み表示のオプション一覧
 */
const CollapsibleOptionList: MFC<Props> = ({ content = undefined }) => {
  return content ? (
    <Collapse
      className={styles.collapse}
      showBtnLabel="その他選択肢を見る"
      hideBtnLabel="その他選択肢を閉じる"
    >
      {content}
    </Collapse>
  ) : null;
};

export default CollapsibleOptionList;
