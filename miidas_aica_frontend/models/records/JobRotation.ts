import { Record } from "immutable";

type Flg = {
  On: boolean;
  Name: string;
};

type Props = {
  Flg: Flg | null;
  Note: string;
};

/** キャリア-ジョブローテーション(旧 ctx_job_rotation_exists) */
export default class JobRotation extends Record<Props>({
  Note: "",
  Flg: null,
}) {}
