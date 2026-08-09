import { type MouseEventHandler, type ReactNode } from "react";

/**
 * 文字列中に含まれる改行コードをbr要素に置換する
 */
export function nl2br(str: string): string | ReactNode[] {
  if (!str) {
    return str;
  }
  const regex = /(\n)/g;
  let count = 0;
  return str.split(regex).map((line) => {
    if (line.match(regex)) {
      count += 1;
      return <br key={`br-${count}`} />;
    }
    return line;
  });
}

/**
 * 文字列中に含まれる[[ ]]をstrong要素に置換する
 * 部分強調色を、BE側で [[ ]] で囲ってFE側で変換（BE側でhtmlタグを扱うのを回避）
 * 例
 * input: '[[現職または前職]]の\n[[休日]]について[[教えてください]]'
 * output: ['', <strong>現職または前職</strong>, 'の\n', <strong>休日</strong>, 'について', <strong>教えてください</strong>, '']
 */
export function squareBracket2Strong(
  value: ReactNode | ReactNode[] | string,
): ReactNode | ReactNode[] | string {
  if (Array.isArray(value)) {
    return value.map((v: ReactNode) => {
      return squareBracket2Strong(v);
    });
  }
  if (typeof value === "string") {
    // 閉じ忘れなど考慮して、両方揃っている場合のみ変換する。
    if (!value.includes("[[") || !value.includes("]]")) {
      return value;
    }
    const regex = /(\[\[.*?\]\])/; // [[hoge]]とマッチさせるため
    const regex2 = /\[\[(.*?)\]\]/; // [[hoge]]からhogeを取り出すため
    let count = 0;
    return value.split(regex).map((line) => {
      const result = line.match(regex2);
      if (result?.[0] && result?.[1]) {
        count += 1;
        return <strong key={`strong-${count}`}>{result[1]}</strong>;
      }
      return line;
    });
  }
  return value;
}

/**
 * value が [string](url) を含むかどうかを正規表現で判定し、true だった場合、<a href="url">string</a> の形の node を作成し返す。
 * 環境変数によってドメインを変える。
 * Note: valueに複数の [string](url) にマッチする文字列があった場合は最初の1つめしか変換されません。
 */
