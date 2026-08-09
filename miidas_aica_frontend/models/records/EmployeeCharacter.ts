import { Record, OrderedMap } from "immutable";
import { type RecordConstructorParameter } from "@/types/utility-types";
import MasterV2Record from "./MasterV2";

type Props = {
  Character1: MasterV2Record | null;
  Character2: MasterV2Record | null;
  Character3: MasterV2Record | null;
  Character4: MasterV2Record | null;
  Character5: MasterV2Record | null;
  Character6: MasterV2Record | null;
  Character7: MasterV2Record | null;
  Character8: MasterV2Record | null;
  Character9: MasterV2Record | null;
  Character10: MasterV2Record | null;
  Character11: MasterV2Record | null;
  Character12: MasterV2Record | null;
  Note: string;
};

/** 組織・社員の特徴(旧 btx_employee_character) */
export default class EmployeeCharacter extends Record<Props>({
  Character1: null,
  Character2: null,
  Character3: null,
  Character4: null,
  Character5: null,
  Character6: null,
  Character7: null,
  Character8: null,
  Character9: null,
  Character10: null,
  Character11: null,
  Character12: null,
  Note: "",
}) {
  constructor(
    employeeCharacter: RecordConstructorParameter<EmployeeCharacter>,
  ) {
    super({
      ...employeeCharacter,
      Character1: employeeCharacter.Character1
        ? new MasterV2Record(employeeCharacter.Character1)
        : null,
      Character2: employeeCharacter.Character2
        ? new MasterV2Record(employeeCharacter.Character2)
        : null,
      Character3: employeeCharacter.Character3
        ? new MasterV2Record(employeeCharacter.Character3)
        : null,
      Character4: employeeCharacter.Character4
        ? new MasterV2Record(employeeCharacter.Character4)
        : null,
      Character5: employeeCharacter.Character5
        ? new MasterV2Record(employeeCharacter.Character5)
        : null,
      Character6: employeeCharacter.Character6
        ? new MasterV2Record(employeeCharacter.Character6)
        : null,
      Character7: employeeCharacter.Character7
        ? new MasterV2Record(employeeCharacter.Character7)
        : null,
      Character8: employeeCharacter.Character8
        ? new MasterV2Record(employeeCharacter.Character8)
        : null,
      Character9: employeeCharacter.Character9
        ? new MasterV2Record(employeeCharacter.Character9)
        : null,
      Character10: employeeCharacter.Character10
        ? new MasterV2Record(employeeCharacter.Character10)
        : null,
      Character11: employeeCharacter.Character11
        ? new MasterV2Record(employeeCharacter.Character11)
        : null,
      Character12: employeeCharacter.Character12
        ? new MasterV2Record(employeeCharacter.Character12)
        : null,
    });
  }

  /**
   * 全ての組織・社員の特徴を反復順序が保障された形で取得する
   */
  getValuesOrderedMap() {
    return OrderedMap({
      Character1: this.Character1?.ID || null,
      Character2: this.Character2?.ID || null,
      Character3: this.Character3?.ID || null,
      Character4: this.Character4?.ID || null,
      Character5: this.Character5?.ID || null,
      Character6: this.Character6?.ID || null,
      Character7: this.Character7?.ID || null,
      Character8: this.Character8?.ID || null,
      Character9: this.Character9?.ID || null,
      Character10: this.Character10?.ID || null,
      Character11: this.Character11?.ID || null,
      Character12: this.Character12?.ID || null,
    });
  }
}
