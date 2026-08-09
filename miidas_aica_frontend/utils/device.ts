import { type IncomingMessage } from "http";

/**
 * ユーザエージェントを取得する
 */
export function getUserAgent(req?: IncomingMessage) {
  // クライアントサイドの場合
  if (typeof window !== "undefined") {
    return window.navigator.userAgent;
  }
  // サーバーサイドの場合
  return req?.headers["user-agent"] ?? "";
}

/**
 * Appのバージョンを取得する
 * @returns {Array<Number>} ex. [5, 0, 1]
 */
export function getAppVersion(req?: IncomingMessage) {
  return getUserAgent(req)
    .replace(/(miidas_android|miidas_ios)\//, "")
    .split(".")
    .map((v) => Number(v));
}

/**
 * Appのバージョンを取得する
 * @returns {String} ex. 5.0.1
 */
export function getAppVersionV2(req?: IncomingMessage) {
  // miidas_ios/5.0.1/17.0.1 または miidas_android/5.0.1 から 5.0.1 を取得する
  return getUserAgent(req)
    .replace(/(miidas_android|miidas_ios)\//, "")
    .split("/")[0];
}

/**
 * iOSアプリであるかどうかを判定する
 */
export function isIosApp(req?: IncomingMessage) {
  return !!getUserAgent(req)?.includes("miidas_ios");
}

/**
 * Androidアプリであるかどうかを判定する
 */
export function isAndroidApp(req?: IncomingMessage) {
  return !!getUserAgent(req)?.includes("miidas_android");
}

/**
 * アプリであるかどうかを判定する
 */
export function isApp(req?: IncomingMessage) {
  return isIosApp(req) || isAndroidApp(req);
}

/**
 * WEBであるかどうかを判定する
 */
export function isWeb(req?: IncomingMessage) {
  return !isApp(req);
}

/**
 * スマホであるかどうかを判定する
 */
export function isSmartphone(req?: IncomingMessage) {
  return (
    isApp(req) ||
    !!getUserAgent(req)
      ?.toLowerCase()
      .match(/iphone|ipad|ipod|android|mobile/)
  );
}

/**
 * パソコンであるかどうかを判定する
 */
export function isPC(req?: IncomingMessage) {
  return !isSmartphone(req);
}

/**
 * デバイスの画面サイズの閾値。数値ははcssの$breakPointを参照
 * NOTE: LPは閾値別なので注意
 */
const DEVICE_BREAK_POINT = {
  PC: 1024,
} as const;

/**
 * window.innerWidthを用いてSP用デザインかどうかを取得する
 */
export function isSmartphoneSize() {
  return window.innerWidth < DEVICE_BREAK_POINT.PC;
}

/**
 * window.innerWidthを用いてPC用デザインかどうかを取得する
 */
export function isPCSize() {
  return !isSmartphoneSize();
}

/**
 * Androidデバイスであるかどうかを判定する
 */
export function isAndroidDevice(req?: IncomingMessage) {
  return (
    !!getUserAgent(req)?.toLowerCase().includes("android") || isAndroidApp()
  );
}

/**
 * iOSデバイスであるかどうかを判定する
 */
export function isIosDevice(req?: IncomingMessage) {
  return (
    !!getUserAgent(req)
      ?.toLowerCase()
      .match(/iphone|ipad|ipod/) || isIosApp()
  );
}

export const OS = {
  WINDOW_PHONE: "Windows Phone",
  WINDOW: "Windows",
  IOS: "iOS",
  ANDROID: "Android",
  MAC: "Macintosh",
  LINUX: "Linux",
  FIREFOX_OS: "Firefox OS",
  DEFAULT: "Unknown",
} as const;

export const BROWSER_NAME = {
  IE: "Internet Explorer",
  EDGE: "Edge",
  OPERA: "Opera",
  FIREFOX: "Firefox",
  CHROME: "Chrome",
  SAFARI: "Safari",
  YAHOO: "Yahoo",
  KAITO: "Kaito",
  LINE: "Line",
  IOS_APP: "iOS App",
  ANDROID_APP: "Android App",
  DEFAULT: "Unknown",
} as const;

/**
 * UAからOSとブラウザの情報を取得
 */
/* eslint-disable no-useless-escape */
export function getPlatform(req?: IncomingMessage) {
  const ua = getUserAgent(req)?.toLowerCase() || "";
  let matches;
  const result = {
    browser: {
      name: "",
      version: "",
    },
    os: {
      name: "",
      version: "",
    },
    isIE: false,
    isEdge: false,
    isFirefox: false,
    isSafari: false,
    isChrome: false,
    isOpera: false,
    isYahoo: false,
    isKaito: false,
    isLine: false,
    isIosApp: false,
    isAndroidApp: false,
    isSmartphone: false,
  };

  // ブラウザ名とバージョン
  switch (true) {
    case / line\//.test(ua): // LINEブラウザを判定
      result.browser.name = BROWSER_NAME.LINE;
      result.isLine = true;
      break;
    case ua.includes("miidas_ios"):
      result.browser.name = BROWSER_NAME.IOS_APP;
      result.isIosApp = true;
      result.isSmartphone = true;
      break;
    case ua.includes("miidas_android"):
      result.browser.name = BROWSER_NAME.ANDROID_APP;
      result.isAndroidApp = true;
      result.isSmartphone = true;
      break;
    case /iphone|ipad|ipod/.test(ua):
      // --------------
      // iOS
      // --------------
      if (/chrome|crios/.test(ua)) {
        result.browser.name = BROWSER_NAME.CHROME;
        result.isChrome = true;
      } else if (ua.includes("fxios") || ua.includes("firefox")) {
        result.browser.name = BROWSER_NAME.FIREFOX;
        result.isFirefox = true;
      } else if (ua.includes("opera") || ua.includes("opios")) {
        result.browser.name = BROWSER_NAME.OPERA;
        result.isOpera = true;
      } else if (ua.includes("ybrowser")) {
        result.browser.name = BROWSER_NAME.YAHOO;
        result.isYahoo = true;
      } else if (ua.includes("edgios")) {
        result.browser.name = BROWSER_NAME.EDGE;
        result.isEdge = true;
      } else if (ua.includes("kaito")) {
        result.browser.name = BROWSER_NAME.KAITO;
        result.isKaito = true;
      } else if (ua.includes("safari")) {
        result.browser.name = BROWSER_NAME.SAFARI;
        result.isSafari = true;
      }
      result.isSmartphone = true;
      break;
    case ua.includes("android") && ua.includes("mobile"):
      // --------------
      // Android
      // --------------
      if (/android/.test(ua) && /linux; u;/.test(ua) && !/chrome/.test(ua)) {
        // アンドロイド標準ブラウザ
      } else if (ua.includes("opera") || ua.includes("opr")) {
        // Opera
        result.browser.name = BROWSER_NAME.OPERA;
        result.isOpera = true;
      } else if (ua.includes("ybrowser")) {
        // Yahooブラウザ
        result.browser.name = BROWSER_NAME.YAHOO;
        result.isYahoo = true;
      } else if (ua.includes("edga")) {
        result.browser.name = BROWSER_NAME.EDGE;
        result.isEdge = true;
      } else if (ua.includes("chrome")) {
        result.browser.name = BROWSER_NAME.CHROME;
        result.isChrome = true;
      }
      result.isSmartphone = true;
      break;
    case /msie|trident/.test(ua):
      result.browser.name = BROWSER_NAME.IE;
      result.isIE = true;
      break;
    case /(edge|edg)\/+/i.test(ua):
      result.browser.name = BROWSER_NAME.EDGE;
      result.isEdge = true;
      break;
    case /opera|opr/.test(ua):
      result.browser.name = BROWSER_NAME.OPERA;
      result.isOpera = true;
      break;
    case /firefox/.test(ua):
      result.browser.name = BROWSER_NAME.FIREFOX;
      result.isFirefox = true;
      break;
    case /chrome/.test(ua):
      result.browser.name = BROWSER_NAME.CHROME;
      result.isChrome = true;
      break;
    case /safari/.test(ua):
      result.browser.name = BROWSER_NAME.SAFARI;
      result.isSafari = true;
      break;
    default:
      result.browser.name = BROWSER_NAME.DEFAULT;
      break;
  }

  if (result.isIE) {
    matches = ua.match(/(msie|rv:?)\s?([\d\.]+)/);
    result.browser.version =
      matches && matches.length > 0 && matches[2] ? matches[2] : "";
  } else if (result.isOpera) {
    if (ua.match(/version\//)) {
      matches = ua.match(/version\/([\d\.]+)/);
      result.browser.version =
        matches && matches.length > 0 && matches[1] ? matches[1] : "";
    } else {
      matches = ua.match(/(opera(\s|\/)|opr\/)([\d\.]+)/);
      result.browser.version =
        matches && matches.length > 0 && matches[3] ? matches[3] : "";
    }
  } else if (
    result.isEdge ||
    result.isFirefox ||
    result.isChrome ||
    result.isSafari
  ) {
    if (result.isEdge) {
      matches = ua.match(/(edg|edge|edgios|edga)\/([\d\.]+)/);
    } else if (result.isFirefox) {
      matches = ua.match(/firefox\/([\d\.]+)/);
    } else if (result.isChrome) {
      matches = ua.match(/chrome\/([\d\.]+)/);
    } else if (result.isSafari) {
      matches = ua.match(/version\/([\d\.]+)/);
    }
    result.browser.version = matches?.slice(-1)[0] || "";
  }

  // OS名とバージョン
  switch (true) {
    case /windows phone/.test(ua):
      result.os.name = OS.WINDOW_PHONE;
      break;
    case /windows/.test(ua):
      result.os.name = OS.WINDOW;
      break;
    case /ios|iphone|ipad|ipod/.test(ua):
      result.os.name = OS.IOS;
      break;
    case /mac os|mac_powerpc|macintosh/.test(ua):
      result.os.name = OS.MAC;
      break;
    case /android/.test(ua):
      result.os.name = OS.ANDROID;
      break;
    case /linux/.test(ua):
      result.os.name = OS.LINUX;
      break;
    case /firefox/.test(ua) || /mobile|tablet/.test(ua):
      result.os.name = OS.FIREFOX_OS;
      break;
    default:
      result.os.name = OS.DEFAULT;
      break;
  }

  if (result.os.name === OS.WINDOW) {
    matches = ua.match(/windows nt ([\d\.]+)/);
    if (matches && matches.length > 0 && matches[1]) {
      if (matches[1].match(/10\.[0-9]/)) {
        result.os.version = matches[1];
      } else if (matches[1] === "6.3") {
        result.os.version = "8.1";
      } else if (matches[1] === "6.2") {
        result.os.version = "8.0";
      } else if (matches[1] === "6.1") {
        result.os.version = "7";
      } else if (matches[1] === "6.0") {
        result.os.version = "Vista";
      } else if (matches[1] === "5.2" || matches[1] === "5.1") {
        result.os.version = "XP";
      } else if (matches[1] === "5.0") {
        result.os.version = "2000";
      }
    }
    matches = ua.match(/windows ([\d]+)/);
    if (matches && matches.length > 0 && matches[1]) {
      if (matches[1] === "98" && ua.match(/9x/)) {
        result.os.version = "Me";
      } else if (matches[1] === "98") {
        result.os.version = "98";
      } else if (matches[1] === "95") {
        result.os.version = "95";
      } else if (matches[1] === "3.1") {
        result.os.version = "3.1";
      }
    }
  } else if (result.os.name === OS.IOS) {
    matches =
      ua.match(/((iphone)? os) ([\d_]+)/) ||
      ua.match(/(miidas_ios\/)?([\d\.].*)\/([\d\.].*)/);
    if (matches && matches.length > 0 && matches[3]) {
      result.os.version = matches[3].replace(/_/g, ".");
    }
  } else if (result.os.name === OS.ANDROID) {
    matches = ua.match(/android ([\d\.]+)/);
    if (matches && matches.length > 0 && matches[1]) {
      result.os.version = matches[1];
    }
  }

  return result;
}
/* eslint-enable no-useless-escape */

/**
 * 画面端でのタッチによる引っ張り操作を無効化したいデバイスかどうかの判定
 */
export function isDisableTouchPullDevice() {
  const result = getPlatform();
  return (
    result.os.name === OS.IOS && Number(result.os.version.split(".")[0]) <= 12
  );
}

/**
 * ブラウザがSafariかどうかを判断する
 */
export function isSafari(req?: IncomingMessage) {
  const ua = getUserAgent(req)?.toLowerCase();
  return !!(ua?.includes("safari") && !ua?.includes("chrome"));
}

/**
 * ブラウザがIE11かどうか判定して返す
 */
export function isIE11(req?: IncomingMessage) {
  const ua = getUserAgent(req)?.toLowerCase();
  return !!ua?.includes("trident");
}

/**
 * SP推奨ブラウザか?
 */
export function isSpRecommendedBrowser() {
  // UAからOSとブラウザの情報を取得
  const result = getPlatform();

  // 下記ブラウザに限定する
  // 1. iOS Safari
  // 2. Android Chrome
  return (
    (result.os.name === OS.IOS && result.isSafari) ||
    (result.os.name === OS.ANDROID && result.isChrome)
  );
}

/**
 * ブラウザがサポート対象かどうか判定
 */
export function isSupportBrowser() {
  // UAからOSとブラウザの情報を取得
  const result = getPlatform();

  // サポートブラウザは、以下6種類に限定する
  // PC Edge、PC Chrome、iOS Safari、Android Chrome、ミイダスiOSアプリ、ミイダスAndroidアプリ
  return (
    (!result.isSmartphone && result.isEdge) ||
    (!result.isSmartphone && result.isChrome) ||
    (result.os.name === OS.IOS && result.isSafari) ||
    (result.os.name === OS.ANDROID && result.isChrome) ||
    result.isIosApp ||
    result.isAndroidApp
  );
}

/**
 * cookieが無効か判定
 */
export function isCookieDisabled() {
  if (!window.navigator.cookieEnabled) return true;

  try {
    // IE対応 navigator.cookieEnabledはtrueだがcookieが無効なケースがあるため
    // TODO: chromeでも navigator.cookieEnabled=true なのにdocument.cookie無効のケースが存在した（applogsの/api/v1/session/log参照。apiは削除済み）ので、その端末が実際ログインできるかの検証をする
    document.cookie = "miidas_user_cookie_check=miidas";
    const isCookieWritable =
      document.cookie.indexOf("miidas_user_cookie_check") !== -1;
    // 一時的な確認なので削除
    document.cookie =
      "miidas_user_cookie_check=miidas; expires=Thu, 01-Jan-1970 00:00:01 GMT";
    return !isCookieWritable;
  } catch {
    // 何もしない
  }

  return true;
}

/**
 * リロードかどうかを判定する
 */
export function isReload() {
  if (!window?.performance?.getEntriesByType) return false;
  // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
  const navigationEntries = window.performance.getEntriesByType(
    "navigation",
  ) as PerformanceNavigationTiming[];
  return !!navigationEntries.length && navigationEntries[0].type === "reload";
}
