import Router, { type NextRouter } from "next/router";
import md5 from "md5";
import smoothscroll from "smoothscroll-polyfill";

import { APP_TAB_BAR_INDEX_BY_PATHNAME } from "@/constants/app";
import { BIAS_GAME_EXAM_STATUS } from "@/constants/biasGame/biasGame";
import { type ValuesType } from "@/types/utility-types";
import type Immutable from "immutable";

// eslint-disable-next-line no-use-before-define
if (isClient()) {
  // Smooth Scroll behavior polyfill
  // 対象メソッド一覧：http://iamdustan.com/smoothscroll/
  smoothscroll.polyfill();
}

/**
 * 現在のスクロール位置を取得する
 */
function getCurrentPosition(
  element: HTMLElement | Window,
  direction: "x" | "y" = "y",
) {
  if (direction === "y") {
    return element instanceof Window
      ? window.scrollY || window.pageYOffset
      : element.scrollTop;
  }
  return element instanceof Window
    ? window.scrollX || window.pageXOffset
    : element.scrollLeft;
}

/**
 * 指定されたElementをスクロールする
 */
function elementScrollTo(
  element: HTMLElement | Window,
  targetPosition: number,
  direction: "x" | "y" = "y",
) {
  // 縦にスクロールする
  if (direction === "y") {
    if (element instanceof Window) {
      // windowの場合
      window.scrollTo(window.scrollX || window.pageXOffset, targetPosition);
    } else {
      // その他の要素の場合
      element.scrollTop = targetPosition;
    }
  }

  // 横にスクロールする
  if (element instanceof Window) {
    // windowの場合
    window.scrollTo(targetPosition, window.scrollY || window.pageYOffset);
  } else {
    // その他の要素の場合
    element.scrollLeft = targetPosition;
  }
}

/**
 * スムーズなスクロール、Promiseを返す
 * 第4引数(easing)を指定しない場合は、easeOutをデフォルト値として採用する
 */
export function smoothScrollTo(
  element: HTMLElement | Window,
  endPoint: number,
  duration: number,
  easing?: "smoothStep" | "easeIn" | "easeOut" | "easeInOut" | "linear",
  direction: "x" | "y" = "y",
) {
  const roundEndPoint = Math.round(endPoint);
  const roundDuration = Math.round(duration);
  if (roundDuration < 0) {
    return Promise.reject(
      new Error("durationをポジティブな数字にしてください"),
    );
  }
  // durationが0ので、直接にジャンプ
  if (roundDuration === 0) {
    elementScrollTo(element, roundEndPoint, direction);
    return Promise.resolve();
  }
  const startTime = Date.now();
  const endTime = startTime + roundDuration;
  const startPosition = getCurrentPosition(element, direction);
  const distance = roundEndPoint - startPosition;
  /* eslint-disable func-names, no-shadow */
  const step = function (
    start: number,
    end: number,
    point: number,
    easing?: "smoothStep" | "easeIn" | "easeOut" | "easeInOut" | "linear",
  ) {
    if (point <= start) {
      return 0;
    }
    if (point >= end) {
      return 1;
    }
    let x = (point - start) / (end - start); // 内挿
    /* eslint-disable no-mixed-operators, no-plusplus */
    switch (easing) {
      case "smoothStep":
        return x * x * (3 - 2 * x);
      case "easeIn":
        return x * x * x * x * x;
      case "easeOut":
        return 1 + --x * x * x * x * x;
      case "easeInOut":
        return x < 0.5 ? 16 * x * x * x * x * x : 1 + 16 * --x * x * x * x * x;
      case "linear":
        return x;
      default:
        return 1 + --x * x * x * x * x;
    }
    /* eslint-enable no-mixed-operators, no-plusplus */
  };
  /* eslint-enable func-names, no-shadow */
  return new Promise<void>((resolve) => {
    // 一フレームをスクロールする
    /* eslint-disable func-names */
    const scrollFrame = function () {
      // このフレームのscrollTopを設定する
      const now = Date.now();
      const point = step(startTime, endTime, now, easing);
      const framePosition = Math.round(startPosition + distance * point);
      elementScrollTo(element, framePosition, direction);
      // 完了しているかのチェック
      if (now >= endTime) {
        resolve();
        return;
      }
      // 次のフレームをスケジュールする
      setTimeout(scrollFrame, 0);
    };
    /* eslint-enable func-names */
    // animation処理をブートストラップ
    setTimeout(scrollFrame, 0);
  });
}

