import { useState, useEffect } from "react";
import { X, ThumbsUp, ThumbsDown } from "lucide-react";
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

const FAB_GRADIENT    = "linear-gradient(135deg, #c0cdff 0%, #c9aeff 100%)";
const HEADER_GRADIENT = "linear-gradient(to right, rgba(192,205,255,0.92), rgba(201,174,255,0.92))";
const HEADER_TEXT     = "#2c1f6e";

export function RecommendFAB({ isReady, countdown, onModalStateChange }: Props) {
  const [isOpen, setIsOpen] = useState(false);
  const [playAttention, setPlayAttention] = useState(false);
  // バッジは isReady 後のみ表示（カウントダウン中は絶対に出さない）
  const [showBadge, setShowBadge] = useState(false);

  useEffect(() => {
    if (!isReady) return;
    setPlayAttention(true);
    setShowBadge(true);
    const timer = setTimeout(() => setPlayAttention(false), 3200);
    return () => clearTimeout(timer);
  }, [isReady]);

  const handleOpen = () => {
    setIsOpen(true);
    setShowBadge(false);
    onModalStateChange(true);
  };

  const handleClose = () => {
    setIsOpen(false);
    onModalStateChange(false);
  };

  return (
    <>
      {/* ── FAB: circle + label ── */}
      <div
        className="flex flex-col items-center gap-[4px] select-none"
        onClick={isReady ? handleOpen : undefined}
        role="button"
        aria-label="AI推薦理由を確認"
        style={{ cursor: isReady ? "pointer" : "default" }}
      >
        {/* Glow rings on ready */}
        <div className="relative" style={{ width: 60, height: 60 }}>
          {playAttention && (
            <>
              <div className="absolute inset-0 rounded-full" style={{ background: FAB_GRADIENT, animation: "glowRingB 0.8s ease-out 0s forwards" }} />
              <div className="absolute inset-0 rounded-full" style={{ background: FAB_GRADIENT, animation: "glowRingB 0.8s ease-out 0.25s forwards" }} />
              <div className="absolute inset-0 rounded-full" style={{ background: FAB_GRADIENT, animation: "glowRingB 0.8s ease-out 0.5s forwards" }} />
            </>
          )}

          {/* Main circle */}
          <div
            className="absolute inset-0 rounded-full flex items-center justify-center"
            style={{
              background: isReady
                ? FAB_GRADIENT
                : "linear-gradient(135deg, rgba(192,205,255,0.45) 0%, rgba(201,174,255,0.45) 100%)",
              boxShadow: isReady
                ? playAttention
                  ? "0 0 0 4px rgba(192,165,255,0.4), 0 6px 24px rgba(160,130,240,0.5)"
                  : "0 4px 18px rgba(160,130,240,0.4)"
                : "0 2px 10px rgba(160,130,240,0.15)",
              animation: playAttention
                ? "fabBounceB 0.7s cubic-bezier(0.34,1.56,0.64,1)"
                : isReady
                ? undefined
                : "loadingPulseB 1.6s ease-in-out infinite",
              transition: "background 0.4s, box-shadow 0.4s",
            }}
          >
            {!isReady ? (
              <div className="flex gap-[4px] items-center">
                {[0, 1, 2].map((i) => (
                  <div
                    key={i}
                    className="rounded-full"
                    style={{ width: 6, height: 6, background: "#9b7ce8", animation: `typingDotB 1.0s ${i * 0.16}s ease-in-out infinite` }}
                  />
                ))}
              </div>
            ) : (
              <img
                src={imgMiibo}
                alt="AIキャラクター"
                style={{
                  width: 44, height: 37, objectFit: "contain",
                  animation: playAttention ? "miiboBounceB 0.7s ease-out" : "miiboFloatB 2.8s ease-in-out infinite",
                }}
              />
            )}
          </div>

          {/* Notification badge — isReady かつ showBadge の両方が true の時のみ */}
          {isReady && showBadge && (
            <div
              className="absolute flex items-center justify-center rounded-full"
              style={{ width: 16, height: 16, top: -2, right: -2, background: "#ff4757", border: "2px solid white", animation: "badgePopB 0.4s cubic-bezier(0.34,1.56,0.64,1)" }}
            >
              <span style={{ fontSize: 8, fontWeight: 700, color: "white", lineHeight: 1 }}>!</span>
            </div>
          )}
        </div>

        {/* Label + countdown */}
        <span
          className="font-['Noto_Sans_JP',sans-serif] text-[10px] leading-none whitespace-nowrap"
          style={{ fontWeight: 700, color: isReady ? HEADER_TEXT : "#9b7ce8", opacity: isReady ? 1 : 0.8 }}
        >
          {isReady ? "推薦理由" : "分析中..."}
        </span>
        {/* Countdown shown only while loading */}
        {!isReady && (
          <span
            className="font-['Noto_Sans_JP',sans-serif] text-[9px] leading-none whitespace-nowrap px-[5px] py-[2px] rounded-full"
            style={{ background: "rgba(124,92,191,0.15)", color: "#7c5cbf", fontWeight: 700 }}
          >
            残り{countdown}s
          </span>
        )}
      </div>

      {/* ── Half-modal ── */}
      {/* overlay は全画面（inset-0）: "ハーフモーダル表示中はヘッダーは不要" なので switcher も覆う */}
      {isOpen && (
        <div className="fixed inset-0 z-[200] flex items-end justify-center">
          <div className="absolute inset-0 bg-black/50" onClick={handleClose} />
          <div
            className="relative w-full max-w-[375px] bg-white rounded-t-[20px] overflow-auto"
            style={{ height: "calc(50vh + 100px)", animation: "fabSheetUpB 0.28s ease-out" }}
          >
            {/* Drag handle */}
            <div className="flex justify-center pt-[10px] pb-[4px] shrink-0">
              <div className="w-[40px] h-[4px] bg-[#dae3ec] rounded-full" />
            </div>
            {/* Close */}
            <button
              onClick={handleClose}
              className="absolute top-[14px] right-[14px] w-[28px] h-[28px] rounded-full flex items-center justify-center cursor-pointer border-none"
              style={{ background: "rgba(44,31,110,0.12)" }}
            >
              <X style={{ width: 15, height: 15, color: HEADER_TEXT }} />
            </button>

            {/* Scrollable inner content */}
            <div className="overflow-auto px-[16px] pb-[28px]" style={{ height: "calc(100% - 32px)" }}>
              {/* Modal header card */}
              <div
                className="mb-[14px] rounded-[14px] px-[16px] py-[12px] flex items-center gap-[12px]"
                style={{ background: HEADER_GRADIENT, border: "1.5px solid rgba(192,160,255,0.35)" }}
              >
                <div style={{ width: 48, height: 40, flexShrink: 0 }}>
                  <img src={imgMiibo} alt="AI" className="w-full h-full object-contain" style={{ animation: "miiboFloatB 2.8s ease-in-out infinite" }} />
                </div>
                <p className="font-['Noto_Sans_JP',sans-serif] text-[14px] leading-[1.4]" style={{ fontWeight: 700, color: HEADER_TEXT }}>
                  この求人があなたに推薦された理由
                </p>
              </div>

              <p className="font-['Noto_Sans_JP',sans-serif] text-[12px] mb-[10px]" style={{ fontWeight: 700, color: HEADER_TEXT }}>主なポイント</p>
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
        @keyframes fabSheetUpB {
          from { transform: translateY(100%); }
          to   { transform: translateY(0); }
        }
        @keyframes miiboFloatB {
          0%, 100% { transform: translateY(0px); }
          50%       { transform: translateY(-6px); }
        }
        @keyframes miiboBounceB {
          0%   { transform: scale(0.7) translateY(0); }
          50%  { transform: scale(1.15) translateY(-4px); }
          100% { transform: scale(1) translateY(0); }
        }
        @keyframes fabBounceB {
          0%   { transform: scale(1); }
          20%  { transform: scale(1.38); }
          45%  { transform: scale(1.12); }
          65%  { transform: scale(1.28); }
          80%  { transform: scale(1.05); }
          100% { transform: scale(1); }
        }
        @keyframes glowRingB {
          0%   { transform: scale(1);   opacity: 0.7; }
          100% { transform: scale(2.4); opacity: 0; }
        }
        @keyframes loadingPulseB {
          0%, 100% { opacity: 0.6; transform: scale(0.97); }
          50%       { opacity: 1;   transform: scale(1.03); }
        }
        @keyframes typingDotB {
          0%, 60%, 100% { transform: translateY(0);   opacity: 0.4; }
          30%            { transform: translateY(-5px); opacity: 1; }
        }
        @keyframes badgePopB {
          0%   { transform: scale(0); opacity: 0; }
          70%  { transform: scale(1.3); opacity: 1; }
          100% { transform: scale(1); opacity: 1; }
        }
      `}</style>
    </>
  );
}
