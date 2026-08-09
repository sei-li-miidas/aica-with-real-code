import { Record, List } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";
import MasterV2Record from "@/models/records/MasterV2";

type Props = {
  IDs: Immutable.List<MasterV2Record>;
  Note: string;
  Options: Immutable.List<MasterV2Record>;
};

/** 値が複数のBTIトレイト */
export default class BTIMultipleTrait extends Record<Props>({
  IDs: List([]),
  Note: "",
  Options: List([]),
}) {
  constructor(btiMultipleTrait: RecordConstructorParameter<BTIMultipleTrait>) {
    super({
      ...btiMultipleTrait,
      IDs: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        (btiMultipleTrait.IDs || []).map((idObj) => new MasterV2Record(idObj)),
      ),
      Options: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        (btiMultipleTrait.Options || []).map(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (option) => new MasterV2Record(option),
        ),
      ),
    });
  }
}
