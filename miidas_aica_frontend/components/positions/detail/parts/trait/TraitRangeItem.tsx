import { type MFC } from "react";

import { isKeyOf } from "@/types/utility-types";
import { TRAIT_OPTION_HELPS } from "@/constants/business";
import { RANGE_RADIO } from "@/constants/master";
import TraitRangeBar, { type HelpLabel } from "./TraitRangeBar";
import styles from "./TraitRangeItem.module.scss";

type Label = {
  left: string;
  right: string;
};

type TraitRangeInfo = {
  [key: number]: {
    groupKey: string;
    labels: Label;
  };
};

type HelpInfo = {
  left?: HelpLabel;
  right?: HelpLabel;
};

type Props =
  | {
      traitId: keyof typeof RANGE_RADIO;
      traitValueImtOrderedMap: Immutable.OrderedMap<string, number | null>;
      traitOptionsHelps?: undefined;
    }
  | {
      traitId: keyof typeof TRAIT_OPTION_HELPS;
      traitValueImtOrderedMap: Immutable.OrderedMap<string, number | null>;
      traitOptionsHelps: typeof TRAIT_OPTION_HELPS;
    };

/**
 * トレイトのレンジ形式表示
 */
const TraitRangeItem: MFC<Props> = ({
  traitId,
  traitValueImtOrderedMap,
  traitOptionsHelps,
}) => {
  // トレイトごとのレンジ情報
  const traitRangeInfo: TraitRangeInfo = RANGE_RADIO[traitId];
  // トレイトごとのレンジ表示用情報
  const rangeInfo = Object.values(traitRangeInfo);

  const items = traitValueImtOrderedMap.entrySeq().map(([key, value]) => {
    if (value === null) {
      return null;
    }
    // トレイト内の各項目のラベル情報
    const labelInfo = rangeInfo.find((item) => item.groupKey === key)?.labels;

    if (!labelInfo) {
      return null;
    }

    // 各項目のヘルプバルーン情報
    const helpInfo = isKeyOf(traitId, TRAIT_OPTION_HELPS)
      ? getHelpInfo(traitOptionsHelps, traitId, key)
      : undefined;

    return (
      <li key={`${traitId}_${key}`}>
        <TraitRangeBar
          value={value}
          leftLabel={labelInfo.left}
          rightLabel={labelInfo.right}
          leftLabelHelp={helpInfo?.left}
          rightLabelHelp={helpInfo?.right}
        />
      </li>
    );
  });

  return <ul className={styles.barList}>{items}</ul>;
};

export default TraitRangeItem;

/**
 * ヘルプバルーンの情報を取得
 */
function getHelpInfo(
  traitOptionsHelps: typeof TRAIT_OPTION_HELPS | undefined,
  traitId: keyof typeof TRAIT_OPTION_HELPS,
  key: string,
): HelpInfo | undefined {
  // ヘルプ情報用に、key: "(1)" や "Type1" から 1 のような数字だけを取り出す
  const helpIdx = parseInt(key.replace(/[^0-9]/g, ""), 10);

  const traitHelp = traitOptionsHelps?.[traitId];
  if (traitHelp && isKeyOf(helpIdx, traitHelp)) {
    return traitHelp[helpIdx];
  }
  return undefined;
}
