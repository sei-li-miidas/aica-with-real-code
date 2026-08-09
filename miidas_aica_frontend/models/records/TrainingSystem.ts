import { Record } from "immutable";

type Props = {
  /** 研修制度 */
  Exists: boolean;
  /** 研修内容 */
  Text: string | null;
};

/**
 * 研修制度
 */
export default class TrainingSystem extends Record<Props>({
  Exists: false,
  Text: null,
}) {}
