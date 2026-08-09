import { Record } from "immutable";

import { type ValuesType } from "@/types/utility-types";
import { HR_EVALUATION_COMPETENCY_FEATURES } from "@/constants/position";

export type CompetencyFeature = ValuesType<
  typeof HR_EVALUATION_COMPETENCY_FEATURES
>;

type Props = {
  /** 特に評価されるコンピテンシー特徴の項目 */
  Axis: string;
  /** 特に評価されるコンピテンシー特徴のスコア */
  Value: number | null;
};

/**
 * HrEvaluationCompetencyAxisTraitValue
 * 特に評価されるコンピテンシー特徴のTraitValueレコード
 */
export default class HrEvaluationCompetencyAxisTraitValue extends Record<Props>(
  {
    Axis: "",
    Value: null,
  },
) {
  /**
   * 特に評価されるコンピテンシーの特徴を取得する
   */
  getCompetencyFeature() {
    const axis = this.Axis;
    // TODO: ts 型エラーが起きないよう後で修正する
    // @ts-expect-error 型エラーが起きないよう後で修正する
    // eslint-disable-next-line @typescript-eslint/no-unsafe-return
    return HR_EVALUATION_COMPETENCY_FEATURES[axis];
  }

  /**
   * 特に評価されるコンピテンシーの特徴のラベルを取得する
   */
  getCompetencyFeatureLabel(competencyFeature: CompetencyFeature) {
    if (this.Value) {
      return competencyFeature.Options.find(
        (option) => option.Value === this.Value,
      )?.Name;
    }
    return "";
  }

  /**
   * 特に評価されるコンピテンシーの特徴のヘルプを取得する
   */
  getCompetencyFeatureHelp(competencyFeature: CompetencyFeature) {
    if (this.Value) {
      const title = competencyFeature.Label;
      const text = competencyFeature.Options.find(
        (option) => option.Value === this.Value,
      )?.Help;
      return { title, text };
    }
    return { title: "", text: "" };
  }
}
