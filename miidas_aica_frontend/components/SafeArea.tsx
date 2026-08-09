import "./SafeArea.scss";
import { PropsWithChildren } from "react";
import Box from "@mui/material/Box";
import { useEffect } from "react";
import { useAppDispatch } from "@/lib/store/hooks";
import { AGREEMENT_KEY } from "@/constants/localStorage";
import { saveTermsOfUseAgreement } from "@/lib/store/features/global_state/globalStateSlice";

export default function SafeArea({ children }: PropsWithChildren) {
  const dispatch = useAppDispatch();
  useEffect(() => {
    // 規約同意済みかどうか
    const hasAgreed = window.localStorage.getItem(AGREEMENT_KEY) === "1";
    if (hasAgreed) {
      dispatch(saveTermsOfUseAgreement());
    }
  }, [dispatch]);
  return <Box className="safe-area">{children}</Box>;
}
