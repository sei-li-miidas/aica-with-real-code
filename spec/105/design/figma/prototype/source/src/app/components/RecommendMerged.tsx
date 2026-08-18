import { useState, useEffect } from "react";
import { ChevronRight } from "lucide-react";
import imgMiibo from "figma:asset/289d43a43fdf8eb7cf5c464e50235f2a3e4bc5f0.png";
import imgMiiboModal from "figma:asset/c006ad515f5770e2a531085f9f5a8d7f914af500.png";

// ── SVG paths（Figmaデザインから）──────────────────────────────────────────
const SVG = {
  close:       "M15.403 16.3752L12 12.9723L8.59705 16.3752L7.62478 15.403L11.0277 12L7.62478 8.59705L8.59705 7.62478L12 11.0277L15.403 7.62478L16.3752 8.59705L12.9723 12L16.3752 15.403L15.403 16.3752Z",
  lightBulb:   "M14.6288 7.31427C14.6288 3.11993 11.0981 -0.249763 6.84717 0.0145571C3.17628 0.242527 0.20125 3.25131 0.0101498 6.92428C-0.0952668 8.9542 0.62759 10.8148 1.8713 12.1987C2.95039 13.3999 3.58237 14.9359 3.58237 16.5509V18.5009C3.58237 19.3842 4.29848 20.0998 5.18128 20.0998H9.44728C10.3306 20.0998 11.0462 19.3837 11.0462 18.5009V16.5224C11.0462 14.9115 11.6911 13.389 12.7656 12.1889C13.9241 10.8953 14.6283 9.18684 14.6283 7.31375L14.6288 7.31427Z",
  lightDot:    "M7.31464 22.2595C8.50743 22.2595 9.47438 21.2926 9.47438 20.0998C9.47438 18.907 8.50743 17.94 7.31464 17.94C6.12184 17.94 5.1549 18.907 5.1549 20.0998C5.1549 21.2926 6.12184 22.2595 7.31464 22.2595Z",
  lightBase:   "M3.58261 18.5012C3.58261 19.3845 4.29871 20.1001 5.18151 20.1001H9.44751C10.3308 20.1001 11.0464 19.384 11.0464 18.5012V16.5512H3.58209V18.5012H3.58261Z",
  chevronDown: "M17.5 9.83198L16.2075 8.5L12 12.8266L7.7925 8.5L6.5 9.83198L12 15.5L17.5 9.83198Z",
  microphone:  "M8.9375 3.4375C8.9375 2.29841 8.01409 1.375 6.875 1.375C5.73591 1.375 4.8125 2.29841 4.8125 3.4375V8.9375C4.8125 10.0766 5.73591 11 6.875 11C8.01409 11 8.9375 10.0766 8.9375 8.9375V3.4375ZM3.4375 3.4375C3.4375 1.53902 4.97652 0 6.875 0C8.77348 0 10.3125 1.53902 10.3125 3.4375V8.9375C10.3125 10.836 8.77348 12.375 6.875 12.375C4.97652 12.375 3.4375 10.836 3.4375 8.9375V3.4375ZM1.375 8.25C1.375 7.8703 1.0672 7.5625 0.6875 7.5625C0.307804 7.5625 0 7.8703 0 8.25V8.9375C0 12.5024 2.71334 15.4336 6.1875 15.7786V17.875H3.4375C3.0578 17.875 2.75 18.1828 2.75 18.5625C2.75 18.9422 3.0578 19.25 3.4375 19.25H10.3125C10.6922 19.25 11 18.9422 11 18.5625C11 18.1828 10.6922 17.875 10.3125 17.875H7.5625V15.7786C11.0367 15.4336 13.75 12.5024 13.75 8.9375V8.25C13.75 7.8703 13.4422 7.5625 13.0625 7.5625C12.6828 7.5625 12.375 7.8703 12.375 8.25V8.9375C12.375 11.9751 9.91257 14.4375 6.875 14.4375C3.83743 14.4375 1.375 11.9751 1.375 8.9375V8.25Z",
};

