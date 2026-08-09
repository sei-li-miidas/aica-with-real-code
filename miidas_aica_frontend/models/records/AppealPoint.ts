import { Record, List } from "immutable";
import type MasterV2Record from "@/models/records/MasterV2";

type Props = {
  Note: string;
  IDs: List<MasterV2Record>;
  Options: List<MasterV2Record>;
};

/** 企業概要-当社のアピールポイント(旧 ctx_appeal_point) */
export default class AppealPoint extends Record<Props>({
  Note: "",
  IDs: List([]),
  Options: List([]),
}) {}
