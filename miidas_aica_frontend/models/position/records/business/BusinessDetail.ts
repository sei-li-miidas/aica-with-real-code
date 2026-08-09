import { Record } from "immutable";
import BusinessRecord from "@/models/records/Business";

/**
 * 事業詳細のモデル
 */
export default class BusinessDetail extends Record<{
  /** 事業レコード */
  Business: BusinessRecord;
}>({
  Business: new BusinessRecord({}),
}) {}
