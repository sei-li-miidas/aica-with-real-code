import { Record, List } from "immutable";
import DummyGroup from "@/models/position/records/DummyGroup";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** スキルグループID */
  ID: number | null;
  /** スキルグループ名 */
  Name: string;
  /** 偽階層グループ一覧 */
  DummyGroups: List<DummyGroup>;
};

/**
 * SkillGroup
 * 仕事内容のスキルグループレコード
 */
export default class SkillGroup extends Record<Props>({
  ID: null,
  Name: "",
  DummyGroups: List([]),
}) {
  constructor(skillGroup: RecordConstructorParameter<Props>) {
    super({
      // @ts-expect-error: 型エラーが起きないよう後で修正する
      ...skillGroup,
      DummyGroups: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        skillGroup.DummyGroups?.map((dummyGroup) => new DummyGroup(dummyGroup)),
      ),
    });
  }
}
