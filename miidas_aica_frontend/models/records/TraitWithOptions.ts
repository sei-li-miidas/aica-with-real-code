import { Record, List } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";
import MasterV2Record from "@/models/records/MasterV2";

type Props = {
  /** ID */
  ID: number | null;
  /** 補足事項 */
  Note: string;
  /** その他ラベル */
  Options: List<MasterV2Record>;
};

/**
 * 補足とオプションがあるレコード
 */
export default class TraitWithOptions extends Record<Props>({
  ID: null,
  Note: "",
  Options: List([]),
}) {
  constructor(value: RecordConstructorParameter<TraitWithOptions>) {
    super({
      ...value,
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      Options: List(value.Options?.map((option) => new MasterV2Record(option))),
    });
  }
}
