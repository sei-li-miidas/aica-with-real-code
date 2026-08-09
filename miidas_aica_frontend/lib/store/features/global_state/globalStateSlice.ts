import { AppThunk } from "@/lib/store";
import { AGREEMENT_KEY } from "@/constants/localStorage";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface GlobalState {
  initToastClosed: boolean;
  positionDetailChatSpeechBubbleClosed: boolean;
  // ユーザーがどのポジションの「詳細をみる」をクリックしたかを記録する。
  positionItemKey: string | null;
  // ユーザーが利用規約に同意したかどうか
  hasAgreedToTermsOfUse: boolean;
}

const initialState: GlobalState = {
  initToastClosed: false,
  positionItemKey: null,
  positionDetailChatSpeechBubbleClosed: false,
  hasAgreedToTermsOfUse: false,
};

const globalStateSlice = createSlice({
  name: "globalState",
  initialState,
  reducers: {
    closeInitToast: (state) => {
      state.initToastClosed = true;
    },
    registerPositionItemKey: (state, action: PayloadAction<string>) => {
      state.positionItemKey = action.payload;
    },
    closePositionDetailChatSpeechBubble: (state) => {
      state.positionDetailChatSpeechBubbleClosed = true;
    },
    agreeToTermsOfUse: (state) => {
      state.hasAgreedToTermsOfUse = true;
    },
  },
});

export const saveTermsOfUseAgreement = (): AppThunk => (dispatch) => {
  console.log("saveTermsOfUseAgreement called");
  localStorage.setItem(AGREEMENT_KEY, "1");
  dispatch(globalStateSlice.actions.agreeToTermsOfUse());
};

export const {
  closeInitToast,
  registerPositionItemKey,
  closePositionDetailChatSpeechBubble,
  agreeToTermsOfUse,
} = globalStateSlice.actions;
export default globalStateSlice.reducer;
