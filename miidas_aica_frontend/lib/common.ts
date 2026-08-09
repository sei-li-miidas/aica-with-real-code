import { ChatMessageRole, ItemType, WorkflowDisplayType, WorkflowStepSelectionType } from "@/constants/enum";
import { KeyValue } from "@/types/utility-types";

export enum PositionSearchFilterType {
  Single = "single",
  Multiple = "multiple",
}

export interface PositionSearchOtherFilterOption {
  Label: string;
  Value: string;
}

export interface PositionSearchFilterOption extends PositionSearchOtherFilterOption {
  Selected: boolean;
}

export interface JobtypePositionSearchFilterOption extends PositionSearchFilterOption {
  Description: string;
}

export interface LocationPositionSearchFilterOption extends PositionSearchFilterOption {
  PrefectureName: string;
  CityName: string;
}

export type GroupedJobtypePositionSearchFilterOptions = Record<
  string,
  JobtypePositionSearchFilterOption[]
>;

export type GroupedJobtypeNamesWithSameSearchFilters = Record<string, string[]>;
export type GroupedOtherFilters = Record<
  string,
  PositionSearchFilter<PositionSearchOtherFilterOption>[]
>;
export type GroupedSelectedFilterOptions = Record<
  string,
  Record<string, string[]>
>;

export interface SinglePositionSearchFilter<
  T extends PositionSearchOtherFilterOption,
> {
  Key: string;
  Name: string;
  Type: PositionSearchFilterType.Single;
  Options: T[];
}

export interface JobtypePositionSearchFilter extends SinglePositionSearchFilter<JobtypePositionSearchFilterOption> {
  Options: JobtypePositionSearchFilterOption[];
}

export type MultiplePositionSearchFilter<
  T extends PositionSearchOtherFilterOption,
> = {
  Key: string;
  Name: string;
  Type: PositionSearchFilterType.Multiple;
  Options: T[];
};

export type PositionSearchFilter<T extends PositionSearchOtherFilterOption> =
  | SinglePositionSearchFilter<T>
  | MultiplePositionSearchFilter<T>;

export interface IPositionSummary {
  ID: string;
  Title: string;
  MainJobText: string;
  SalaryFrom: string;
  SalaryTo: string;
  Image: string;
  messages: IMessageItem[];
}

export interface IPositionRecommendation {
  Theme: string;
  Title: string;
  Description?: string;
}

export interface IPositionSearchResult {
  SearchKey: string;
  TotalPositionCount: number;
  Positions: IPositionSummary[];
  Recommendations: IPositionRecommendation[];
}

export interface IPositionSearchLink {
  ToolCallId: string;
  Salary: number;
  Residence: string;
  WorkLocations: string[];
  IsFullyRemoteWork: boolean;
  PositionKeyword: string;
  JobtypeNames: string[];
}

export interface IJobtypeSearchResult {
  ToolCallId: string;
  Keyword?: string;
  Jobtypes: KeyValue[];
  Choice: string;
}

// 会話履歴
export interface IItem {
  readonly itemType: ItemType;
  role: ChatMessageRole;
  itemId: string;
}

// 会話メッセージ（ユーザーかAgent）
export interface INormalMessageItem extends Omit<IItem, "itemType"> {
  readonly itemType: ItemType.ChatMessage;
  message: string;
}

// ポジション検索ツールの結果
export interface IPositionSearchResultItem extends Omit<IItem, "itemType"> {
  readonly itemType: ItemType.PositionSearchResult;
  positionSearchResult: IPositionSearchResult;
}

// 過去履歴ロード時のポジション検索アクション
export interface IPositionSearchLinkItem extends Omit<IItem, "itemType"> {
  readonly itemType: ItemType.PositionSearchLink;
  positionSearchLink: IPositionSearchLink;
}

// 職種検索ツールの結果
export interface IJobtypeSearchResultItem extends Omit<IItem, "itemType"> {
  readonly itemType: ItemType.JobtypeSearchResult;
  jobtypeSearchResult: IJobtypeSearchResult;
}

// ワークフロー
export interface IWorkflowOptionItem {
  label: string;
  value: number;
  allowFreeText: boolean;
  jobNature?: string;
  description?: string;
}

export interface IWorkflowCategoryOption {
  id: string;
  name: string;
  items: IWorkflowOptionItem[];
}

export interface IWorkflowStep {
  id: number;
  question: string;
  questionPrompt: string;
  selectionType: WorkflowStepSelectionType;
  options: IWorkflowCategoryOption[] | IWorkflowOptionItem[];
}

