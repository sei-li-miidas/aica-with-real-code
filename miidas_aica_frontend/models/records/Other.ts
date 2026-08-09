import { Record, List } from "immutable";
import type MasterV2Record from "@/models/records/MasterV2";

type Props = {
  Note: string;
  IDs: List<MasterV2Record>;
  Options: List<MasterV2Record>;
};

/** その他企業特徴(旧 ctx_other) */
export default class Other extends Record<Props>({
  Note: "",
  IDs: List([]),
  Options: List([]),
}) {}
