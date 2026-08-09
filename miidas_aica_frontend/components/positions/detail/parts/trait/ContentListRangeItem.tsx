import { type MFC } from "react";
import type Immutable from "immutable";

import { isKeyOf } from "@/types/utility-types";
import { type RANGE_RADIO } from "@/constants/master";
import { TRAIT_OPTION_HELPS } from "@/constants/business";
import CollapsibleNote from "@/components/positions/detail/parts/CollapsibleNote";
import TraitRangeItem from "./TraitRangeItem";
import styles from "./ContentListRangeItem.module.scss";

type Props =
  | {
      traitId: keyof typeof RANGE_RADIO;
      traitValueImtOrderedMap: Immutable.OrderedMap<string, number | null>;
      traitOptionsHelps?: undefined;
      noteText?: string;
    }
  | {
      traitId: keyof typeof TRAIT_OPTION_HELPS;
      traitValueImtOrderedMap: Immutable.OrderedMap<string, number | null>;
      traitOptionsHelps: typeof TRAIT_OPTION_HELPS;
      noteText?: string;
    };

/**
 * トレイトのレンジ形式表示&補足
 */
const ContentListRangeItem: MFC<Props> = ({
  traitId,
  traitValueImtOrderedMap,
  traitOptionsHelps,
  noteText = undefined,
}) => {
  const traitRangeItem = isKeyOf(traitId, TRAIT_OPTION_HELPS) ? (
    <TraitRangeItem
      traitId={traitId}
      traitValueImtOrderedMap={traitValueImtOrderedMap}
      traitOptionsHelps={traitOptionsHelps}
    />
  ) : (
    <TraitRangeItem
      traitId={traitId}
      traitValueImtOrderedMap={traitValueImtOrderedMap}
    />
  );
  // トレイトのレンジ形式表示
  const range = <li>{traitRangeItem}</li>;

  // 補足
  const note = noteText ? (
    <li>
      <CollapsibleNote contentText={noteText} className={styles.note} />
    </li>
  ) : null;

  return (
    <>
      {range}
      {note}
    </>
  );
};

export default ContentListRangeItem;