export interface IWorkflowDefinition {
  id: string;
  name: string;
  displayType: WorkflowDisplayType;
  steps: IWorkflowStep[];
}

export interface IWorkflowItem extends Omit<IItem, "itemType"> {
  readonly itemType: ItemType.Workflow;
  workflowDefinition: IWorkflowDefinition;
}

// 過去履歴ロード時のワークフロー再実行ボタン（displayType: modal 用）
export interface IRestartWorkflowButtonItem extends Omit<IItem, "itemType"> {
  readonly itemType: ItemType.RestartWorkflowButton;
  workflowDefinition: IWorkflowDefinition;
}

// エラー
export interface IErrorItem extends Omit<INormalMessageItem, "itemType"> {
  readonly itemType: ItemType.Error;
}

// 未知（基本ないはず）
export interface IUnknownItem extends Omit<INormalMessageItem, "itemType"> {
  readonly itemType: ItemType.Unknown;
}

export type IMessageItem = INormalMessageItem | IErrorItem | IUnknownItem;

export const createNormalMessageItem = (
  role: ChatMessageRole,
  itemId: string,
  message: string,
): INormalMessageItem => {
  return {
    itemType: ItemType.ChatMessage,
    role: role,
    itemId: itemId,
    message: message,
  };
};

export const createWorkflowItem = (
  itemId: string,
  message: string | IWorkflowDefinition,
): IWorkflowItem => {
  try {
    const workflowDefinition =
      typeof message === "string" ? JSON.parse(message) : message;

    return {
      itemType: ItemType.Workflow,
      role: ChatMessageRole.Agent,
      itemId: itemId,
      workflowDefinition: workflowDefinition,
    };
  } catch (error) {
    throw new Error(
      `Failed to parse workflow definition JSON for itemId ${itemId}: ${error}`,
    );
  }
};

export const createRestartWorkflowButtonItem = (
  itemId: string,
  workflowDefinition: IWorkflowDefinition,
): IRestartWorkflowButtonItem => {
  return {
    itemType: ItemType.RestartWorkflowButton,
    role: ChatMessageRole.Agent,
    itemId: itemId,
    workflowDefinition: workflowDefinition,
  };
};

export const createPositionSearchResultItem = (
  itemId: string,
  message: string,
): IPositionSearchResultItem => {
  try {
    const positionSearchResult = JSON.parse(message);

    return {
      itemType: ItemType.PositionSearchResult,
      role: ChatMessageRole.Agent,
      itemId: itemId,
      positionSearchResult,
    };
  } catch (error) {
    throw new Error(
      `Failed to parse position search result JSON for itemId ${itemId}: ${error}`,
    );
  }
};

export const createPositionSearchLinkItem = (
  itemId: string,
  message: string | IPositionSearchLink,
): IPositionSearchLinkItem => {
  try {
    const positionSearchLink =
      typeof message === "string" ? JSON.parse(message) : message;

    return {
      itemType: ItemType.PositionSearchLink,
      role: ChatMessageRole.Agent,
      itemId: itemId,
      positionSearchLink: positionSearchLink,
    };
  } catch (error) {
    throw new Error(
      `Failed to parse position search link JSON for itemId ${itemId}: ${error}`,
    );
  }
};

export const createJobtypeSearchResultItem = (
  itemId: string,
  message: string | IJobtypeSearchResult,
): IJobtypeSearchResultItem => {
  try {
    const jobtypeSearchResult =
      typeof message === "string" ? JSON.parse(message) : message;

    return {
      itemType: ItemType.JobtypeSearchResult,
      role: ChatMessageRole.Agent,
      itemId: itemId,
      jobtypeSearchResult,
    };
  } catch (error) {
    throw new Error(
      `Failed to parse jobtype search result JSON for itemId ${itemId}: ${error}`,
    );
  }
};

export const createErrorItem = (
  itemId: string,
  message: string,
): IErrorItem => {
  return {
    itemType: ItemType.Error,
    role: ChatMessageRole.Agent,
    itemId: itemId,
    message: message,
  };
};

export const createUnknownItem = (
  itemId: string,
  message: string,
): IUnknownItem => {
  return {
    itemType: ItemType.Unknown,
    role: ChatMessageRole.Agent,
    itemId: itemId,
    message: message,
  };
};

export const formatResidenceAddress = (
  address:
    | {
        CityName?: string;
        PrefectureName?: string;
      }
    | undefined,
): string => {
  if (!address) return "";
  return `${address.PrefectureName ?? ""}${address.CityName ?? ""}`;
};
