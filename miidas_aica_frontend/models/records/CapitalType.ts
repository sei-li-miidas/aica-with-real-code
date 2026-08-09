import { Record, List } from "immutable";
import type MasterV2Record from "@/models/records/MasterV2";

type Props = {
  Note: string;
  IDs: List<MasterV2Record>;
  Options: List<MasterV2Record>;
};

/** 企業概要-資本区分(旧 ctx_capital_type) */
export default class CapitalType extends Record<Props>({
  Note: "",
  IDs: List([]),
  Options: List([]),
}) {}