function createNodeIfMatchedRegex(value: ReactNode) {
  const regex = {
    markdown: /\[\S+\]\(https?:\/\/[a-zA-Z0-9!-/:-@¥[-`{-~]*\)/,
    domain: /^https?:\/\/miidas.jp/,
  };
  const stringifiedValue = String(value);

  if (!regex.markdown.test(stringifiedValue)) return value;

  const getMatchedIndex = (v: string, r: RegExp) => {
    const match = v.match(r);
    return match?.index ?? -1;
  };

  const switchDomainByEnv = (url: string) => {
    // 本番環境ではない場合、URLドメインを環境に合わせて変更する
    if (
      regex.domain.test(url) &&
      process.env.NEXT_PUBLIC_HOSTNAME !== "miidas.jp"
    ) {
      return url.replace(
        "miidas.jp",
        process.env.NEXT_PUBLIC_HOSTNAME ?? "local.miidas.jp",
      );
    }
    return url;
  };

  const targetTextStartIndex = getMatchedIndex(stringifiedValue, /\[/);
  const targetTextEndIndex = getMatchedIndex(stringifiedValue, /\]/);
  const urlStartIndex = getMatchedIndex(stringifiedValue, /\(/);
  const urlEndIndex = getMatchedIndex(stringifiedValue, /\)/);

  const targetText = stringifiedValue.slice(
    targetTextStartIndex + 1,
    targetTextEndIndex,
  );
  const url = stringifiedValue.slice(urlStartIndex + 1, urlEndIndex);
  const urlToUse = switchDomainByEnv(url);
  const beforeText = stringifiedValue.slice(0, targetTextStartIndex);
  const afterText = stringifiedValue.slice(
    urlEndIndex + 1,
    stringifiedValue.length,
  );

  return (
    <span key={urlToUse}>
      {beforeText}
      <a href={urlToUse} target="_blank" rel="noopener noreferrer">
        {targetText}
      </a>
      {afterText}
    </span>
  );
}

/**
 * 引数を受け取り createNodeIfMatchedRegex を実行する
 */
export function convertToLink(
  value: ReactNode | ReactNode[],
): ReactNode | ReactNode[] {
  if (Array.isArray(value)) {
    // value が配列の場合は再帰処理
    return value.map((v: ReactNode) => {
      return convertToLink(v);
    });
  }

  return createNodeIfMatchedRegex(value);
}

/**
 * 正規表現にマッチする部分文字列をa要素に置換する
 */
/* eslint no-cond-assign: 0 */
function regexpmatch2link(
  value: string,
  regex: RegExp,
  linkPrefix: string = "",
  onClick?: MouseEventHandler<HTMLAnchorElement>,
) {
  let result: RegExpExecArray | null;
  let indexStart = 0;
  const array: ReactNode[] = [];

  while ((result = regex.exec(value)) !== null) {
    const link = result[0].trim();

    const leadingText = value.substring(indexStart, result.index);
    if (leadingText !== "") {
      array.push(leadingText);
    }

    // decodeできる場合はリンクにする
    let linkNode: ReactNode;
    try {
      linkNode = (
        <a
          key={`${linkPrefix}${link}`}
          href={`${linkPrefix}${link}`}
          target="_blank"
          rel="noopener noreferrer"
          onClick={onClick}
        >
          {decodeURIComponent(link)}
        </a>
      );
    } catch {
      linkNode = link;
    }
    array.push(linkNode);

    indexStart = regex.lastIndex;
  }

  const trailingText = value.substring(indexStart);
  if (trailingText !== "") {
    array.push(trailingText);
  }

  return array;
}

/**
 * 文字列中に含まれるURLをa要素に置換する
 */
export function url2link(
  value: ReactNode | ReactNode[],
  onClick?: MouseEventHandler<HTMLAnchorElement>,
): ReactNode | ReactNode[] {
  if (Array.isArray(value)) {
    // 引数が配列の場合は配列の要素に対して自身を実行
    return value.map((v: ReactNode) => {
      return url2link(v, onClick);
    });
  }

  if (typeof value === "string") {
    // NOTE: 下記正規表現はremark-gfmから流用
    // https://github.com/syntax-tree/mdast-util-gfm-autolink-literal/blob/65d8ac287041b18106ce1c8bfd963c9f55d63324/lib/index.js#L143
    // #69188 末尾に全角スペース(u3000)が含まれる場合はリンクとして認識しないよう処理を追加
    const regex = /(https?:\/\/|www(?=\.))([-.\w]+)([^ \t\r\n\u3000]*)/gi;
    return regexpmatch2link(value, regex, "", onClick);
  }

  return value;
}

/**
 * 文字列中に含まれるメールアドレスをa要素に置換する
 */
export function mail2link(
  value: ReactNode | ReactNode[],
): ReactNode | ReactNode[] {
  if (Array.isArray(value)) {
    // 引数が配列の場合は配列の要素に対して自身を実行
    return value.map((v: ReactNode) => {
      return mail2link(v);
    });
  }

  if (typeof value === "string") {
    // 引数が文字列の場合は文字列中に含まれるメールアドレスを抽出する
    const regex =
      /[a-zA-Z0-9.!#$%&'*+\/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*/g; // eslint-disable-line no-useless-escape
    return regexpmatch2link(value, regex, "mailto:");
  }

  return value;
}

// 対応する電話番号
// 03-1234-5678
// 070-9876-5432
// 0312345678
// 07098765432
// 03 1234 5678
// 090 1234 5678
const phoneRegex = /(0\d{1,4}[-\s]?\d{1,4}[-\s]?\d{4})/g;

/**
 * 文字列中に含まれる電話番号をa要素に置換する
 */
export function phone2link(
  value: ReactNode | ReactNode[],
): ReactNode | ReactNode[] {
  if (Array.isArray(value)) {
    // 引数が配列の場合は配列の要素に対して自身を実行
    return value.map((v: ReactNode) => {
      return phone2link(v);
    });
  }

  if (typeof value === "string") {
    // 引数が文字列の場合は文字列中に含まれる電話番号を抽出する
    return regexpmatch2link(value, phoneRegex, "tel:");
  }

  return value;
}
