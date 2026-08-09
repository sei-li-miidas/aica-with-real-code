import { Record, List } from "immutable";

import SkillGroupRecord from "@/models/position/records/SkillGroup";
import { type RecordConstructorParameter } from "@/types/utility-types";

type Props = {
  /** 職種小ID */
  SmallID: number | null;
  /** 職種小名 */
  Name: string;
  /** スキルグループ一覧 */
  SkillGroups: List<SkillGroupRecord>;
  /** メイン仕事内容フラグ */
  Main: boolean;
};

/**
 * Job
 * 仕事内容のレコード
 */
export default class Job extends Record<Props>({
  SmallID: null,
  Name: "",
  SkillGroups: List([]),
  Main: false,
}) {
  constructor(job: RecordConstructorParameter<Job>) {
    super({
      ...job,
      SkillGroups: List(
        // @ts-expect-error: 型エラーが起きないよう後で修正する
        job.SkillGroups?.map((skillGroup) => new SkillGroupRecord(skillGroup)),
      ),
    });
  }
}
