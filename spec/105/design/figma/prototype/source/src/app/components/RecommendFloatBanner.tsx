import { useState, useEffect } from "react";
import { ChevronRight, X, ThumbsUp, ThumbsDown } from "lucide-react";
import imgMiibo from "figma:asset/289d43a43fdf8eb7cf5c464e50235f2a3e4bc5f0.png";

interface Props {
  isReady: boolean;
  countdown: number;
  onModalStateChange: (open: boolean) => void;
}

const paragraphs = [
  "「圧倒的な裁量権」と「CMO（最高マーケティング責任者）への最短ルート」がここにありそうです！",
  "この企業は現在IPO準備中で、マーケティング予算の配分を社長直下で決められます。「自分の成果がダイレクトに事業貢献につながるポジション」を求めるあなたからして、制限が少なく自社プロダクトで試せる環境のようです。",
  "また、B2B領域は現在、市場価値が非常に高騰しています。あえてここでB2Bの経験を積むことは、将来的なキャリアの市場価値を（B2Cのみの経験よりも）大きく引き上げるはずです。",
  "フルリモートではありませんが、経営陣と膝を突き合わせて戦略を練るには、今のフェーズではむしろ最適な距離感かもしれません。",
  "年収も希望を上回る提示です。「フルリモート」という条件を一度だけ脇に置いて、「経営に近い位置でビジネスを動かす」という視点で、一度話を聞いてみませんか？",
];

const BG_GRADIENT  = "linear-gradient(to right, rgba(192,205,255,0.94), rgba(201,174,255,0.94))";
const BG_MODAL_HDR = "linear-gradient(to right, rgba(192,205,255,0.92), rgba(201,174,255,0.92))";
const TEXT_DARK    = "#2c1f6e";

