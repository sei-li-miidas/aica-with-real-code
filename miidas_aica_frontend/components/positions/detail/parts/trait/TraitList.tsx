import { type MFC, type ReactNode } from "react";

type Props = {
  children: ReactNode;
};

/**
 * トレイトのリスト
 */
const TraitList: MFC<Props> = ({ children }) => {
  return <dl>{children}</dl>;
};

export default TraitList;