/**
 * 待機タイマー関数
 * async、awaitで非同期制御する際に利用できます。
 * 以下、使用例
 *
 * // 非同期処理を制御
 * (async () => {
 *   // 表示待機
 *   await wait(1000); //ここで１秒待機
 *   dispatch({ type : types.APP_NOTICE_HIDE }); //このdispatchは上の1秒経過した後に叩かれる。
 *   await wait(2000); //ここで2秒待機
 *   callBack && callBack(); //ここのコールバックも上の2秒経過した後に叩かれる。
 *   await(); //引数を省略すると１秒待機します。
 *   alert('end');
 * })();
 *
 */
export function wait(millisecond: number = 1000) {
  return new Promise<void>((resolve) => {
    setTimeout(() => {
      resolve();
    }, millisecond);
  });
}

/**
 * 文字列のハッシュ値を返す
 */
export function getHash(str: string) {
  return md5(str);
}

/**
 * router.pathname だと /xxx/[xxxId] のようなパスになるため、意図しないパスになることがある。
 * それを避けるために /xxx/123 を取るためのfunction。
 * @param router next/router
 * @returns dynamic routeでもparamが入っているパス
 */
export function getRealPathname(router: NextRouter) {
  return new URL(router.asPath, `https://${process.env.NEXT_PUBLIC_HOSTNAME}`)
    .pathname;
}

/**
 * /xxx/yyy?zzz=123 のようなURLから /xxx/yyy を取得する
 */
export function getPathnameByUrl(url: string) {
  if (url.match(/\?.*/)) {
    return url.replace(/\?.*/, "");
  }
  return url;
}

/**
 * パスの文字列から/trashedを除去する
 */
export function removeTrashedFromPath(path: string) {
  if (path.match(/\/trashed/)) {
    return path.replace(/\/trashed/, "");
  }
  return path;
}

/**
 * 複数のselectの項目をお互いにフィルターする
 */
export function filterMultiSelectOptions<T extends Record<"ID", unknown>>(
  options: T[],
  selectedValues: Immutable.List<number>,
  includeValue: unknown,
) {
  return options.filter((option) => {
    if (option.ID === includeValue) {
      // 除外しない値ので、フィルターしない
      return true;
    }
    // もう選択された値をフィルターする
    return selectedValues.every((v) => {
      return v !== option.ID;
    });
  });
}

/**
 * 指定文字数より多い文字を切り捨てして返す
 */
export function getOmittedString(
  str: string,
  max: number,
  ellipsis: string = "…",
) {
  if (str.length >= max) {
    return `${str.substring(0, max - 1)}${ellipsis}`;
  }
  return str;
}

/**
 * 配列に0以上の整数以外の値をフィルタする
 */
export function filterNonPositiveIntegers(values: number[] = []) {
  return values.filter((v) => {
    return (
      v &&
      isFinite(v) && // eslint-disable-line no-restricted-globals
      Math.floor(v) === v &&
      v > 0
    );
  });
}

/**
 * バージョン番号を比較する。返す値が下です。
 * a. v1 > v2の場合は1を返す
 * b. v1 < v2の場合は-1を返す
 * c. v1 = v2の場合は0を返す
 */
export function compareVersionNumbers(v1: string, v2: string) {
  const v1Parts = v1.split(".");
  const v2Parts = v2.split(".");

  const isValidPart = (x: string) => {
    return /^\d+$/.test(x);
  };

  if (!v1Parts.every(isValidPart) || !v2Parts.every(isValidPart)) {
    return NaN;
  }

  while (v1Parts.length < v2Parts.length) v1Parts.push("0");
  while (v2Parts.length < v1Parts.length) v2Parts.push("0");

  const numberedV1Parts = v1Parts.map(Number);
  const numberedV2Parts = v2Parts.map(Number);

  for (let i = 0; i < numberedV1Parts.length; i++) {
    if (numberedV1Parts[i] !== numberedV2Parts[i]) {
      if (numberedV1Parts[i] > numberedV2Parts[i]) {
        return 1;
      }
      return -1;
    }
  }

  return 0;
}

