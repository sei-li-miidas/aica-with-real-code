import { type TRAIT_EMPLOYMENT_TYPE } from "@/constants/position";
import { type ValuesType } from "@/types/utility-types";
import { Record } from "immutable";

// 契約形態の型
export type EmploymentType = ValuesType<typeof TRAIT_EMPLOYMENT_TYPE>;

/**
 * 契約形態用データのレコード
 */
export default class TraitEmploymentType extends Record<{
  /** ID */
  ID: EmploymentType | null;
  /** 名前 */
  Name: string;
  /** 補足事項 */
  Note: string;
}>({
  ID: null,
  Name: "",
  Note: "",
}) {}
