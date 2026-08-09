import { Record, List } from "immutable";
import MasterV2Record from "@/models/records/MasterV2";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** 値と名前のテキスト */
  IDs: List<MasterV2Record>;
  /** 補足 */
  Note: string;
};

/**
 * ITEngineerWorkEnvironment
 * 求人特徴 労働環境（ITエンジニア）のレコード
 */
export default class ITEngineerWorkEnvironment extends Record<Props>({
  IDs: List([]),
  Note: "",
}) {
  constructor(value: RecordConstructorParameter<ITEngineerWorkEnvironment>) {
    super({
      ...value,
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      IDs: List(value.IDs?.map((id) => new MasterV2Record(id))),
    });
  }

  /**
   * hasSomeValue
   * ひとつでも値があるかどうか
   */
  hasSomeValue() {
    return !!this.IDs.size;
  }
}