/**
 * span時間の間隔でstart時間からcount個の時間一覧を取得する
 * (1, 0, 2) => ['0時間', '1時間']
 */
export const getHourDurationList = (
  span: number,
  start: number,
  count: number,
) => {
  return Array.from({ length: count }, (_, i) => {
    return {
      // 分単位での値設定
      ID: `${start * 60 + i * 60 * span}`,
      // 時間単位で表示
      Name: `${start + i * span}時間`,
    };
  });
};

/**
 * 関数のコール回数を制限する
 */
export function debounce<Args extends unknown[]>(
  fn: (...args: Args) => void,
  delay: number,
): [(...args: Args) => void, () => void] {
  let timeout: NodeJS.Timeout | undefined;

  function start(...args: Args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => {
      fn(...args);
    }, delay);
  }

  function cancel() {
    clearTimeout(timeout);
  }

  return [start, cancel];
}

/**
 * 開始終了処理の有る関数のコール回数を制限する
 */
export function startEndDebounce<Args extends unknown[]>(
  sfn: (...args: Args) => void,
  efn: (...args: Args) => void,
  delay: number,
) {
  let timeout: NodeJS.Timeout | undefined;

  return (...args: Args) => {
    const later = () => {
      timeout = undefined;
      efn(...args);
    };
    const callNow = !timeout;
    clearTimeout(timeout);
    timeout = setTimeout(later, delay);
    if (callNow) sfn(...args);
  };
}

/**
 * なりすましログイン時にtrueを返す
 */
export function isRefLoggedin() {
  const host = window.location.hostname;
  if (host.indexOf("ref") === -1) {
    return false;
  }
  return true;
}

/**
 * isServer
 * サーバでの実行かチェックする関数
 */
export function isServer() {
  return typeof window === "undefined";
}

/**
 * isClient
 * クライアントでの実行かチェックする関数
 */
export function isClient() {
  return !isServer();
}

/**
 * REPからのアクセスかチェックする
 */
export function isRep() {
  return /(?=.*rep)(?=.*miidas)/.test(document.referrer);
}

/**
 * 404ページにリダイレクトする
 */
export function gotoNotFound() {
  Router.replace("/404", Router.asPath);
}

/**
 * 指定DOMアイテムの実際の高さを取得する
 */
export function getElementHeight(elementRef: HTMLElement | null) {
  // 引数が無効の場合は0を返す
  if (!elementRef) {
    return 0;
  }

  const cssStyle = getComputedStyle(elementRef);
  const marginTop = parseInt(cssStyle.marginTop, 10);
  const marginBottom = parseInt(cssStyle.marginBottom, 10);

  return elementRef.offsetHeight + marginTop + marginBottom;
}

/**
 * indexで指定されたReactListアイテムの高さを返す
 * 高さ可変なReactList（type="variable"）の場合はこのメソッドを利用する
 */
export function getReactListItemHeightFromCache(
  index: number,
  itemHeightCacheImtMap: Immutable.Map<number, number>,
  heightWhenNoCache: number,
) {
  // キャッシュ値があれば、それを返す
  const cache = itemHeightCacheImtMap.get(index);
  if (cache) {
    return cache;
  }

  if (itemHeightCacheImtMap.size) {
    // キャッシュされた高さの配列の合計を取得
    const totalHeight = itemHeightCacheImtMap.reduce((currentTotal, value) => {
      return currentTotal + value;
    }, 0);

    // 平均高さを返す
    return Math.floor(totalHeight / itemHeightCacheImtMap.size);
  }

  // 情報が最低限の場合のミニマム値:iphone5でコンテンツ一番少ない場合に取得した高さ
  return heightWhenNoCache;
}

