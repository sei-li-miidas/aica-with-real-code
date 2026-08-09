import { Record } from "immutable";

type Flg = {
  On: boolean;
  Name: string;
};

type Props = {
  Flg: Flg | null;
  Note: string;
};

/** キャリア-異動希望申請制度(旧 ctx_change_department_request) */
export default class ChangeDepartment extends Record<Props>({
  Note: "",
  Flg: null,
}) {}
