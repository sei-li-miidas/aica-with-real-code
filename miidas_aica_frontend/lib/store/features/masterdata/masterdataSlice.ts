import { MASTER_KEYS } from "@/constants/master";
import { School, SortedMasterType } from "@/types/utility-types";
import { createSlice, PayloadAction } from "@reduxjs/toolkit";

export interface MasterDataState {
  [MASTER_KEYS.LANG_LEVEL]: SortedMasterType[];
  [MASTER_KEYS.SCHOOL_TYPE]: SortedMasterType[];
  [MASTER_KEYS.SCHOOL]: School[];
  [MASTER_KEYS.DEPARTMENT_TYPE]: SortedMasterType[];
  [MASTER_KEYS.PROFESSIONAL_TRAINING_COLLEGE_CATEGORY]: SortedMasterType[];
}

const initialState: MasterDataState = {
  [MASTER_KEYS.LANG_LEVEL]: [],
  [MASTER_KEYS.SCHOOL_TYPE]: [],
  [MASTER_KEYS.SCHOOL]: [],
  [MASTER_KEYS.DEPARTMENT_TYPE]: [],
  [MASTER_KEYS.PROFESSIONAL_TRAINING_COLLEGE_CATEGORY]: [],
};

const masterdataSlice = createSlice({
  name: "masterdata",
  initialState,
  reducers: {
    setMasterData: <K extends keyof MasterDataState>(
      state: MasterDataState,
      action: PayloadAction<{
        key: K;
        data: MasterDataState[K];
      }>,
    ) => {
      state[action.payload.key] = action.payload.data;
    },
  },
});

export const { setMasterData } = masterdataSlice.actions;
export default masterdataSlice.reducer;