interface Props {
  isTriggered: boolean;
  isReady: boolean;
  countdown: number;
  totalSeconds: number;
  onTrigger: () => void;
  onModalStateChange: (open: boolean) => void;
}

const BG_COMPACT = "#ffffff";
const TEXT_DARK  = "#2c1f6e";

const RING_R = 15;
const RING_C = 2 * Math.PI * RING_R;

const SPARKLES = [
  { sx: -80, sy: -24, ex: -100, ey: -56, color: "#c9aeff", size: 9, delay: 0    },
  { sx: -38, sy: -26, ex:  -46, ey: -60, color: "#ff9d0a", size: 7, delay: 0.05 },
  { sx:   0, sy: -26, ex:    0, ey: -64, color: "#c0cdff", size: 9, delay: 0.10 },
  { sx:  38, sy: -26, ex:   46, ey: -60, color: "#1bc2f5", size: 7, delay: 0.05 },
  { sx:  80, sy: -24, ex:  100, ey: -56, color: "#ffb347", size: 9, delay: 0    },
  { sx: -68, sy:  24, ex:  -86, ey:  56, color: "#c9aeff", size: 7, delay: 0.07 },
  { sx:   0, sy:  26, ex:    0, ey:  64, color: "#ff9d0a", size: 9, delay: 0.12 },
  { sx:  68, sy:  24, ex:   86, ey:  56, color: "#c0cdff", size: 7, delay: 0.07 },
  { sx: -110, sy:  0, ex: -148, ey:   0, color: "#c9aeff", size: 8, delay: 0.03 },
  { sx:  110, sy:  0, ex:  148, ey:   0, color: "#ffb347", size: 8, delay: 0.03 },
  { sx:  -96, sy: -16, ex: -132, ey: -44, color: "#ffffff", size: 5, delay: 0.08 },
  { sx:   96, sy: -16, ex:  132, ey: -44, color: "#ffffff", size: 5, delay: 0.08 },
  { sx:  -90, sy:  16, ex: -124, ey:  44, color: "#ffffff", size: 5, delay: 0.12 },
  { sx:   90, sy:  16, ex:  124, ey:  44, color: "#ffffff", size: 5, delay: 0.12 },
];

const sections = [
  {
    title: "やりたいこととのマッチ",
    content: "佐藤さんが求める「自社サービスの育成」と「大きな裁量権」を、圧倒的なスピード感の中で実現できるポジションです。希望条件のフルリモートやB2Cとは一部異なりますが、年収の大幅アップCMOへ最短ルートが期待できる、キャリアの飛躍に最適な環境として推薦いたします。",
  },
  {
    title: "今の経験がどう使えるか",
    content: "広告代理店での厳しいクライアントワークで培った「数値に基づいたWebマーケティングの運用スキル」は、この企業のリードマーケター（CMO候補）として即戦力になります。代理店時代に磨かれた仮説検証と実行力は、これから一気に事業を拡大していくフェーズにおいて、企業側が喉から手が出るほど求めている強みそのものです。",
  },
  {
    title: "条件のズレについて",
    content: "正直にお伝えすると、今回の求人は佐藤さんの絶対条件である「フルリモート」「B2C」からは外れ、「週3日出社のハイブリッド」「B2B」となります。しかし、その乖離を補って余りある「年収700万〜900万円」という高い条件提示があります。経営陣と直接議論して戦略を練る今のフェーズでは、出社を交えたコミュニケーションがむしろ事業を前進させる強い武器となります。",
  },
  {
    title: "未来の自分の価値",
    content: "現在、市場価値が急騰しているB2B SaaS領域において、IPO前のフェーズからCMO候補として事業を牽引したという実績は、5年後の佐藤さんのキャリアにおいて圧倒的な資産となります。この経験を積むことで、将来的にフルリモートや地方移住を叶えたいとなった際にも、CxOクラスや戦略顧問として、今よりはるかに自由に働き方や条件を選べる確固たる立場を築けるはずです。",
  },
];

