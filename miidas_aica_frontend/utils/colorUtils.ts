// 色をhexからRGBに変換
function hexToRgb(hex: string): { r: number; g: number; b: number } | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result
    ? {
        r: parseInt(result[1], 16),
        g: parseInt(result[2], 16),
        b: parseInt(result[3], 16),
      }
    : null;
}

// RGBの色をhexに変換
function rgbToHex(r: number, g: number, b: number): string {
  return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1).padStart(6, "0")}`;
}

// 色の変化を計算する
export function interpolateColor(
  color1Hex: string,
  color2Hex: string,
  factor: number,
): string {
  const c1 = hexToRgb(color1Hex);
  const c2 = hexToRgb(color2Hex);

  if (!c1 || !c2) {
    return color1Hex; // Fallback or throw error
  }

  const r = Math.round(c1.r + factor * (c2.r - c1.r));
  const g = Math.round(c1.g + factor * (c2.g - c1.g));
  const b = Math.round(c1.b + factor * (c2.b - c1.b));

  return rgbToHex(r, g, b);
}
