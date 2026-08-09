import { type MFC } from "react";

import { clsx } from "@/utils/className";
import { nl2br } from "@/utils/jsx";
import HelpTooltip from "@/components/utils/HelpTooltip";
import styles from "./TraitRangeBar.module.scss";

export type HelpLabel = {
  title?: string;
  text: string;
};

type Props = {
  value: number;
  leftLabel: string;
  rightLabel: string;
  leftLabelHelp?: HelpLabel;
  rightLabelHelp?: HelpLabel;
};

/**
 * トレイトのレンジ形式表示のバー
 */
const TraitRangeBar: MFC<Props> = ({
  value,
  leftLabel,
  rightLabel,
  leftLabelHelp = undefined,
  rightLabelHelp = undefined,
}) => {
  const rangeBar = renderRangeBar(value);

  const leftLabelHelpToolTip = leftLabelHelp ? (
    <HelpTooltip help={leftLabelHelp} />
  ) : null;

  const rightLabelHelpToolTip = rightLabelHelp ? (
    <HelpTooltip help={rightLabelHelp} />
  ) : null;

  return (
    <ul className={styles.itemWrapList}>
      <li className={styles.labelWrap}>
        <span className={styles.label}>
          {nl2br(leftLabel)}
          {leftLabelHelpToolTip}
        </span>
        <span className={`${styles.label} ${styles.right}`}>
          {nl2br(rightLabel)}
          {rightLabelHelpToolTip}
        </span>
      </li>
      <li>{rangeBar}</li>
    </ul>
  );
};

export default TraitRangeBar;

/**
 * レンジバー
 */
function renderRangeBar(value: number) {
  const units = Array.from({ length: 5 }).map((_, idx) => {
    const unitValue = idx + 1;

    const cls = clsx(styles.unit, unitValue === value && styles.active);

    return <li key={`${value}_${unitValue}`} className={cls} />;
  });

  return <ul className={styles.bar}>{units}</ul>;
}
