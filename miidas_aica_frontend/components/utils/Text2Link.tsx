import {
  nl2br as convertNl2br,
  url2link as convertUrl2link,
  phone2link as convertPhone2link,
  mail2link as convertMail2link,
} from "@/utils/jsx";
import { type ReactNode, type MFC, type MouseEventHandler } from "react";

type Props = {
  text: string;
  nl2br?: boolean;
  url2link?: boolean;
  mail2link?: boolean;
  phone2link?: boolean;
  onClick?: MouseEventHandler<HTMLAnchorElement>;
};

/**
 * テキストの中のURLやメールアドレスをリンクに変換する
 */
const Text2Link: MFC<Props> = ({
  text,
  nl2br = true,
  url2link = true,
  mail2link = true,
  phone2link = true,
  onClick,
}) => {
  let converted: ReactNode | ReactNode[] = nl2br ? convertNl2br(text) : text;
  converted = url2link ? convertUrl2link(converted, onClick) : converted;
  converted = phone2link ? convertPhone2link(converted) : converted;
  return <>{mail2link ? convertMail2link(converted) : converted}</>;
};

export default Text2Link;
