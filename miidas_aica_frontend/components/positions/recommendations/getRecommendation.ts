import { fetchApiData } from "@/utils/fetch";

interface RecommendationPositionsResult {
  data: any;
  httpStatus: number | null;
  error: Error | null;
}

const cache = new Map<string, RecommendationPositionsResult>();

export default async function getRecommendationPositions(
  searchKey: string,
  theme: string,
): Promise<RecommendationPositionsResult> {
  const cacheKey = `positions/recommendations/${searchKey}/${theme}`;

  if (cache.has(cacheKey)) {
    console.log(
      `[キャッシュあり] Recommendations for searchKey: ${searchKey}, theme: ${theme}`,
    );
    return cache.get(cacheKey)!;
  }

  console.log(
    `[キャッシュなし] Fetching recommendations for searchKey: ${searchKey}, theme: ${theme}`,
  );
  const request = await fetchApiData(
    `positions/recommendations/${searchKey}/${theme}`,
    "おすすめ取得に失敗しました",
  );
  cache.set(cacheKey, request);
  return request;
}
