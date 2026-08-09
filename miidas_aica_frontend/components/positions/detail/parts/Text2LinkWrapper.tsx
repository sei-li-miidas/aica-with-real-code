import { useRef, type MFC, type ElementType, type RefObject } from "react";

import Text2Link from "@/containers/app/Text2Link";
import { clsx } from "@/utils/className";

import styles from "./Text2LinkWrapper.module.scss";

type Props = {
  text?: string;
  className?: string;
  itemTagName?: ElementType;
  wrapContainerRef?: RefObject<HTMLElement>;
};

/**
 * テキストの中のURLやメールアドレスをリンクに変換するWrapper
 */
const Text2LinkWrapper: MFC<Props> = ({
  text = "",
  className = "",
  itemTagName: Container = "p",
  wrapContainerRef = null,
}) => {
  const localContainerRef = useRef<HTMLElement>(null);
  const containerRef = wrapContainerRef || localContainerRef;

  const cls = clsx(styles.container, className);

  return (
    <Container className={cls} ref={containerRef}>
      <Text2Link text={text} />
    </Container>
  );
};

export default Text2LinkWrapper;
