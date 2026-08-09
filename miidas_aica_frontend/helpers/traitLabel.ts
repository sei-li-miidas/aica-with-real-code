import {
  TRAITS as COMPANY_TRAITS,
  TRAIT_OPTION_VALUES as COMPANY_TRAIT_OPTION_VALUES,
} from "@/constants/companies";
import {
  POSITION_DETAIL,
  POSITION_LABEL_DISPLAY_TYPE,
  TRAIT_OPTION_VALUES,
} from "@/constants/position";
// eslint-disable-next-line import/no-deprecated
import type MasterV2Record from "@/models/records/MasterV2";
import type TraitRecord from "@/models/position/records/Trait";
import { type ValuesType } from "@/types/utility-types";

/**
 * 表示用のラベルを取得する
 * NOTE: 求人詳細TOPのサマリ、求人詳細、求人カードでラベルを変えているケースをここに追加する
 */
export const getModifiedLabel = (
  traitId: string,
  // eslint-disable-next-line import/no-deprecated
  traitImtRecord: MasterV2Record | TraitRecord,
  type: ValuesType<typeof POSITION_LABEL_DISPLAY_TYPE>,
) => {
  if (!traitImtRecord) {
    return "";
  }

  const label = traitImtRecord.Name;
  // 年間休日
  if (traitId === COMPANY_TRAITS.CTX_YEAR_HOLIDAYS.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.CARD) {
      const traitValue = traitImtRecord.ID;
      if (
        traitValue &&
        [
          COMPANY_TRAIT_OPTION_VALUES.CTX_YEAR_HOLIDAYS.OVER_120, // 120日以上
          COMPANY_TRAIT_OPTION_VALUES.CTX_YEAR_HOLIDAYS.OVER_130, // 130日以上
          COMPANY_TRAIT_OPTION_VALUES.CTX_YEAR_HOLIDAYS.OVER_140, // 140日以上
        ].includes(traitValue)
      ) {
        return `年間休日${label}`;
      }
    }
  }
  // 平均残業時間
  if (traitId === POSITION_DETAIL.OVERTIME_AVG.ID) {
    const traitValue = traitImtRecord.ID;
    if (type === POSITION_LABEL_DISPLAY_TYPE.SUMMARY) {
      if (traitValue === TRAIT_OPTION_VALUES.OVERTIME_AVG.NONE) {
        // 原則なし
        return "原則残業なし";
      }
    }
    if (type === POSITION_LABEL_DISPLAY_TYPE.CARD) {
      if (traitValue === TRAIT_OPTION_VALUES.OVERTIME_AVG.NONE) {
        // 原則なし
        return "残業なし";
      }
      if (
        traitValue === TRAIT_OPTION_VALUES.OVERTIME_AVG.UNDER_10H || // 月10時間以内
        traitValue === TRAIT_OPTION_VALUES.OVERTIME_AVG.UNDER_20H // 月20時間以内
      ) {
        return `残業${label}`;
      }
    }
  }
  // 勤務時間制度
  if (traitId === POSITION_DETAIL.WORK_TIME_SYSTEM.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.CARD) {
      const traitValue = traitImtRecord.ID;
      if (traitValue === TRAIT_OPTION_VALUES.WORK_TIME_SYSTEM.FIXED) {
        // 勤務時間固定制
        return "勤務時間固定";
      }
    }
  }
  // 在宅勤務
  if (traitId === POSITION_DETAIL.REMOTE_WORK.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.SUMMARY) {
      const traitValue = traitImtRecord.ID;
      if (traitValue === TRAIT_OPTION_VALUES.REMOTE_WORK.NG) {
        // なし
        return "NG";
      }
      // 在宅勤務OK
      return "OK";
    }
  }

  // HWエンジニア-キャリアパス
  if (traitId === POSITION_DETAIL.CAREER_PATH_WORK_HEAD_OFFICE_EXISTS.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `キャリアパス：${label}`;
    }
  }
  // 組織-エンジニア出身役員
  if (traitId === POSITION_DETAIL.ORG_TREND_ENGINEER_MANAGER_EXISTS.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `組織：${label}`;
    }
  }
  // 組織-エンジニアと他部署（企画、営業など）との関係性
  if (traitId === POSITION_DETAIL.ORG_TREND_RELATED_WITH_ENGINEER.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `エンジニアと他部署（企画、営業など）との関係性：${label}`;
    }
  }
  // 組織-管理専門職 配属部署の人数
  if (traitId === POSITION_DETAIL.ORG_TREND_SECTION_MEMBER_QTY.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `配属部署の人数：${label}人`;
    }
  }
  // 組織-管理専門職 会計士、税理士在籍
  if (traitId === POSITION_DETAIL.ORG_TREND_ACCOUNTING_LICENCE_EXISTS.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `組織：${label}`;
    }
  }
  // 組織-管理専門職 弁護士、弁理士在籍
  if (traitId === POSITION_DETAIL.ORG_TREND_LEGAL_LICENCE_EXISTS.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `組織：${label}`;
    }
  }
  // HWエンジニア-開発スパン
  if (traitId === POSITION_DETAIL.DEVELOPMENT_TERM.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `開発スパン：${label}`;
    }
  }
  // 営業-個人の業績目標の達成率
  if (traitId === POSITION_DETAIL.ACCOMPLISHMENT_RATE.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `個人の業績目標の達成率：${label}`;
    }
  }
  // 営業-新規飛び込み営業
  if (traitId === POSITION_DETAIL.SALES_STYLE_DIVE.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `新規飛び込み営業：${label}`;
    }
  }
  // 営業-新規テレアポ（電話営業）
  if (traitId === POSITION_DETAIL.SALES_STYLE_TEL_APPOINTMENT.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `新規テレアポ（電話営業）：${label}`;
    }
  }
  // 営業-接待
  if (traitId === POSITION_DETAIL.SALES_STYLE_HOST.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `接待：${label}`;
    }
  }
  // 営業/サービス-他部署への異動
  if (traitId === POSITION_DETAIL.CAREER_PATH_OUT_OF_SITE_EXISTS.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `他部署への異動：${label}`;
    }
  }
  // 緊急対応
  if (traitId === POSITION_DETAIL.EMERGENCY_SUPPORT.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `緊急対応：${label}`;
    }
  }

  // オフィス出社
  if (traitId === POSITION_DETAIL.REMOTE_WORK_OFFICE_FREQUENCY.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `オフィス出社：${label}`;
    }
  }
  // 試用期間
  if (traitId === POSITION_DETAIL.PROBATION.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `※試用期間：${label}`;
    }
  }
  // 契約更新
  if (traitId === POSITION_DETAIL.CONTRACT_RENEWAL.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `※契約更新：${label}`;
    }
  }
  // 海外売上比率
  if (traitId === COMPANY_TRAITS.CTX_SALES_OVERSEAS_RATE.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `※${label}`;
    }
  }
  // 国内転勤の頻度
  if (traitId === POSITION_DETAIL.TRANSFERENCE_FREQUENCY.ID) {
    if (type === POSITION_LABEL_DISPLAY_TYPE.DETAIL) {
      return `国内転勤の頻度：${label}`;
    }
  }

  return label;
};