export function RecommendFloatBanner({ isReady, countdown, onModalStateChange }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [glow, setGlow]     = useState(false);

  useEffect(() => {
    if (!isReady) return;
    setGlow(true);
    const t = setTimeout(() => setGlow(false), 2400);
    return () => clearTimeout(t);
  }, [isReady]);

  return (
    <>
      {/* ── フロートバナー（フッター直上に absolute） ── */}
      <div
        style={{
          background: BG_GRADIENT,
          borderTop: "1px solid rgba(155,124,232,0.3)",
          transition: "box-shadow 0.5s ease",
          boxShadow: glow
            ? "0 -8px 32px rgba(160,130,240,0.55), 0 -2px 0 rgba(192,165,255,0.8)"
            : "0 -4px 20px rgba(124,92,191,0.22)",
          animation: glow ? "bannerGlowC 0.6s ease-out" : undefined,
        }}
      >
        <button
          className="w-full flex items-center gap-[12px] px-[16px] py-[12px]"
          onClick={isReady ? () => { setIsOpen(true); onModalStateChange(true); } : undefined}
          style={{ background: "transparent", border: "none", cursor: isReady ? "pointer" : "default", textAlign: "left" }}
        >
          {/* Character */}
          <div style={{ width: 44, height: 37, flexShrink: 0 }}>
            <img
              src={imgMiibo}
              alt="AICA"
              style={{ width: "100%", height: "100%", objectFit: "contain", animation: "miiboFloatC 2.8s ease-in-out infinite" }}
            />
          </div>

          {/* Text */}
          {!isReady ? (
            /* 分析中 */
            <div className="flex-1 min-w-0">
              <div className="shimmer-bar-c rounded-full mb-[7px]" style={{ height: 13, width: "65%" }} />
              <div className="flex items-center gap-[7px]">
                <div className="flex gap-[3px]">
                  {[0, 1, 2].map((i) => (
                    <div
                      key={i}
                      className="rounded-full"
                      style={{ width: 4, height: 4, background: TEXT_DARK, opacity: 0.4, animation: `typingDotC 1.2s ${i * 0.18}s ease-in-out infinite` }}
                    />
                  ))}
                </div>
                <span className="font-['Noto_Sans_JP',sans-serif] text-[11px]" style={{ color: TEXT_DARK, opacity: 0.65 }}>
                  推薦理由を生成中...
                </span>
                {/* Countdown badge */}
                <span
                  className="ml-auto font-['Noto_Sans_JP',sans-serif] text-[11px] px-[7px] py-[2px] rounded-full shrink-0"
                  style={{ background: "rgba(44,31,110,0.13)", color: TEXT_DARK, fontWeight: 700 }}
                >
                  残り{countdown}s
                </span>
              </div>
            </div>
          ) : (
            /* 推薦完了 */
            <div className="flex-1 min-w-0">
              <p className="font-['Noto_Sans_JP',sans-serif] text-[14px] leading-[1.35]" style={{ fontWeight: 700, color: TEXT_DARK }}>
                あなたへの推薦理由をお教えします！
              </p>
              <p className="font-['Noto_Sans_JP',sans-serif] text-[11px] mt-[2px]" style={{ color: TEXT_DARK, opacity: 0.6 }}>
                タップして確認する
              </p>
            </div>
          )}

          {isReady && (
            <ChevronRight style={{ width: 20, height: 20, color: TEXT_DARK, flexShrink: 0, opacity: 0.6 }} />
          )}
        </button>
      </div>

      {/* ── センターモーダル ── */}
      {/* full-screen overlay → modal はちょうど 50vh、画面中央配置 */}
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center px-[20px]">
          {/* Backdrop */}
          <div className="absolute inset-0" style={{ background: "rgba(0,0,0,0.52)" }} onClick={() => { setIsOpen(false); onModalStateChange(false); }} />

          {/* Card — 50vh、スクロール可 */}
          <div
            className="relative w-full max-w-[335px] bg-white flex flex-col"
            style={{
              borderRadius: 20,
              height: "50vh",
              animation: "modalScaleInC 0.3s cubic-bezier(0.34,1.56,0.64,1)",
              overflow: "hidden",
            }}
          >
            {/* Close */}
            <button
              onClick={() => { setIsOpen(false); onModalStateChange(false); }}
              className="absolute top-[12px] right-[12px] w-[28px] h-[28px] rounded-full flex items-center justify-center cursor-pointer border-none z-10"
              style={{ background: "rgba(44,31,110,0.12)" }}
            >
              <X style={{ width: 15, height: 15, color: TEXT_DARK }} />
            </button>

            {/* Fixed header — does NOT scroll */}
            <div
              className="shrink-0 px-[16px] py-[12px] flex items-center gap-[12px]"
              style={{ background: BG_MODAL_HDR, borderRadius: "20px 20px 0 0" }}
            >
              <div style={{ width: 44, height: 37, flexShrink: 0 }}>
                <img src={imgMiibo} alt="AI" className="w-full h-full object-contain" style={{ animation: "miiboFloatC 2.8s ease-in-out infinite" }} />
              </div>
              <p className="font-['Noto_Sans_JP',sans-serif] text-[14px] leading-[1.4]" style={{ fontWeight: 700, color: TEXT_DARK }}>
                この求人があなたに推薦された理由
              </p>
            </div>

            {/* Scrollable body */}
            <div className="flex-1 overflow-auto px-[16px] pt-[14px] pb-[24px]">
              <p className="font-['Noto_Sans_JP',sans-serif] text-[12px] mb-[10px]" style={{ fontWeight: 700, color: TEXT_DARK }}>主なポイント</p>
              <div className="flex flex-col gap-[10px] mb-[20px]">
                {paragraphs.map((para, i) => (
                  <p key={i} className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[13px] leading-[1.8]" style={{ fontWeight: i === 0 ? 700 : 400 }}>
                    {para}
                  </p>
                ))}
              </div>
              <div className="bg-[#f3f6fa] rounded-[12px] p-[14px] text-center">
                <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[12px] mb-[10px]">この推薦は参考になりましたか？</p>
                <div className="flex items-center justify-center gap-[12px]">
                  <button className="flex items-center gap-[5px] bg-white rounded-full px-[16px] py-[8px] cursor-pointer border-none" style={{ border: "1px solid #dae3ec" }}>
                    <ThumbsUp style={{ width: 14, height: 14, color: "#1bc2f5" }} />
                    <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px]">はい</span>
                  </button>
                  <button className="flex items-center gap-[5px] bg-white rounded-full px-[16px] py-[8px] cursor-pointer border-none" style={{ border: "1px solid #dae3ec" }}>
                    <ThumbsDown style={{ width: 14, height: 14, color: "#8999ab" }} />
                    <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px]">いいえ</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes miiboFloatC {
          0%, 100% { transform: translateY(0px); }
          50%       { transform: translateY(-6px); }
        }
        @keyframes typingDotC {
          0%, 60%, 100% { transform: translateY(0);   opacity: 0.4; }
          30%            { transform: translateY(-4px); opacity: 1; }
        }
        @keyframes bannerGlowC {
          0%   { box-shadow: 0 -4px 20px rgba(124,92,191,0.22); }
          40%  { box-shadow: 0 -10px 40px rgba(160,130,240,0.65), 0 -2px 0 rgba(192,165,255,0.9); }
          100% { box-shadow: 0 -4px 20px rgba(124,92,191,0.22); }
        }
        @keyframes modalScaleInC {
          from { opacity: 0; transform: scale(0.88); }
          to   { opacity: 1; transform: scale(1); }
        }
        .shimmer-bar-c {
          background: linear-gradient(90deg,
            rgba(192,205,255,0.25) 25%,
            rgba(201,174,255,0.5)  50%,
            rgba(192,205,255,0.25) 75%
          );
          background-size: 200% 100%;
          animation: shimmerC 1.6s linear infinite;
        }
        @keyframes shimmerC {
          0%   { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </>
  );
}
