// バーチャルキーボードのevent.target
// TypeScriptに存在しないためビルドエラーが発生
export interface VirtualKeyboardEventTarget extends EventTarget {
  readonly boundingRect: DOMRect;
}

// バーチャルキーボードのevent
// TypeScriptに存在しないためビルドエラーが発生
export interface VirtualKeyboardGeometryChangeEvent extends Event {
  readonly target: VirtualKeyboardEventTarget | null;
}

// 1. Define the actual type of the virtualKeyboard object
interface VirtualKeyboard {
  // Add the properties you need to access from it
  readonly boundingRect: DOMRect;
  overlaysContent: boolean;
  // Add the methods you call
  addEventListener(type: "geometrychange", listener: (event: VirtualKeyboardGeometryChangeEvent) => void): void;
  removeEventListener(type: "geometrychange", listener: (event: VirtualKeyboardGeometryChangeEvent) => void): void;
}

// 2. Extend the global Navigator interface
declare global {
  interface Navigator {
    // The property is optional, reflecting the runtime check you are doing
    readonly virtualKeyboard?: VirtualKeyboard;
  }
}
