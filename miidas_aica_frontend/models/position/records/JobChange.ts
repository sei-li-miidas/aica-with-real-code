import { Record, Map } from "immutable";

import {
  type ValuesType,
  type RecordConstructorParameter,
} from "@/types/utility-types";

type IncomeValueType = {
  /** 年収from */
  From: number | null;
  /** 年収to */
  To: number | null;
  /** 補足 */
  Note: string;
};

type Props = {
  Income: Map<keyof IncomeValueType, ValuesType<IncomeValueType>>;
};

/**
 * JobChange
 * 確約年収のレコード
 */
export default class JobChange extends Record<Props>({
  Income: Map<keyof IncomeValueType, ValuesType<IncomeValueType>>({
    From: null,
    To: null,
    Note: "",
  }),
}) {
  constructor(jobChange: RecordConstructorParameter<JobChange> = {}) {
    super({
      Income: Map<keyof IncomeValueType, ValuesType<IncomeValueType>>({
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        From: jobChange.Income?.From ? String(jobChange.Income.From) : null,
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        To: jobChange.Income?.To ?? null,
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        Note: jobChange.Income?.Note ?? "",
      }),
    });
  }

  /**
   * isIncomeInputted
   * 報酬が入力されたかを返す
   */
  isIncomeInputted() {
    return !!(this.Income.get("From") || this.Income.get("To"));
  }
}