/*
 * 月の配列を返す。引数で「今年」が渡ってきたら今月までの配列を返す
 */
export function getMonthsUntilThisMonth(year: number) {
  const d = new Date();
  const thisYear = d.getFullYear();
  const thisMonths = d.getMonth() + 1;
  const months = [];
  // 今年の場合は「今月」まで、それ以外は12ヶ月の配列を作成
  const month = thisYear === year ? thisMonths : 12;
  for (let i = 1; i <= month; i++) {
    months.push({
      ID: i,
      Name: i,
    });
  }
  return months;
}

/**
 * 在職期間の開始年範囲を取得する
 */
export function getJoinTermFromYearOptions<T extends Record<"ID", number>>(
  yearOptions: T[],
  toYear: number | null,
) {
  if (!toYear) {
    return yearOptions;
  }
  const firstYear = yearOptions[0].ID;
  return yearOptions.slice(0, toYear - firstYear + 1);
}

/**
 * 在職期間の退職年範囲を取得する
 */
export function getJoinTermToYearOptions<T extends Record<"ID", number>>(
  yearOptions: T[],
  fromYear: number | null,
) {
  if (!fromYear) {
    return yearOptions;
  }
  const firstYear = yearOptions[0].ID;
  return yearOptions.slice(fromYear - firstYear);
}

/**
 * 年数の差分を取得
 * @param from 入社日
 * @param to 退職日
 * @param isGapAcceptable 1ヶ月のズレを許容するかのフラグ
 */
export function getDiffYears(
  from: Date | null,
  to: Date | null,
  isGapAcceptable: boolean = true,
) {
  const dateFrom = from || new Date();
  const dateTo = to || new Date();

  let startYear = dateFrom.getFullYear();
  let startMonth = dateFrom.getMonth();
  let endYear = dateTo.getFullYear();
  let endMonth = dateTo.getMonth();

  if (startYear === endYear && startMonth === endMonth) {
    // 年月が一致する場合は、計算せずに0をリターン
    return 0;
  }
  if ((startYear === endYear && startMonth > endMonth) || startYear > endYear) {
    // fromの年月とtoの年月が逆の場合は入れ替えを行う
    [startYear, endYear] = [endYear, startYear];
    [startMonth, endMonth] = [endMonth, startMonth];
  }

  // 一ヶ月のズレを許容するかどうか
  const oneMonthGap = isGapAcceptable ? 1 : 0;

  // 2020.1  - 2021.6  => (2021 - 2020) + (6  -  1 + 1) / 12 = 0.5
  // 2020.12 - 2021.6  => (2021 - 2020) + (6  - 12 + 1) / 12 = 0.583
  // 2020.12 - 2021.11 => (2021 - 2020) + (11 - 12 + 1) / 12 = 1.0
  // 2020.1  - 2022.12 => (2022 - 2020) + (12 -  1 + 1) / 12 = 3.0
  return endYear - startYear + (endMonth - startMonth + oneMonthGap) / 12;
}

/**
 * 画面最上部に表示されているバリデーションエラー入力項目にスクロールする
 * @param validErrorKeys バリデーションエラーの入力項目名一覧
 */
export function scrollToTopValidErrorField(
  validErrorKeys: string[],
  currentDomBaseClassName: string,
  offsetTop?: number,
) {
  // 画面最上部に表示されているバリデーションエラー入力項目DOMを取得
  const topDisplayedElm = validErrorKeys.reduce<HTMLElement | null>(
    (dom, errorKey) => {
      // eslint-disable-next-line @typescript-eslint/consistent-type-assertions
      const currentDoms = document.getElementsByClassName(
        `${currentDomBaseClassName}${errorKey}`,
      ) as HTMLCollectionOf<HTMLElement>;

      if (!currentDoms.length) return dom;
      const currentDom = currentDoms[0];

      // 初期値
      if (!dom) return currentDom;
      // 高い位置にあるdomを返す
      return dom.offsetTop < currentDom.offsetTop ? dom : currentDom;
    },
    null,
  );

  // DOMが取得出来なかった場合には何もしない(バリデーションエラーキー名と一致しない場合などのフェイルセーフ)
  if (!topDisplayedElm) return;

  // スクロール
  // (バリデーションエラー項目 - ヘッダー高さ) - 50px
  const pos = offsetTop || topDisplayedElm.offsetTop - 56 - 55;
  smoothScrollTo(window, pos, 500, "easeInOut");
}

