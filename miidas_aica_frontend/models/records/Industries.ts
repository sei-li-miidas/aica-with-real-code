import { Record, List } from "immutable";
import BusinessRecord from "@/models/position/records/business/traitValue/Business";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  Industries: Immutable.List<BusinessRecord>;
  Note: string;
};

/** 事業内容(旧 btx_business_industry) */
export default class Industries extends Record<Props>({
  Industries: List([]),
  Note: "",
}) {
  constructor(industries: RecordConstructorParameter<Industries>) {
    super({
      ...industries,
      Industries: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        (industries.Industries || []).map(
          // @ts-expect-error: 型エラーが起きないよう後で修正する
          (industry) => new BusinessRecord(industry),
        ),
      ),
    });
  }

  /**
   * メインの事業内容レコードを取得する
   */
  getMainBusinessRecord() {
    return this.Industries.find((industryImtRecord) => {
      return industryImtRecord.IsMain;
    });
  }
}
