import { Record, List } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";
import MasterV2Record from "@/models/records/MasterV2";

type Props = {
  ID: number | null;
  Name: string;
  Note: string;
  Options: Immutable.List<MasterV2Record>;
};

/** 値が単一のBTIトレイト */
export default class BTISingleTrait extends Record<Props>({
  ID: null,
  Name: "",
  Note: "",
  Options: List([]),
}) {
  constructor(btiSingleTrait: RecordConstructorParameter<BTISingleTrait>) {
    super({
      ...btiSingleTrait,
      Options: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        (btiSingleTrait.Options || []).map(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (option) => new MasterV2Record(option),
        ),
      ),
    });
  }
}
