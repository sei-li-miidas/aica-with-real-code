import { Record, List } from "immutable";
import TraitRecord from "@/models/position/records/Trait";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** 値と補足のテキスト */
  Values: List<TraitRecord>;
  /** 勤務地全体に対する補足 */
  Note: string;
};

/**
 * WorkAddress
 * 勤務地のレコード
 */
export default class WorkAddress extends Record<Props>({
  Values: List([]),
  Note: "",
}) {
  constructor(workAddress: RecordConstructorParameter<WorkAddress>) {
    super({
      ...workAddress,
      Values: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        workAddress.Values?.map((target) => new TraitRecord(target)),
      ),
    });
  }

  /**
   * hasSomeValue
   * ひとつでも値を持っているかどうか
   */
  hasSomeValue() {
    return !!this.Values.size;
  }

  /**
   * getWorkLocationForDisplay
   * 表示用の勤務地を返す
   */
  getWorkLocationForDisplay() {
    if (!this.Values) return null;
    // 複数勤務地の場合、「勤務地1、勤務地2、..、勤務地n」の形にする
    const workLocations = this.Values.map((value) => {
      return value.Name;
    }).toArray();
    return workLocations.join(",");
  }
}
