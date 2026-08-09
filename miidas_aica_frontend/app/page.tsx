import { redirect } from "next/navigation";
import { PagePath } from "@/constants/enum";

export default function Home() {
  // LPは不要なのでchatにリダイレクト
  redirect(PagePath.Chat);
}
