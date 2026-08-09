import { type MFC } from "react";

import {
  type default as HrEvaluationCompetencyAxisRecord,
  type CompetencyFeature,
} from "@/models/position/records/traitValue/HrEvaluationCompetencyAxisTraitValue";
import HelpTooltip from "@/components/utils/HelpTooltip";

import styles from "./ContentListItemHrEvaluationCompetency.module.scss";

type Props = {
  traitValueImtRecord: HrEvaluationCompetencyAxisRecord;
};

/**
 * 「特に評価されるコンピテンシー」の項目（ラベルと補足）
 */
const ContentListItemHrEvaluationCompetency: MFC<Props> = ({
  traitValueImtRecord,
}) => {
  // TODO: ts src/models/position/records/traitValue/HrEvaluationCompetencyAxisTraitValue.ts修正後、eslint-disable削除
  const competencyFeature: CompetencyFeature =
    traitValueImtRecord.getCompetencyFeature();

  if (!competencyFeature) {
    return null;
  }

  const featureLabel =
    traitValueImtRecord.getCompetencyFeatureLabel(competencyFeature);
  if (!featureLabel) {
    return null;
  }

  const featureHelp =
    traitValueImtRecord.getCompetencyFeatureHelp(competencyFeature);
  const titleLabel = featureHelp.title;

  return (
    <li className={styles.item}>
      <dl>
        <dt className={styles.itemKey}>
          <span>{titleLabel}</span>
          <HelpTooltip help={featureHelp} />
        </dt>
        <dd>
          <span>{featureLabel}</span>
        </dd>
      </dl>
    </li>
  );
};

export default ContentListItemHrEvaluationCompetency;
