import { Record } from "immutable";
import { ArrayFinder } from "@/utils/finder";
import {
  OUTSOURCING_APPEAL_WORK_TYPE_ID_CONSULTANT,
  OUTSOURCING_APPEAL_WORK_TYPE_ID_RESEARCH,
  OUTSOURCING_APPEAL_WORK_TYPE_MASTER,
} from "@/constants/position";
import { type ArrayElement } from "@/types/utility-types";

type Props = {
  /** 業務内容 */
  WorkType: ArrayElement<typeof OUTSOURCING_APPEAL_WORK_TYPE_MASTER>["ID"];
};

// アピールポイント設定値のレコード
export default class OutsourcingAppealRecord extends Record<Props>({
  WorkType: 0,
}) {
  /**
   * isShowWorkTypeAppeal
   * 業務内容のアピールラベルを表示するかどうかを返却
   */
  isShowWorkTypeAppeal() {
    return (
      this.WorkType === OUTSOURCING_APPEAL_WORK_TYPE_ID_CONSULTANT ||
      this.WorkType === OUTSOURCING_APPEAL_WORK_TYPE_ID_RESEARCH
    );
  }

  /**
   * getWorkTypeLabel
   * 「業務内容」の内訳のラベルを返却
   */
  // readonly type errorが出るのでspread operator使う
  getWorkTypeLabel() {
    return ArrayFinder.findNameById(
      [...OUTSOURCING_APPEAL_WORK_TYPE_MASTER],
      this.WorkType,
    );
  }
}
