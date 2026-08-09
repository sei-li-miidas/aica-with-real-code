"use client";

import { fetchApiData, readMockData } from "@/utils/fetch";

export async function getPositionData(positionId: string): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  if (process.env.NEXT_PUBLIC_MOCK_API === "true") {
    return readMockData(
      "positions",
      positionId,
      "求人情報の取得に失敗しました",
    );
  }
  return fetchApiData(
    `positions/detail/${positionId}`,
    "求人情報の取得に失敗しました",
  );
}

export async function getCompanyData(positionId: string): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  if (process.env.NEXT_PUBLIC_MOCK_API === "true") {
    return readMockData(
      "companies",
      positionId,
      "企業情報の取得に失敗しました",
    );
  }
  return fetchApiData(
    `companies/detail/${positionId}`,
    "企業情報の取得に失敗しました",
  );
}

export async function getBusinessData(positionId: string): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  if (process.env.NEXT_PUBLIC_MOCK_API === "true") {
    return readMockData(
      "businesses",
      positionId,
      "事業情報の取得に失敗しました",
    );
  }
  return fetchApiData(
    `businesses/detail/${positionId}`,
    "事業情報の取得に失敗しました",
  );
}

export async function applyStart(positionId: string): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  return fetchApiData(`apply/${positionId}/start`, "応募できませんでした", {
    method: "POST",
  });
}

export async function addPosition(positionId: string): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  return fetchApiData(`apply/${positionId}/add`, "応募できませんでした", {
    method: "PUT",
  });
}

export async function applyPosition(positionId: string): Promise<{
  data: any;
  httpStatus: number | null;
  error: Error | null;
}> {
  return fetchApiData(`apply/position/${positionId}`, "応募できませんでした", {
    method: "POST",
  });
}
