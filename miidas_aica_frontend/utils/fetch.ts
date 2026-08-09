import { store } from "@/lib/store";
import {
  LOCALSTORAGE_SOURCE_COMPONENT_KEY,
  SESSION_KEY,
} from "@/constants/localStorage";
import { Address, JobType } from "@/types/utility-types";
import {
  addOrUpdateMainChatMessageItem,
  updateMaintenanceMessage,
} from "@/lib/store/features/websocket/websocketSlice";
import { ChatMessageRole, ItemType } from "@/constants/enum";

let jobSearchFilterCache: any | null = null;
// キャッシュ済みの検索条件データが、どの session ID で取得されたものかを保持する。
// session が切り替わったら古いデータを再利用しないために使う。
let jobSearchFilterCacheSessionID = "";
let jobSearchFilterRequest: Promise<any | null> | null = null;
// 共有中の in-flight request が、どの session ID で開始されたものかを保持する。
// session が切り替わったら古い Promise を使い回さないために使う。
let jobSearchFilterRequestSessionID = "";

function getCurrentSessionID() {
  let sessionID = store.getState().websocket.sessionID;
  if (!sessionID) {
    console.error(
      "!!!!!can NOT get session id from store.getState().websocket.sessionID!!!!!",
    );
    sessionID = localStorage.getItem(SESSION_KEY) ?? "";
    if (!sessionID) {
      console.error(
        `!!!!!can NOT get session id from localStorage.getItem(${SESSION_KEY}) either!!!!!`,
      );
    }
  }

  return sessionID;
}

export async function readMockData(
  path: string,
  id: string,
  errorMsg: string,
): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  try {
    const response = await fetch(`/mock/api/responses/${path}/${id}.json`);
    if (response.ok) {
      return {
        data: await response.json(),
        httpStatus: response.status,
        error: null,
      };
    } else {
      return {
        data: null,
        httpStatus: response.status,
        error: new Error(`Failed to fetch mock ${path} data`),
      };
    }
  } catch (err) {
    console.error(`Error loading mock ${path} data:`, err);
    return {
      data: null,
      httpStatus: null,
      error: new Error(errorMsg, { cause: err }),
    };
  }
}

export async function fetchApiData(
  path: string,
  errorMsg: string,
  options: {
    [key: string]: any;
  } = {},
): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  const sessionID = getCurrentSessionID();
  // 分析用の項目をローカルストレージから取得
  const sourceComponent = localStorage.getItem(
    LOCALSTORAGE_SOURCE_COMPONENT_KEY,
  );
  const apiEndpoint = process.env.NEXT_PUBLIC_API_ENDPOINT;
  const url = `${apiEndpoint}/${path}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };
  if (sessionID) {
    headers["X-SESSION-ID"] = sessionID;

    const now = new Date();
    const pad = (n: number, len = 2) => n.toString().padStart(len, "0");
    const yyyy = now.getFullYear();
    const MM = pad(now.getMonth() + 1);
    const dd = pad(now.getDate());
    const HH = pad(now.getHours());
    const mm = pad(now.getMinutes());
    const SS = pad(now.getSeconds());
    const ssssss = pad(now.getMilliseconds(), 6);
    const random = Math.floor(Math.random() * 1000000);

    headers["X-REQUEST-ID"] =
      `${yyyy}${MM}${dd}${HH}${mm}${SS}.${ssssss}.${random}`;
  }
  if (sourceComponent) {
    headers["X-SOURCE-COMPONENT"] = sourceComponent;
  }

  const fetchOptions: RequestInit = options.data
    ? {
        method: options.method || "POST",
        headers,
        body: JSON.stringify(
          Object.fromEntries(
            Object.entries(options.data).filter(([key]) => key !== "method"),
          ),
        ),
      }
    : {
        method: options.method || "GET",
        headers,
      };

  const response = await fetch(url, {
    ...fetchOptions,
    signal: options.signal,
  });

  const contentType = response.headers.get("content-type");
  let data = null;
  if (contentType && contentType.includes("application/json")) {
    data = await response.json();
  }
  if (response.status === 429) {
    // レート制限
    const messageID = `developer_${crypto.randomUUID()}`;
    store.dispatch(
      addOrUpdateMainChatMessageItem({
        itemType: ItemType.ChatMessage,
        role: ChatMessageRole.Agent,
        itemId: messageID,
        message: `ただいまサイトが大変混み合っております。
