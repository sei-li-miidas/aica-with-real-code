import { useState, useEffect } from "react";
import svgPaths from "../imports/svg-bvynv977e8";
import imgJHyk8AV2 from "figma:asset/5b9d3a0807f0fb8841ca9cf42b4185c1d649bd8f.png";
import img891C8706924C4A59B1B7B85765E580122 from "figma:asset/3041fcce9dce1c3acac08446865066fc2a3a0ac0.png";
import img156B5463Da9E4102800709565847Af4A1 from "figma:asset/17c23f55fa425264e39d4d58decdf7faf07df6db.png";
import { imgJHyk8AV1, img891C8706924C4A59B1B7B85765E580121 } from "../imports/svg-dfabc";
import { RecommendMerged } from "./components/RecommendMerged";

// ─── Demo timing config ────────────────────────────────────────────────────────
// 10秒で実際のシナリオをシミュレーション
const DEMO_DELAY_MS = 10000;
const DEMO_SECS = DEMO_DELAY_MS / 1000;

// ─── URL param helpers ─────────────────────────────────────────────────────────
function getPlanFromURL(): 1 {
  return 1;
}
function setPlanInURL(id: 1) {
  // No longer needed, but keeping for compatibility
}

// ─── Status bar ──────────────────────────────────────────────────────────────
function StatusBar() {
  return (
    <div className="bg-white flex items-center justify-between px-[16px] pt-[10px] pb-[2px]">
      <span className="font-['Inter',sans-serif] text-[#273340] text-[14px]" style={{ fontWeight: 700 }}>11:42</span>
      <div className="h-[11px] w-[75px] relative">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 75 11">
          <g id="Frame 1643">
            <path clipRule="evenodd" d={svgPaths.p103836f0} fill="#273340" fillRule="evenodd" />
            <path clipRule="evenodd" d={svgPaths.p1d509400} fill="#273340" fillRule="evenodd" />
            <g id="Battery">
              <path d={svgPaths.p35bf7080} fill="#273340" />
              <path clipRule="evenodd" d={svgPaths.p37e82a80} fill="#273340" fillRule="evenodd" />
            </g>
          </g>
        </svg>
      </div>
    </div>
  );
}

// ─── Header bar ───────────────────────────────────────────────────────────────
function HeaderBar() {
  return (
    <div className="bg-white flex h-[46px] items-center justify-between px-[10px] relative" style={{ borderBottom: "1px solid #eef2f7" }}>
      <div className="size-[24px] relative">
        <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 24 24">
          <path clipRule="evenodd" d={svgPaths.p389de000} fill="#354659" fillRule="evenodd" />
        </svg>
      </div>
      <p className="font-['Noto_Sans_JP',sans-serif] leading-normal text-[#354659] text-[15px] whitespace-nowrap absolute left-1/2 -translate-x-1/2" style={{ fontWeight: 700 }}>
        ミイダス株式会社
      </p>
      <div className="w-[24px]" />
    </div>
  );
}

// ─── Hero section ─────────────────────────────────────────────────────────────
function HeroSection() {
  return (
    <div className="relative w-full overflow-hidden" style={{ height: 210 }}>
      <div className="absolute left-0 top-0" style={{ width: 421, height: 281, maskImage: `url('${imgJHyk8AV1}')`, maskSize: "330px 210px", maskPosition: "39px 47px", maskRepeat: "no-repeat", marginLeft: -39, marginTop: -47 }}>
        <img alt="" className="absolute inset-0 max-w-none object-cover size-full" src={imgJHyk8AV2} />
      </div>
      <div className="absolute" style={{ left: 374, top: 0, width: 333, height: 222, maskImage: `url('${img891C8706924C4A59B1B7B85765E580121}')`, maskSize: "38px 210px", maskPosition: "8px 5px", maskRepeat: "no-repeat", marginLeft: -8, marginTop: -5 }}>
        <img alt="" className="absolute inset-0 max-w-none object-cover size-full" src={img156B5463Da9E4102800709565847Af4A1} />
      </div>
      <div className="absolute bg-white flex flex-col gap-[2px] items-center justify-center rounded-full" style={{ width: 64, height: 64, right: 10, bottom: 10, border: "1px solid #e7eaef", paddingTop: 3 }}>
        <p className="font-['Noto_Sans_JP',sans-serif] text-[#6885a5] text-[9px] text-center w-full leading-none" style={{ fontWeight: 500 }}>マッチ度</p>
        <p className="font-['Noto_Sans_JP',sans-serif] text-[#ff5757] text-[30px] text-center w-full leading-none" style={{ fontWeight: 700 }}>A</p>
      </div>
      <div className="absolute left-0 w-full flex justify-center gap-[8px]" style={{ bottom: 8 }}>
        <div className="w-[6px] h-[6px] rounded-full bg-[#1bc2f5]" />
        <div className="w-[6px] h-[6px] rounded-full bg-[#dae3ec]" />
        <div className="w-[6px] h-[6px] rounded-full bg-[#dae3ec]" />
      </div>
    </div>
  );
}

