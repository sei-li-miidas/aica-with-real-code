import type { NextConfig } from "next";

// 環境変数がない場合はassetPrefixを設定しない
const assetPathEnv = process.env.NEXT_PUBLIC_ASSET_PATH?.trim();
const assetPrefixNextOption = assetPathEnv ? { assetPrefix: assetPathEnv } : {};

// 環境変数がない場合はbasePathを設定しない
const basePathEnv = process.env.NEXT_PUBLIC_BASE_PATH?.trim();
const basePathOption = basePathEnv ? { basePath: basePathEnv } : {};

// NEXT_PUBLIC_APP_ENVがproductionまたはstagingのときはエラーログのみ出力する
const appEnv = process.env.NEXT_PUBLIC_APP_ENV?.trim();
const compilerOption =
  appEnv === "production" || appEnv === "staging"
    ? { compiler: { removeConsole: { exclude: ["error"] } } }
    : {};

const nextConfig: NextConfig = {
  devIndicators: false,
  output: "export",
  distDir: "build",
  trailingSlash: true,
  ...assetPrefixNextOption,
  ...basePathOption,
  ...compilerOption,
};

export default nextConfig;
