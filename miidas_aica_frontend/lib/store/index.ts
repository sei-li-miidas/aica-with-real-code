import { Action, configureStore, ThunkAction } from "@reduxjs/toolkit";
import globalStateReducer from "./features/global_state/globalStateSlice";
import masterdataReducer from "./features/masterdata/masterdataSlice";
import profileReducer from "./features/profile/profileSlice";
import positionSearchReducer from "./features/position_search/positionSearchSlice";
import websocketReducer from "./features/websocket/websocketSlice";

export const makeStore = () => {
  return configureStore({
    reducer: {
      websocket: websocketReducer,
      globalState: globalStateReducer,
      profile: profileReducer,
      masterdata: masterdataReducer,
      positionSearch: positionSearchReducer,
    },
  });
};

export const store = makeStore();

// Infer the type of makeStore
export type AppStore = ReturnType<typeof makeStore>;
// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<AppStore["getState"]>;
export type AppDispatch = AppStore["dispatch"];

export type AppThunk<ReturnType = void> = ThunkAction<
  ReturnType,
  RootState,
  unknown,
  Action<string>
>;
