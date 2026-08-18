import { Bot, TrendingUp } from "lucide-react";

const matchItems = [
  { label: "スキル適合", score: 92, color: "#1bc2f5" },
  { label: "働き方", score: 88, color: "#34d399" },
  { label: "年収", score: 85, color: "#a78bfa" },
  { label: "成長環境", score: 95, color: "#f59e0b" },
];

const tags = ["React経験者歓迎", "キャリアチェンジOK", "年休120日+", "エンジニア育成環境"];

export function RecommendCard() {
  return (
    <div className="w-full bg-white rounded-[16px] shadow-[0_2px_16px_rgba(0,0,0,0.08)] overflow-hidden">
      {/* Top accent */}
      <div className="h-[4px] bg-gradient-to-r from-[#1bc2f5] via-[#a78bfa] to-[#34d399]" />

      <div className="p-[16px]">
        {/* Header */}
        <div className="flex items-center gap-[10px] mb-[16px]">
          <div className="w-[40px] h-[40px] rounded-full bg-gradient-to-br from-[#1bc2f5] to-[#0ea5e9] flex items-center justify-center">
            <Bot className="w-[22px] h-[22px] text-white" />
          </div>
          <div className="flex-1">
            <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[14px]" style={{ fontWeight: 700 }}>
              AI推薦スコア
            </p>
            <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[11px]">
              あなたのプロフィールを分析しました
            </p>
          </div>
          <div className="flex items-center gap-[4px]">
            <TrendingUp className="w-[16px] h-[16px] text-[#34d399]" />
            <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[24px]" style={{ fontWeight: 700 }}>
              92
            </span>
            <span className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[12px]">点</span>
          </div>
        </div>

        {/* Score bars */}
        <div className="flex flex-col gap-[10px] mb-[16px]">
          {matchItems.map((item) => (
            <div key={item.label} className="flex items-center gap-[8px]">
              <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px] w-[64px] shrink-0">
                {item.label}
              </p>
              <div className="flex-1 h-[6px] bg-[#f0f4f8] rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-500"
                  style={{ width: `${item.score}%`, backgroundColor: item.color }}
                />
              </div>
              <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px] w-[30px] text-right" style={{ fontWeight: 700 }}>
                {item.score}%
              </span>
            </div>
          ))}
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-[6px]">
          {tags.map((tag) => (
            <span
              key={tag}
              className="font-['Noto_Sans_JP',sans-serif] text-[11px] text-[#1bc2f5] bg-[#e8f7fd] px-[10px] py-[4px] rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
