import { type MFC, type ReactNode, type ElementType } from "react";

import GroupHeader from "@/components/positions/detail/parts/GroupHeader";

type Props = {
  title: ReactNode;
  children?: ReactNode;
  itemTagName?: ElementType;
};

/**
 * セクションのリストアイテム
 * セクション...「募集要項」「選考方法」など
 * リストアイテム...「募集要項」の中の「求人のポイント」「企業の特徴」など
 */
const SectionListItem: MFC<Props> = ({
  title,
  children,
  itemTagName: Container = "li",
}) => {
  return (
    <Container>
      <section>
        <GroupHeader>{title}</GroupHeader>
        {children}
      </section>
    </Container>
  );
};

export default SectionListItem;
