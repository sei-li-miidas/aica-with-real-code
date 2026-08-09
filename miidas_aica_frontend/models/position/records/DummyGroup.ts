import { Record, List } from "immutable";

import SkillRecord from "./Skill";

import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** 偽階層グループ名 */
  Name: string;
  /** スキル一覧 */
  Skills: List<SkillRecord>;
};

/**
 * DummyGroup
 * 仕事内容の偽階層グループレコード
 */
export default class DummyGroup extends Record<Props>({
  Name: "",
  Skills: List([]),
}) {
  constructor(dummyGroup: RecordConstructorParameter<DummyGroup>) {
    super({
      ...dummyGroup,
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      Skills: List(dummyGroup.Skills?.map((skill) => new SkillRecord(skill))),
    });
  }

  /**
   * 偽階層グループ名が空かどうか
   */
  isNameEmpty() {
    return !this.Name;
  }
}
