import { Record, List } from "immutable";
import SpotExpLevelItemRecord from "@/models/records/SpotExpLevelItem";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** 分類No. */
  ClassNo: string;
  /** 分類No.ごとの選択肢（SpotExpLevelItemRecord）のリスト */
  List: List<SpotExpLevelItemRecord>;
};

/**
 * SpotExpLevel
 * スポット応募時の熟練度回答の複数選択肢を管理するレコード
 */
export default class SpotExpLevel extends Record<Props>({
  ClassNo: "",
  List: List([]),
}) {
  constructor(spotExpLevel: RecordConstructorParameter<SpotExpLevel>) {
    const spotExpLevelItemsImtList = List(
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      (spotExpLevel.List || []).map((item) => {
        return new SpotExpLevelItemRecord(item);
      }),
    );

    const spotExpLevelRecord = {
      ...spotExpLevel,
      List: spotExpLevelItemsImtList,
    };

    // @ts-expect-error: 型エラーが起きないよう後で修正する
    super(spotExpLevelRecord);
  }
}
