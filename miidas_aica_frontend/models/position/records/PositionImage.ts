import { Record } from "immutable";

type Props = {
  /** 画像のURL */
  URL: string;
  /** メイン画像/サブ画像 */
  DisplayType: number | null;
};

/**
 * 求人画像のレコード
 */
export default class PositionImageRecord extends Record<Props>({
  URL: "",
  DisplayType: null,
}) {}
