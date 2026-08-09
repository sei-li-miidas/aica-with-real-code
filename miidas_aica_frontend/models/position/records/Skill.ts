import { Record } from "immutable";

type Props = {
  /** スキルID */
  ID: number | null;
  /** スキル名 */
  Name: string;
  /** メインスキルフラグ */
  Main: boolean;
};

/**
 * Skill
 * 仕事内容のスキルレコード
 */
export default class Skill extends Record<Props>({
  ID: null,
  Name: "",
  Main: false,
}) {}