export function RecommendMerged({
  isTriggered,
  isReady,
  countdown,
  totalSeconds,
  onTrigger,
  onModalStateChange,
}: Props) {
  const [isOpen,         setIsOpen]         = useState(false);
  const [showSparkle,    setShowSparkle]    = useState(false);
  const [doBounce,       setDoBounce]       = useState(false);
  const [accordionOpen,  setAccordionOpen]  = useState(true);

  useEffect(() => {
    if (!isTriggered) {
      setShowSparkle(false);
      setIsOpen(false);
      setDoBounce(false);
    }
  }, [isTriggered]);

  useEffect(() => {
    if (!isReady) return;
    setShowSparkle(true);
    setDoBounce(true);
    const t1 = setTimeout(() => setShowSparkle(false), 1000);
    const t2 = setTimeout(() => setDoBounce(false), 900);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [isReady]);

  const handleClick = () => {
    if (!isTriggered) { onTrigger(); return; }
    if (!isReady) return;
    setIsOpen(true);
    onModalStateChange(true);
  };

  const handleClose = () => {
    setIsOpen(false);
    setAccordionOpen(true);
    onModalStateChange(false);
  };

  const ringProgress = totalSeconds > 0 ? countdown / totalSeconds : 0;
  const ringOffset   = RING_C * (1 - ringProgress);

  return (
    <>
      {/* ── Pill wrapper ─────────────────────────────────────────────────── */}
      <div className="flex justify-end px-[12px] pb-[8px]">
        <div style={{ position: "relative", width: "auto" }}>

          {/* スパークル */}
          {showSparkle && (
            <div style={{ position: "absolute", inset: 0, pointerEvents: "none", overflow: "visible", zIndex: 10 }}>
              {SPARKLES.map((sp, i) => (
                <div
                  key={i}
                  style={{
                    position: "absolute",
                    left: "50%", top: "50%",
                    width: sp.size, height: sp.size,
                    marginLeft: -sp.size / 2, marginTop: -sp.size / 2,
                    borderRadius: "50%",
                    background: sp.color,
                    boxShadow: `0 0 6px 2px ${sp.color}88`,
                    ["--sp-sx" as string]: `${sp.sx}px`,
                    ["--sp-sy" as string]: `${sp.sy}px`,
                    ["--sp-ex" as string]: `${sp.ex}px`,
                    ["--sp-ey" as string]: `${sp.ey}px`,
                    animation: `sparkleOut 0.9s ${sp.delay}s cubic-bezier(0.2,0.8,0.4,1) forwards`,
                    opacity: 0,
                  }}
                />
              ))}
            </div>
          )}

          {/* Pill ボタン */}
          <div
            style={{
              padding: 1,
              borderRadius: 999,
              background: isReady
                ? "conic-gradient(from var(--border-angle), #9b7ce8, #ff9d0a, #1bc2f5, #9b7ce8)"
                : "rgba(155,124,232,0.3)",
              boxShadow: isReady
                ? "0 4px 20px rgba(124,92,191,0.38)"
                : "0 4px 20px rgba(124,92,191,0.28)",
              animation: doBounce && isReady
                ? "pillBounce 0.85s cubic-bezier(0.34,1.56,0.64,1), borderBeamSpin 6s linear infinite"
                : isReady
                ? "borderBeamSpin 6s linear infinite"
                : undefined,
            }}
          >
            <div style={{ background: BG_COMPACT, borderRadius: 999 }}>
              <button
                onClick={handleClick}
                style={{
                  background: "transparent",
                  border: "none",
                  cursor: isTriggered && !isReady ? "default" : "pointer",
                  padding: "9px 14px",
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                }}
              >
                <div style={{ width: 34, height: 28, flexShrink: 0 }}>
                  <img
                    src={imgMiibo}
                    alt="AICA"
                    style={{
                      width: "100%", height: "100%", objectFit: "contain",
                      animation: doBounce ? "miiboPop 0.85s ease-out" : "miiboFloat 2.8s ease-in-out infinite",
                    }}
                  />
                </div>

                {!isTriggered ? (
                  <span style={{ fontFamily: "'Noto Sans JP', sans-serif", fontSize: 12, fontWeight: 700, color: TEXT_DARK, whiteSpace: "nowrap" }}>
                    あなたへの推薦理由
                  </span>
                ) : !isReady ? (
                  <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
                    <p style={{ fontFamily: "'Noto Sans JP', sans-serif", fontSize: 11, fontWeight: 700, color: TEXT_DARK, opacity: 0.7, whiteSpace: "nowrap", lineHeight: 1.6, margin: 0, textAlign: "left" }}>
                      あなただけの<br />注目ポイントを準備中
                    </p>
                    {[0, 1, 2].map((i) => (
                      <div
                        key={i}
                        style={{ width: 4, height: 4, borderRadius: "50%", background: TEXT_DARK, opacity: 0.45, animation: `typingDot 1.2s ${i * 0.18}s ease-in-out infinite` }}
                      />
                    ))}
                  </div>
                ) : (
                  <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                    <span style={{ fontFamily: "'Noto Sans JP', sans-serif", fontSize: 11, fontWeight: 700, color: TEXT_DARK, whiteSpace: "nowrap", lineHeight: 1.6, textAlign: "left" }}>
                      ここに注目！
                    </span>
                    <span
                      style={{
                        display: "inline-flex", alignItems: "center", justifyContent: "center",
                        background: TEXT_DARK, borderRadius: "50%", width: 28, height: 28, flexShrink: 0,
                      }}
                    >
                      <ChevronRight style={{ width: 16, height: 16, color: "#ffffff" }} />
                    </span>
                  </div>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* ── チャットモーダル ──────────────────────────────────────────────── */}
      {isOpen && (
        <div
          className="fixed inset-0 z-[500] flex justify-center"
          style={{ pointerEvents: "none", animation: "modalIn 0.3s ease-out" }}
        >
          {/* スマホ幅コンテナ */}
          <div
            className="relative w-full h-full"
            style={{
              maxWidth: 375,
              background: "rgba(0,0,0,0.6)",
              pointerEvents: "auto",
              display: "flex",
              flexDirection: "column",
              alignItems: "flex-end",
              padding: 16,
            }}
          >
            {/* カード本体 */}
            <div
              style={{
                width: 343,
                height: "100%",
                borderRadius: 8,
                overflow: "hidden",
                display: "flex",
                flexDirection: "column",
                backgroundImage: "linear-gradient(127.869deg, rgb(216,224,255) 0%, rgb(240,241,255) 30%, rgb(239,248,250) 65%, rgb(254,240,247) 100%)",
              }}
            >
              {/* ── Header ── */}
              <div className="shrink-0 flex items-center justify-end p-[12px]">
                <button
                  onClick={handleClose}
                  className="border-none cursor-pointer p-0"
                  style={{ background: "transparent", width: 24, height: 24 }}
                >
                  <svg className="block size-full" fill="none" viewBox="0 0 24 24">
                    <rect fill="#F3F6FA" height="24" rx="12" width="24" />
                    <path d={SVG.close} fill="#273340" />
                  </svg>
                </button>
              </div>

              {/* ── Body（スクロール） ── */}
              <div className="flex-1 overflow-auto pb-[20px]">

                {/* メインカード */}
                <div className="px-[12px] py-[8px]">
                  <div className="bg-white rounded-[16px] w-full" style={{ boxShadow: "0px 2px 2px rgba(62,64,213,0.06)" }}>
                    <div className="flex flex-col gap-[12px] p-[12px]">

                      {/* タイトル行 */}
                      <div className="flex gap-[8px] items-center w-full">
                        {/* 電球アイコン */}
                        <div className="overflow-clip relative shrink-0" style={{ width: 24, height: 24 }}>
                          <div className="absolute" style={{ inset: "4.17% 19.52% 3.09% 19.52%" }}>
                            <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 14.6288 22.2595">
                              <path d={SVG.lightBulb} fill="#FFD134" />
                              <path d={SVG.lightDot}  fill="#C4CDD8" />
                              <path d={SVG.lightBase}  fill="#C4CDD8" />
                            </svg>
                          </div>
                        </div>
                        <p
                          className="flex-1 min-w-0 leading-[1.3] text-[#2e3679]"
                          style={{ fontFamily: "'Noto Sans JP', sans-serif", fontWeight: 700, fontSize: 16 }}
                        >
                          ここに注目！
                        </p>
                        {/* アコーディオン矢印ボタン */}
                        <button
                          onClick={() => setAccordionOpen(v => !v)}
                          className="shrink-0 border-none cursor-pointer p-0"
                          style={{ background: "transparent", width: 24, height: 24, transform: accordionOpen ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.25s ease" }}
                        >
                          <svg className="block size-full" fill="none" viewBox="0 0 24 24">
                            <rect fill={accordionOpen ? "#5E59EC" : "#F3F6FA"} height="24" rx="12" width="24" />
                            <path clipRule="evenodd" d={SVG.chevronDown} fill={accordionOpen ? "white" : "#273340"} fillRule="evenodd" />
                          </svg>
                        </button>
                      </div>

                      {/* アコーディオン展開コンテンツ */}
                      {accordionOpen && (
                        <>
                          {/* 区切り線 */}
                          <div className="w-full h-px" style={{ background: "rgba(68,98,135,0.2)" }} />

                          {/* 説明テキスト */}
                          <p
                            className="leading-[1.6] text-[#2e3679] w-full"
                            style={{ fontFamily: "'Noto Sans JP', sans-serif", fontWeight: 400, fontSize: 13 }}
                          >
                            佐藤さんが求める「自社サービスの育成」と「大きな裁量権」を、圧倒的なスピード感の中で実現できるポジションです。希望条件のフルリモートやB2Cとは一部異なりますが、年収の大幅アップとCMOへの最短ルートが期待できる、キャリアの飛躍に最適な環境として推薦いたします。
                          </p>

                          {/* セクションカード */}
                          {sections.map((s, i) => (
                            <div key={i} className="bg-white rounded-[12px] w-full relative">
                              <div
                                className="absolute inset-0 rounded-[12px] pointer-events-none"
                                style={{ border: "1px solid rgba(68,98,135,0.2)" }}
                              />
                              <div className="flex flex-col gap-[8px] p-[12px]">
                                <p
                                  className="leading-[1.5] text-[#2c1f6e]"
                                  style={{ fontFamily: "'Noto Sans JP', sans-serif", fontWeight: 700, fontSize: 14 }}
                                >
                                  {s.title}
                                </p>
                                <p
                                  className="leading-[1.6] text-[#2e3679]"
                                  style={{ fontFamily: "'Noto Sans JP', sans-serif", fontWeight: 400, fontSize: 13 }}
                                >
                                  {s.content}
                                </p>
                              </div>
                            </div>
                          ))}

                          {/* 免責テキスト */}
                          <div className="flex items-start w-full">
                            <span className="shrink-0 leading-[1.6]" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "rgba(39,51,64,0.6)", fontWeight: 400, fontSize: 12 }}>※</span>
                            <p className="flex-1 min-w-0 leading-[1.6]" style={{ fontFamily: "'Noto Sans JP', sans-serif", color: "rgba(39,51,64,0.6)", fontWeight: 400, fontSize: 12 }}>
                              これはAIが求人情報を基に作成したものです。内容の正確性を保証するものではありません。最新の求人情報を必ずご確認ください。
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  </div>
                </div>

                {/* AIチャットバブル */}
                <div className="flex flex-col gap-[4px] items-start pl-[12px] pr-[40px] py-[8px]">
                  <div style={{ height: 40, width: 48, flexShrink: 0 }}>
                    <img
                      alt="AICA"
                      src={imgMiiboModal}
                      style={{ width: "100%", height: "100%", objectFit: "cover", animation: "miiboFloat 2.8s ease-in-out infinite" }}
                    />
                  </div>
                  <div className="bg-white w-full rounded-bl-[16px] rounded-br-[16px] rounded-tr-[16px]" style={{ boxShadow: "0px 2px 4px rgba(62,64,213,0.06)" }}>
                    <div className="flex items-center p-[12px]">
                      <p className="flex-1 min-w-0 leading-[1.5] text-[#2e3679]" style={{ fontFamily: "'Noto Sans JP', sans-serif", fontWeight: 400, fontSize: 15 }}>
                        この求人について、気になる点やご質問はありますか？
                        <br />
                        お気軽にお尋ねください。
                      </p>
                    </div>
                  </div>
                </div>
              </div>

              {/* ── Footer ── */}
              <div
                className="shrink-0 flex gap-[8px] items-end px-[12px] py-[8px]"
                style={{ backdropFilter: "blur(2px)", background: "linear-gradient(to right, #cdd7fc, #efe8fd)" }}
              >
                <div className="flex-1 min-w-0 rounded-[24px] bg-white" style={{ boxShadow: "0px 1px 4px rgba(62,64,213,0.05)" }}>
                  <div className="flex items-center px-[16px] py-[12px]">
                    <p className="shrink-0 leading-[1.5] text-[#b0bcc7] whitespace-nowrap" style={{ fontFamily: "'Noto Sans JP', sans-serif", fontWeight: 400, fontSize: 15 }}>
                      メッセージを入力
                    </p>
                  </div>
                </div>
                <div
                  className="flex items-center justify-center shrink-0 rounded-full"
                  style={{ width: 43, height: 43, background: "rgba(94,89,236,0.1)" }}
                >
                  <div className="overflow-clip relative" style={{ width: 22, height: 22 }}>
                    <div className="absolute" style={{ inset: "6.25% 18.75%" }}>
                      <svg className="absolute block inset-0 size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 13.75 19.25">
                        <path d={SVG.microphone} fill="#2E3679" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @property --border-angle {
          syntax: '<angle>';
          initial-value: 0deg;
          inherits: false;
        }
        @keyframes borderBeamSpin {
          to { --border-angle: 360deg; }
        }
        @keyframes miiboFloat {
          0%, 100% { transform: translateY(0); }
          50%       { transform: translateY(-5px); }
        }
        @keyframes miiboPop {
          0%   { transform: scale(0.85); }
          35%  { transform: scale(1.45) translateY(-8px); }
          60%  { transform: scale(1.1)  translateY(-2px); }
          80%  { transform: scale(1.2)  translateY(-4px); }
          100% { transform: scale(1)   translateY(0); }
        }
        @keyframes typingDot {
          0%, 60%, 100% { transform: translateY(0);   opacity: 0.4; }
          30%            { transform: translateY(-4px); opacity: 1; }
        }
        @keyframes pillBounce {
          0%   { transform: scale(1); }
          22%  { transform: scale(1.14); }
          45%  { transform: scale(0.94); }
          65%  { transform: scale(1.07); }
          80%  { transform: scale(0.97); }
          100% { transform: scale(1); }
        }
        @keyframes sparkleOut {
          0%   { transform: translate(var(--sp-sx), var(--sp-sy)) scale(1.4); opacity: 1; }
          70%  { opacity: 0.9; }
          100% { transform: translate(var(--sp-ex), var(--sp-ey)) scale(0);   opacity: 0; }
        }
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.96); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </>
  );
}