ご迷惑をおかけしますが、時間をあけて再度アクセスしてください。`,
      }),
    );
  } else if (response.status === 404 && data === null) {
    store.dispatch(
      updateMaintenanceMessage(`システムメンテナンスが開始されました。
ご迷惑をおかけしますが、しばらく経ってから再度お試しください。
まもなくメンテナンス画面に切り替わります。`),
    );

    // 本体側がメンテモードに入ったので、画面リロードして本体側のメンテページに遷移します。
    setTimeout(() => {
      window.location.reload();
    }, 5000);

    return {
      data: null,
      httpStatus: response.status,
      error: new Error("Maintenance mode"),
    };
  }

  return {
    data: data,
    httpStatus: response.status,
    error: response.ok ? null : new Error(errorMsg),
  };
}

export async function getMasterData(
  names: string[],
  options: {
    [key: string]: any;
  } = {},
) {
  const params = new URLSearchParams();
  names.forEach((name) => params.append("names", name));

  try {
    const result = await fetchApiData(
      `master/?${params}`,
      "マスタデータ取得に失敗しました",
      options,
    );
    if (result.error) {
      console.error("マスタデータ取得に失敗しました:", result.error);
      return null;
    } else {
      // 取得対象マスターデータのみを残す
      const filteredList = result.data.List.filter((item: any) =>
        names.includes(item.Name),
      );
      return filteredList;
    }
  } catch (error) {
    console.error("マスタデータ取得に失敗しました", error);
    return null;
  }
}

export async function getSavedUserProfile(
  options: {
    [key: string]: any;
  } = {},
) {
  const savedProfileRetrieved = store.getState().profile.savedProfileRetrieved;
  if (savedProfileRetrieved) {
    // 取得済みの場合、スキップ
    return null;
  }

  const result = await fetchApiData(
    `profile`,
    "プロフィール取得に失敗しました",
    options,
  );

  if (result.error) {
    console.error("プロフィール取得に失敗しました:", result.error);
  } else {
    return result.data;
  }

  return null;
}

export async function getJobSearchFilter(
  options: {
    [key: string]: any;
  } = {},
) {
  const forceRefresh = Boolean(options.forceRefresh);
  const sessionID = `${getCurrentSessionID() ?? ""}`.trim();

  if (!sessionID) {
    jobSearchFilterCache = null;
    jobSearchFilterCacheSessionID = "";
    jobSearchFilterRequest = null;
    jobSearchFilterRequestSessionID = "";
    return null;
  }

  if (jobSearchFilterCacheSessionID !== sessionID) {
    jobSearchFilterCache = null;
    jobSearchFilterCacheSessionID = "";
  }

  if (jobSearchFilterRequestSessionID !== sessionID) {
    jobSearchFilterRequest = null;
    jobSearchFilterRequestSessionID = "";
  }

  if (!forceRefresh && jobSearchFilterCache) {
    // 取得済みの場合、スキップ
    return jobSearchFilterCache;
  }

  // signal 付きの fetch は呼び出し元ごとに abort され得るため、
  // 共有の in-flight request を使い回すと、ある呼び出し元の abort が
  // 別の呼び出し元にも影響する可能性がある。
  // そのため、signal 付きのときは request の共有対象から外す。
  if (!forceRefresh && !options.signal && jobSearchFilterRequest) {
    return jobSearchFilterRequest;
  }

  const request = (async () => {
    const result = await fetchApiData(
      "positions/search_filter/current",
      "ポジション検索条件取得に失敗しました",
      options,
    );

    if (result.error) {
      console.error("ポジション検索条件取得に失敗しました:", result.error);
      return null;
    }

    jobSearchFilterCache = result.data;
    jobSearchFilterCacheSessionID = sessionID;
    return result.data;
  })();

  // signal がない request だけを共有管理し、複数箇所からの同時取得を 1 回にまとめる。
  // signal 付き request は、画面遷移やアンマウントで「この呼び出し元だけ」中断したい場合がある。
  // もし共有すると、ある呼び出し元の abort により、まだ結果を必要としている別の呼び出し元まで
  // 同じ request ごと巻き込んで失敗させてしまうため、共有しない。
  if (!forceRefresh && !options.signal) {
    jobSearchFilterRequestSessionID = sessionID;
    jobSearchFilterRequest = request.finally(() => {
      jobSearchFilterRequest = null;
      jobSearchFilterRequestSessionID = "";
    });
    return jobSearchFilterRequest;
  }

  return request;
}

export async function searchAddressByKeyword(
  keyword: string,
  options: {
    [key: string]: any;
  } = {},
): Promise<Address[]> {
  return searchAddress("location/search/keyword", {
    ...options,
    keyword: keyword.trim(),
  });
}

export async function searchCommutingAreas(
  prefecture: string,
  city: string,
  options: {
    [key: string]: any;
  } = {},
): Promise<Address[]> {
  return searchAddress("location/search/commuting_areas", {
    ...options,
    prefecture_name: prefecture,
    city_name: city,
  });
}

export async function searchByPrefectureCityName(
  prefecture: string,
  city: string,
  options: {
    [key: string]: any;
  } = {},
): Promise<Address[]> {
  const addresses = await searchByPrefectureCityNames(
    [{ prefectureName: prefecture, cityName: city }],
    options,
  );
  return addresses;
}

export async function searchByPrefectureCityNames(
  locations: {
    prefectureName: string;
    cityName: string;
  }[],
  options: {
    [key: string]: any;
  } = {},
): Promise<Address[]> {
  const normalizedLocations = locations
    .map((location) => ({
      prefecture_name: location.prefectureName.trim(),
      city_name: location.cityName.trim(),
    }))
    .filter(
      (location) =>
        location.prefecture_name.length > 0 && location.city_name.length > 0,
    );
  if (normalizedLocations.length === 0) {
    return [];
  }

  try {
    const result = await fetchApiData(
      "location/verify/prefecture/city",
      "住所検索に失敗しました",
      {
        ...options,
        data: {
          locations: normalizedLocations,
        },
      },
    );

    if (result.error) {
      console.error("住所検索に失敗しました:", result.error);
      return [];
    }

    const addresses = result.data || [];
    return addresses.map((item: any) => ({
      prefecture: {
        ID: item.PrefectureID,
        Name: item.PrefectureName,
      },
      city: {
        ID: item.CityID,
        Name: item.CityName,
      },
    }));
  } catch (error) {
    console.error("住所検索に失敗しました:", error);
    return [];
  }
}

async function searchAddress(
  path: string,
  options: {
    [key: string]: any;
  } = {},
): Promise<Address[]> {
  try {
    const result = await fetchApiData(path, "住所検索に失敗しました", {
      data: options,
    });

    if (result.error) {
      console.error("住所検索に失敗しました:", result.error);
    } else {
      const addresses = result.data || [];
      return addresses.map((item: any) => ({
        prefecture: {
          ID: item.PrefectureID,
          Name: item.PrefectureName,
        },
        city: {
          ID: item.CityID,
          Name: item.CityName,
        },
      }));
    }
  } catch (error) {
    console.error("住所検索に失敗しました:", error);
  }

  return [];
}

export async function searchJobtypeByKeyword(
  keyword: string,
  options: {
    [key: string]: any;
  } = {},
): Promise<JobType[]> {
  try {
    const result = await fetchApiData(
      "jobtype/search/keyword",
      "職種検索に失敗しました",
      {
        data: {
          ...options,
          keyword: keyword.trim(),
        },
      },
    );

    if (result.error) {
      console.error("職種検索に失敗しました:", result.error);
      return [];
    }

    if (
      result.data &&
      typeof result.data === "object" &&
      "Jobtypes" in result.data &&
      Array.isArray(result.data.Jobtypes)
    ) {
      return result.data.Jobtypes as JobType[];
    }

    return [];
  } catch (error) {
    console.error("職種検索に失敗しました:", error);
    return [];
  }
}

export async function searchJobtypeByName(
  names: string[],
  options: {
    [key: string]: any;
  } = {},
): Promise<JobType[]> {
  const normalizedNames = names
    .map((name) => name.trim())
    .filter((name) => name.length > 0);
  if (normalizedNames.length === 0) {
    return [];
  }

  try {
    const result = await fetchApiData(
      "jobtype/search/names",
      "職種検索に失敗しました",
      {
        ...options,
        data: {
          names: normalizedNames,
        },
      },
    );

    if (result.error) {
      console.error("職種検索に失敗しました:", result.error);
      return [];
    } else {
      const jobTypes = result.data || [];
      return Array.isArray(jobTypes) ? jobTypes : [];
    }
  } catch (error) {
    console.error("職種検索に失敗しました:", error);
    return [];
  }
}
