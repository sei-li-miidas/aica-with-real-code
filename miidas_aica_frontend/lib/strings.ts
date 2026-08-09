export function removeSpaces(str: string): string {
  return str.replace(/\s/g, "");
}

export interface IThinkingSeparated {
  thinking: string;
  message: string;
}
