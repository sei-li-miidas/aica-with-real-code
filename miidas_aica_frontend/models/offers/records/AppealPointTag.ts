import { Record } from "immutable";

type GenreSvgIconMapKeyType =
  | "work_time"
  | "remote"
  | "income"
  | "inexperienced_welcome";

type Props = {
  /** アイコン表示用のジャンル */
  Genre: GenreSvgIconMapKeyType | null;
  /** ラベル文字列 */
  Label: string;
  /** 強調するラベルかどうか */
  IsImportant: boolean;
};

/**
 * 求人画面に表示するアピールポイントタグ用のレコード
 */
export default class AppealPointTagRecord extends Record<Props>({
  Genre: null,
  Label: "",
  IsImportant: false,
}) {}