// ─── Job title ────────────────────────────────────────────────────────────────
function JobTitle() {
  return (
    <div className="w-full px-[10px] pb-[20px] pt-[10px]">
      <p className="font-['Noto_Sans_JP',sans-serif] leading-[1.5] text-[#354659] text-[18px] w-full" style={{ fontWeight: 700 }}>
        キャリアチェンジ歓迎／経験豊富なエンジニアのもとで成長したいエンジニア募集
      </p>
    </div>
  );
}

// ─── Quick check panel ────────────────────────────────────────────────────────
function QuickCheckItem({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="flex flex-1 gap-[8px] h-[48px] items-center min-w-0">
      <div className="flex items-center justify-center w-[40px] shrink-0">{icon}</div>
      <div className="flex flex-col font-['Noto_Sans_JP',sans-serif] items-start justify-center leading-[1.5]">
        <p className="text-[#25b8e5] text-[13px] shrink-0" style={{ fontWeight: 700 }}>{label}</p>
        <p className="text-[#354659] text-[15px] whitespace-nowrap" style={{ fontWeight: 700 }}>{value}</p>
      </div>
    </div>
  );
}

function QuickCheckPanel() {
  return (
    <div className="bg-[#e3f6fe] w-full px-[12px] py-[16px]">
      <div className="bg-white rounded-[8px] w-full" style={{ border: "2px solid #1bc2f5" }}>
        <div className="bg-[#1bc2f5] rounded-tl-[8px] rounded-tr-[8px] px-[16px] py-[8px]">
          <p className="font-['Noto_Sans_JP',sans-serif] text-white text-[15px] text-center" style={{ fontWeight: 700 }}>気になる項目をチェック！</p>
        </div>
        <div className="flex flex-col gap-[16px] p-[16px]">
          <div className="flex gap-[8px]">
            <QuickCheckItem label="休日" value="週休2日制" icon={<div className="h-[39px] w-[40px] relative"><svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 40.5 39.5698"><path d={svgPaths.pb0be800} fill="#6C85A1" stroke="#6C85A1" /><path d={svgPaths.p3dc1ac00} fill="#6C85A1" /><path d={svgPaths.p1347af80} fill="#6C85A1" /><path d={svgPaths.p1c6d6700} fill="#6C85A1" /></svg></div>} />
            <QuickCheckItem label="年間休日" value="120日以上" icon={<div className="h-[35px] w-[40px] relative"><svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 40.25 34.6197"><path d={svgPaths.p1b9a3700} fill="#6C85A1" /><circle cx="28.6345" cy="22.8988" fill="white" r="7.9801" /><path d={svgPaths.p1742f200} fill="#6C85A1" stroke="#6C85A1" strokeWidth="0.5" /><path d={svgPaths.p3ff37f00} fill="#6C85A1" stroke="#6C85A1" strokeWidth="0.2" /></svg></div>} />
          </div>
          <div className="flex gap-[8px]">
            <QuickCheckItem label="平均残業時間" value="月30時間以内" icon={<div className="h-[40px] w-[35px] relative"><svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 34.4309 31.4797"><path d={svgPaths.p37f76200} fill="#6C85A1" /><path d={svgPaths.p36f45200} fill="#6C85A1" /></svg></div>} />
            <QuickCheckItem label="在宅勤務" value="NO" icon={<div className="h-[36px] w-[40px] relative"><svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 40 35.7895"><path clipRule="evenodd" d={svgPaths.p35be6480} fill="#6C85A1" fillRule="evenodd" /><path d={svgPaths.p31552800} fill="#6C85A1" /><rect fill="#6C85A1" height="2.10526" rx="1.05263" width="6.31579" x="22.1052" y="25.7894" /><rect fill="#6C85A1" height="2.10526" rx="1.05263" transform="rotate(111.893 30.9478 21.4023)" width="7.18852" x="30.9478" y="21.4023" /></svg></div>} />
          </div>
          <div className="flex gap-[8px]">
            <QuickCheckItem label="書類選考" value="あり" icon={<div className="h-[40px] w-[37px] relative"><svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 36.7568 40"><path d={svgPaths.p9399b00} fill="#6C85A1" /><path d={svgPaths.p3454c80} fill="#6C85A1" /><path d={svgPaths.p1e7ada00} fill="#6C85A1" /></svg></div>} />
            <QuickCheckItem label="オンライン面接" value="YES" icon={<div className="h-[31px] w-[40px] relative"><svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 40.5 31.4091"><path d={svgPaths.p1782ed80} fill="#6C85A1" /><path d={svgPaths.p2cd75e80} fill="#6C85A1" /><path d={svgPaths.p144fc700} fill="white" /><path d={svgPaths.p20164c80} fill="#6C85A1" stroke="#6C85A1" /><rect fill="#6C85A1" height="1.81818" rx="0.909091" width="10" x="25.9091" y="4.59085" /><rect fill="#6C85A1" height="1.81818" rx="0.909091" transform="rotate(111.893 30.9478 21.4023)" width="7.27273" x="30.9478" y="21.4023" /></svg></div>} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Tab navigation ───────────────────────────────────────────────────────────
function TabNav() {
  return (
    <div className="bg-[#f3f6fa] h-[76px] w-full flex items-center" style={{ borderTop: "1px solid #dae3ec", borderBottom: "1px solid #dae3ec" }}>
      <div className="flex gap-[5px] items-center pl-[8px] w-full">
        {[{ label: "募集要項", active: true }, { label: "選考方法", active: false }, { label: "企業情報", active: false }, { label: "業界研究", active: false, muted: true }]
          .map(({ label, active, muted }) => (
            <div key={label} className="flex items-center justify-center rounded-full shrink-0" style={{ width: 113, padding: "11px 12px 11px 15px", background: active ? "#1bc2f5" : "white", border: `1px solid ${active ? "#1bc2f5" : "#8999ab"}`, boxShadow: "2px 2px 4px 0px rgba(30,59,98,0.15)" }}>
              <span className="font-['Noto_Sans_JP',sans-serif] text-[16px] whitespace-nowrap leading-normal" style={{ fontWeight: 700, color: active ? "white" : muted ? "#6885a5" : "#354659" }}>{label}</span>
            </div>
          ))}
      </div>
    </div>
  );
}

// ─── Recruit title ────────────────────────────────────────────────────────────
function RecruitTitle() {
  return (
    <div className="w-full py-[24px] pl-[12px]">
      <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[26px] text-center whitespace-nowrap" style={{ fontWeight: 700 }}>募集要項</p>
    </div>
  );
}

// ─── Section title ────────────────────────────────────────────────────────────
function SectionTitle({ title }: { title: string }) {
  return (
    <div className="bg-[#f3f6fa] w-full relative" style={{ borderTop: "5px solid #1bc2f5" }}>
      <div className="flex items-center pb-[14px] pl-[8px] pt-[18px] w-full">
        <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[18px] whitespace-nowrap leading-normal" style={{ fontWeight: 700 }}>{title}</p>
      </div>
    </div>
  );
}

// ─── Section body ─────────────────────────────────────────────────────────────
function SectionBody({ text }: { text: string }) {
  return (
    <div className="px-[4px]">
      <p className="font-['Noto_Sans_JP',sans-serif] leading-[1.8] text-[#354659] text-[14px] whitespace-pre-wrap">{text}</p>
    </div>
  );
}

// ─── Read more button ─────────────────────────────────────────────────────────
function ReadMoreBtn() {
  return (
    <div className="h-[44px] relative rounded-full w-full" style={{ border: "1px solid #8999ab" }}>
      <div className="flex flex-col items-center justify-center size-full">
        <div className="flex gap-[4px] items-center">
          <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[14px] text-right whitespace-nowrap leading-[24px]" style={{ fontWeight: 700 }}>続きを読む</p>
          <div className="size-[20px] relative">
            <div className="absolute inset-[29.17%_16.67%] flex items-center justify-center">
              <div className="h-[16px] rotate-90 w-[10px]">
                <svg className="block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 8.33333 13.3333">
                  <path clipRule="evenodd" d={svgPaths.p3ec353f0} fill="#354659" fillRule="evenodd" />
                </svg>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Footer button ────────────────────────────────────────────────────────────
function FooterButton() {
  return (
    <div className="w-full" style={{ borderTop: "1px solid #dae3ec" }}>
      <div className="bg-[#eef2f7] p-[12px]">
        <div className="flex items-center justify-center rounded-[3px] h-[52px] w-full" style={{ background: "#1bc2f5", boxShadow: "0px 2px 2px 0px rgba(37,70,105,0.2)" }}>
          <div className="flex flex-col items-center gap-[4px]">
            <div className="size-[24px] relative">
              <svg className="absolute block size-full" fill="none" preserveAspectRatio="none" viewBox="0 0 20.25 19.3675">
                <path clipRule="evenodd" d={svgPaths.p2e341a71} fill="white" fillRule="evenodd" />
                <path d={svgPaths.p299d7d80} fill="white" />
              </svg>
            </div>
            <p className="font-['Noto_Sans_JP',sans-serif] text-white text-[11px] text-center leading-none" style={{ fontWeight: 700 }}>話を聞いてみたい</p>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Main App ─────────────────────────────────────────────────────────────────
export default function App() {
  const [isTriggered, setIsTriggered] = useState(true);
  const [isRecommendReady, setIsRecommendReady] = useState(false);
  const [countdown, setCountdown] = useState(DEMO_SECS);
  const [demoKey, setDemoKey] = useState(0);
  // モーダル表示中はヘッダー操作を封鎖
  const [modalIsOpen, setModalIsOpen] = useState(false);

  // カウントダウン：isTriggered になったら開始
  useEffect(() => {
    if (!isTriggered) return;

    setCountdown(DEMO_SECS);
    setIsRecommendReady(false);

    const readyTimer = setTimeout(() => setIsRecommendReady(true), DEMO_DELAY_MS);
    const countdownTimer = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) { clearInterval(countdownTimer); return 0; }
        return c - 1;
      });
    }, 1000);

    return () => { clearTimeout(readyTimer); clearInterval(countdownTimer); };
  }, [isTriggered, demoKey]);

  const handleTrigger = () => {
    if (isTriggered) return;
    setIsTriggered(true);
  };

  const handleReset = () => {
    setIsTriggered(false);
    setIsRecommendReady(false);
    setCountdown(DEMO_SECS);
    setDemoKey((k) => k + 1);
    // リセット後に自動再スタート
    setTimeout(() => setIsTriggered(true), 50);
  };

  return (
    <div className="min-h-screen bg-[#f3f6fa] flex flex-col items-center font-['Noto_Sans_JP',sans-serif]">
      {/* ── Demo control bar ─────────────────────────────────────────── */}
      <div
        className="w-full max-w-[420px] bg-white sticky top-0 z-[40] shadow-[0_2px_8px_rgba(0,0,0,0.08)]"
        style={{
          pointerEvents: modalIsOpen ? "none" : undefined,
          transform: modalIsOpen ? "translateY(-120%)" : "translateY(0)",
          transition: "transform 0.25s ease-in-out",
        }}
      >
        <div className="px-[12px] py-[8px]">
          <div className="flex items-center justify-between mb-[6px]">
            <p className="text-[#354659] text-[12px]" style={{ fontWeight: 700 }}>AI推薦理由UI（B案 + C案 マージ版）</p>
            {/* Demo countdown indicator */}
            <div className="flex items-center gap-[6px]">
              {!isTriggered ? (
                <div className="flex items-center gap-[4px] px-[8px] py-[3px] rounded-full" style={{ background: "rgba(153,153,153,0.1)" }}>
                  <span className="text-[#8999ab] text-[10px] whitespace-nowrap" style={{ fontWeight: 700 }}>待機中</span>
                </div>
              ) : !isRecommendReady ? (
                <div className="flex items-center gap-[5px] px-[8px] py-[3px] rounded-full" style={{ background: "rgba(192,205,255,0.35)" }}>
                  <div className="flex gap-[2px] items-center">
                    {[0, 1, 2].map((i) => (
                      <div key={i} className="w-[3px] h-[3px] rounded-full" style={{ background: "#7c5cbf", animation: `switcherDot 1.2s ${i * 0.2}s ease-in-out infinite` }} />
                    ))}
                  </div>
                  <span className="text-[#7c5cbf] text-[10px] whitespace-nowrap" style={{ fontWeight: 700 }}>
                    AI分析中 {countdown}s
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-[4px] px-[8px] py-[3px] rounded-full" style={{ background: "rgba(56,142,60,0.12)" }}>
                  <span className="text-[#388e3c] text-[10px] whitespace-nowrap" style={{ fontWeight: 700 }}>✓ AI推薦完了</span>
                </div>
              )}
              <button
                onClick={handleReset}
                className="text-[#8999ab] text-[10px] border-none bg-transparent cursor-pointer underline shrink-0"
              >
                リセット
              </button>
            </div>
          </div>
          {/* Note about demo */}
          <p className="text-[#8999ab] text-[10px]">
            ※デモ: 求人詳細に入ると自動でAI推薦理由の生成が始まります（10秒）
          </p>
        </div>
      </div>

      {/* ── Phone content ───────────────────────────────────────────────── */}
      <div className="w-full max-w-[375px] bg-white overflow-x-clip relative">
        <div
          className="sticky top-[96px] z-[30] bg-white"
          style={{ pointerEvents: modalIsOpen ? "none" : undefined }}
        >
          <StatusBar />
          <HeaderBar />
        </div>

        <div>
          <HeroSection />
          <JobTitle />
          <QuickCheckPanel />
          <TabNav />

          <div className="bg-[#f3f6fa]">
            <RecruitTitle />
            <div className="bg-white flex flex-col gap-[20px] px-[8px] pb-[24px]">
              <div className="flex flex-col gap-[20px]">
                <SectionTitle title="求人のポイント" />
                <SectionBody text="ここは「ポジションPRの内容」を表示します。私達はユーザーが抱えている課題をユーザーインタビューなどの定性情報と膨大なWebアクセスデータの定量情の両面から特定し、ディレクターやデザイナー、エンジニアが一体となって改善に取り組んでおります。\n\n現在、マネーフォワード クラウドは急成長を遂げており、その成長を支えるLPO部も拡大を続けています。" />
                <ReadMoreBtn />
              </div>
              <div className="flex flex-col gap-[20px]">
                <SectionTitle title="企業の特徴" />
                <SectionBody text="ここは「企業PR」の内容を表示します。「お金」とは、人生においてツールでしかありません。しかし「お金」とは、自身と家族の身を守るため、また夢を実現するために必要不可欠な存在でもあります。私たちは「お金と前向きに向き合い、可能性を広げる企業」を目指して事業を展開しています。" />
                <ReadMoreBtn />
              </div>
              <div className="flex flex-col gap-[20px]">
                <SectionTitle title="仕事内容" />
                <SectionBody text="＜映像配信サービスに関わる業務＞\n※映像に関する専門知識は不要！！\n\n当社では、映像配信サービスに関する業務を幅広く行っております。主には以下のような取引先企業の業務を行っていただくことになります。" />
                <ReadMoreBtn />
              </div>
              <div className="flex flex-col gap-[20px]">
                <SectionTitle title="休日休暇" />
                <div className="px-[4px]">
                  <div className="flex flex-col gap-[8px]">
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[16px]" style={{ fontWeight: 700 }}>休日</p>
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[14px] leading-[1.5]">土日休み</p>
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#596674] text-[12px] leading-[1.7]">補足内容テキストが入ります。補足内容テキストが入ります。</p>
                  </div>
                  <div className="h-px bg-[#bcc8d5] my-[24px]" />
                  <div className="flex flex-col gap-[8px]">
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[16px]" style={{ fontWeight: 700 }}>年間休日</p>
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[14px] leading-[1.5]">120日以上</p>
                  </div>
                </div>
              </div>
              <div className="flex flex-col gap-[20px]">
                <SectionTitle title="給与" />
                <div className="px-[4px]">
                  <div className="flex flex-col gap-[8px]">
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[16px]" style={{ fontWeight: 700 }}>入社時年収</p>
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[14px] leading-[1.5]">550〜750 万円</p>
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#6885a5] text-[12px] leading-[1.7]">年収イメージ</p>
                    <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[14px]">20代：500万円 / 30代：600万円 / 40代：700万円</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Sticky footer ─────────────────────────────────────────────── */}
        <div className="sticky bottom-0 z-30 relative">
          <div className="absolute bottom-full left-0 right-0">
            <RecommendMerged
              key={`merged-${demoKey}`}
              isTriggered={isTriggered}
              isReady={isRecommendReady}
              countdown={countdown}
              totalSeconds={DEMO_SECS}
              onTrigger={handleTrigger}
              onModalStateChange={setModalIsOpen}
            />
          </div>
          <FooterButton />
        </div>
      </div>

      <style>{`
        @keyframes switcherDot {
          0%, 80%, 100% { transform: scale(0.7); opacity: 0.4; }
          40% { transform: scale(1.2); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