/**
 * 前画面に戻れるかを返す
 * 新旧システム間の画面遷移に戻るボタンの表示判断で使う
 */
export function canBackToPreviousPage(isDirectAccess: boolean) {
  // TODO:旧user側の企業検索機能が削除されたら、referrerを見ないように修正する（isDirectAccessがtrueの場合のみfalseを返す）

  // 直接アクセスでない（論理遷移）場合、trueを返す
  if (!isDirectAccess) return true;

  // 前画面（document.referrer）がない場合（戻り先がないため）、falseを返す
  if (!document.referrer) return false;

  // 前画面（document.referrer）が違うドメインの場合（他サイトに戻ってしまうことを防ぐため）、falseを返す
  if (!document.referrer.startsWith(window.location.origin)) return false;

  // 前画面（document.referrer）は今画面と同じURLの場合（戻っても画面が変わらないことを防ぐため）、falseを返す
  if (document.referrer === window.location.href) return false;

  // 前画面（document.referrer）がログイン画面の場合（ログイン画面に戻ってしまうことを防ぐため）、falseを返す
  if (/\/login\/?$/.test(document.referrer)) return false;

  // 上記以外の場合、falseを返す
  return false;
}

/**
 * resetTextIfNeeded
 * 空文字(スペース、タブ)のみなど無効な入力値の場合にリセットする
 */
export function resetTextIfNeeded(value: string) {
  if (value?.trim() === "") {
    return "";
  }
  return value;
}

/**
 * 関数のコール回数を制限する
 * 何回に呼ばれても、指定の間隔時間に関数の実行回数を１回だけにする
 * スクロールのイベントハンドラーなどで使用される想定である
 */
export function throttle<Args extends unknown[]>(
  fn: (...args: Args) => void,
  interval: number,
): [(...args: Args) => void, () => void] {
  let timerId: NodeJS.Timeout | undefined;
  let lastExecTime = 0;

  function start(...args: Args) {
    const currentTime = Date.now();

    const execute = () => {
      fn(...args);
      lastExecTime = Date.now();
    };

    // 念の為、タイマーをクリア（時間になってもtimerが実行されていない場合があるため）
    clearTimeout(timerId);

    if (lastExecTime + interval <= currentTime) {
      // 前回の実行より指定の間隔時間を経ったら、関数を実行
      execute();
    } else {
      // 前回の実行より指定の間隔時間を経ってなければ、タイマーを登録
      const newInterval = lastExecTime + interval - currentTime;
      timerId = setTimeout(execute, newInterval);
    }
  }

  function clear() {
    clearTimeout(timerId);
  }

  return [start, clear];
}

/**
 * 文字をひらがなタイプからカタカナに変換します
 */
export function convertHiraganaToKatakana(str: string) {
  if (typeof str === "string") {
    // ぁ-ん、ゔ、ゕ、ゖ
    return str.replace(/[\u3041-\u3096]/g, (s) => {
      return String.fromCharCode(s.charCodeAt(0) + 0x60);
    });
  }
  return str;
}

/**
 * 文字列をキャメルケースからスネークケースに変換する
 */
export function convertCamelCaseToSnake(str: string) {
  return str
    .split(/(?=[A-Z])/)
    .join("_")
    .toLowerCase();
}

/**
 * 数字を文字列に変換する
 * 卒業年のような数字型の値をinputに設定する時使うと想定する。
 *
 * 下記のルールで引数の該当文字列を返す
 *   0の場合：'0'
 *   nullまたundefinedの場合：''
 *   上記以外の数字nの場合：'{n}'
 */
export function convertNumToString(num?: number | null) {
  if (num === 0) {
    return String(num);
  }
  return String(num || "");
}

/**
 * 文字数をカウントする
 */
