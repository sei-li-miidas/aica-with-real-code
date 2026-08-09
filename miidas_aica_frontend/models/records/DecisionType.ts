import { Record, OrderedMap } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";
import MasterV2Record from "./MasterV2";

type Props = {
  Type1: MasterV2Record | null;
  Type2: MasterV2Record | null;
  Type3: MasterV2Record | null;
  Type4: MasterV2Record | null;
  Note: string;
};

/** 意思決定と裁量(旧 btx_decision_type) */
export default class DecisionType extends Record<Props>({
  Type1: null,
  Type2: null,
  Type3: null,
  Type4: null,
  Note: "",
}) {
  constructor(decisionType: RecordConstructorParameter<DecisionType>) {
    super({
      ...decisionType,
      Type1: decisionType.Type1 ? new MasterV2Record(decisionType.Type1) : null,
      Type2: decisionType.Type2 ? new MasterV2Record(decisionType.Type2) : null,
      Type3: decisionType.Type3 ? new MasterV2Record(decisionType.Type3) : null,
      Type4: decisionType.Type4 ? new MasterV2Record(decisionType.Type4) : null,
    });
  }

  /**
   * 全ての意思決定と裁量を反復順序が保障された形で取得する
   */
  getValuesOrderedMap() {
    return OrderedMap({
      Type1: this.Type1?.ID || null,
      Type2: this.Type2?.ID || null,
      Type3: this.Type3?.ID || null,
      Type4: this.Type4?.ID || null,
    });
  }
}
