import { Record, List } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";
import HrEvaluationCompetencyAxisRecord from "./traitValue/HrEvaluationCompetencyAxisTraitValue";

type Props = {
  /** 特に評価されるコンピテンシー特徴の項目と値 */
  Axes: List<HrEvaluationCompetencyAxisRecord>;
  /** 補足 */
  Note: string;
};

/**
 * HrEvaluationCompetency
 * 特に評価されるコンピテンシーのvalueレコード
 */
export default class HrEvaluationCompetency extends Record<Props>({
  Axes: List([]),
  Note: "",
}) {
  constructor(value: RecordConstructorParameter<HrEvaluationCompetency>) {
    super({
      ...value,
      Axes: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        value.Axes?.map(
          (
            axis: RecordConstructorParameter<HrEvaluationCompetencyAxisRecord>,
          ) => new HrEvaluationCompetencyAxisRecord(axis),
        ),
      ),
    });
  }
}
