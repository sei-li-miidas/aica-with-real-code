export type FilterModalType =
  | "jobtype"
  | "keyword"
  | "location"
  | "salary"
  | "detail"
  | null;

export type DetailGroupKey = string;

export type SubModalType =
  | null
  | { type: "location-primary" }
  | { type: "location-other" }
  | { type: "detail-item"; key: DetailGroupKey }
  | { type: "jobtype-group"; toolName: string };

export type DetailSelections = Record<DetailGroupKey, string[]>;

export type FilterOptionView = {
  label: string;
  value: string;
  description?: string;
};