export function getTextCount(str: string) {
  // 見た目上の文字数と乖離する可能性があるが、DBに保存される時のバイト数に合わせて.lengthでカウント(#68758参考)
  return str.length;
}

/**
 * 開発用隠しステータス ABTestDebug でユーザーを切り替える
 */
export function getABTestDebugId(testPatterns: unknown[]) {
  const regex = /[?&]ABTestDebug=([^&#]*)/;
  const query = window.location.search;
  const queryParam = query.match(regex);

  // 値がない、異常値ならスルー
  if (queryParam === null || Number(queryParam[1]) > testPatterns.length - 1) {
    return null;
  }

  return Number(queryParam[1]);
}

type ABTestPatternOptions = {
  userId?: number | null;
  isDisable?: boolean;
  isTargetDevice?: boolean;
};

/**
 * ABテストの表示や処理をユーザーIDによって振り分ける
 */
export function getABTestPattern<T>(
  { userId, isDisable = false, isTargetDevice = true }: ABTestPatternOptions,
  ...testPatterns: T[]
) {
  // ABテスト対象がなければ即時return
  if (!testPatterns) return null;
  // ABテスト対象が2つ以上なければ即時return
  if (testPatterns.length && testPatterns.length <= 1) return null;
  // userIdがない場合、ABテスト対象の1つ目を返す
  if (!userId) return testPatterns[0];
  // 明示的に無効にされている場合、ABテスト対象の1つ目を返す
  if (isDisable) return testPatterns[0];
  // 対象デバイスではない場合、ABテスト対象の1つ目を返す
  if (!isTargetDevice) return testPatterns[0];

  const debugId = getABTestDebugId(testPatterns);
  const userType = debugId !== null ? debugId : userId % testPatterns.length;
  return testPatterns[userType];
}

type BiasGameExamStatus = ValuesType<typeof BIAS_GAME_EXAM_STATUS>;

/**
 * バイアス診断ゲームの受験状況を取得する
 */
export function getExamLabel(biasGameExamStatus: BiasGameExamStatus) {
  switch (biasGameExamStatus) {
    case BIAS_GAME_EXAM_STATUS.FINISHED:
      return "受験済み";
    case BIAS_GAME_EXAM_STATUS.IN_PROGRESS:
      return "受験中";
    default:
      return "未受験";
  }
}

type AppTabBarPathName = keyof typeof APP_TAB_BAR_INDEX_BY_PATHNAME;

/**
 * アプリでタブバーのタブの移動先インデックスを取得する
 */
export const getAppMoveToTabBarIndex = (pathname: AppTabBarPathName) => {
  return APP_TAB_BAR_INDEX_BY_PATHNAME[pathname];
};

/**
 * アプリでタブバーのタブを移動するかどうか
 * @returns true: 移動する, false: 移動しない
 */
export const shouldAppMoveToTabBarIndex = (
  nextPathname: AppTabBarPathName,
  referencedAppTapIndex: number,
) => {
  const nextReferencedAppTapIndex = getAppMoveToTabBarIndex(nextPathname);
  if (nextReferencedAppTapIndex === undefined) {
    // タブバーのタブを移動する必要がない場合は、タブバーの移動不要
    return false;
  }
  // 既に次の遷移先のタブで開かれている場合は、タブバーの移動不要
  // NOTE: この判定がないと、/wish -> /offer/employeeへの遷移でタブバー移動扱いになり検索条件の変更が適応されない
  return nextReferencedAppTapIndex !== referencedAppTapIndex;
};

/**
 * 引数の文字列をクリップボードにコピーする
 */
export const copyToClipboard = (str: string) => {
  // クリップボードコピー用に一時的に要素を作成
  const tmpEl = document.createElement("textarea");
  tmpEl.value = str;
  document.body.appendChild(tmpEl);
  tmpEl.select();
  // コピーが成功したらtrue、失敗したらfalseが入る
  const result = document.execCommand("copy");
  // 一時的に作成した要素が見えないようにdisplay:noneをセット
  tmpEl.style.display = "none";
  // クリップボードコピー用に作成した要素を削除
  document.body.removeChild(tmpEl);
  return result;
};
