import { type ReactNode } from "react";

type Master = {
  Name: string;
};

/**
 * MasterRecord形式のRecordからラベルを取得
 */
export const getLabelFromMasterRecord = (
  imtRecord: Master | null | undefined,
) => {
  return imtRecord?.Name || "";
};

/**
 * セクションのリストアイテム内に表示するトレイトの値が１つでもあるかを返す
 */
export const hasSomeTraitValues = (items: ReactNode[]) => {
  return items.some((value) => !!value);
};
