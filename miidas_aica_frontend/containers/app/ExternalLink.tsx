import { type ReactNode, type MFC } from "react";
import { useAppActions } from "@/hooks/useAppActions";

type Props = {
  url: string;
  children?: ReactNode;
  className?: string;
};

/**
 * 外部リンクの遷移前に確認モーダルを表示
 * ※ ユーザー入力のURLをリンク化する時に使う
 */
const ExternalLink: MFC<Props> = ({ url, className, children }) => {
  const { showExternalLinkDialog } = useAppActions();

  return (
    <a
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      className={className}
      onClick={showExternalLinkDialog}
    >
      {children}
    </a>
  );
};

export default ExternalLink;
