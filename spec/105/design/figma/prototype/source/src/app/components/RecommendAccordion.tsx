import { useState } from "react";
import { Zap, Briefcase, Clock, Wallet, ChevronRight } from "lucide-react";

const categories = [
  {
    icon: Briefcase,
    title: "スキル・経験",
    color: "#1bc2f5",
    bgColor: "#e8f7fd",
    reasons: ["React / TypeScript の実務経験がマッチ", "キャリアチェンジ歓迎で挑戦しやすい環境"],
  },
  {
    icon: Clock,
    title: "働き方・環境",
    color: "#34d399",
    bgColor: "#ecfdf5",
    reasons: ["週休2日制・年間休日120日以上", "平均残業月30時間以内", "オンライン面接対応"],
  },
  {
    icon: Wallet,
    title: "待遇・報酬",
    color: "#a78bfa",
    bgColor: "#f3f0ff",
    reasons: ["希望年収レンジ（550〜750万円）にマッチ", "充実した福利厚生"],
  },
];

export function RecommendAccordion() {
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  return (
    <div className="w-full">
      {/* Header */}
      <div className="flex items-center gap-[8px] mb-[12px]">
        <div className="w-[28px] h-[28px] rounded-[8px] bg-gradient-to-br from-[#1bc2f5] to-[#0ea5e9] flex items-center justify-center">
          <Zap className="w-[16px] h-[16px] text-white" />
        </div>
        <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[15px]" style={{ fontWeight: 700 }}>
          AIがこの求人を推薦する理由
        </p>
      </div>

      {/* Accordion items */}
      <div className="flex flex-col gap-[8px]">
        {categories.map((cat, i) => {
          const isOpen = openIndex === i;
          const Icon = cat.icon;
          return (
            <div
              key={cat.title}
              className="rounded-[10px] overflow-hidden transition-all duration-200"
              style={{
                border: `1px solid ${isOpen ? cat.color : "#e0e8f2"}`,
                backgroundColor: isOpen ? cat.bgColor : "white",
              }}
            >
              <button
                className="w-full flex items-center gap-[10px] px-[14px] py-[12px] cursor-pointer bg-transparent border-none"
                onClick={() => setOpenIndex(isOpen ? null : i)}
              >
                <div
                  className="w-[32px] h-[32px] rounded-full flex items-center justify-center shrink-0"
                  style={{ backgroundColor: isOpen ? cat.color : cat.bgColor }}
                >
                  <Icon className="w-[16px] h-[16px]" style={{ color: isOpen ? "white" : cat.color }} />
                </div>
                <span
                  className="font-['Noto_Sans_JP',sans-serif] text-[13px] flex-1 text-left"
                  style={{ color: "#354659", fontWeight: 700 }}
                >
                  {cat.title}
                </span>
                <ChevronRight
                  className="w-[16px] h-[16px] text-[#8999ab] transition-transform duration-200"
                  style={{ transform: isOpen ? "rotate(90deg)" : "rotate(0deg)" }}
                />
              </button>

              <div
                className="overflow-hidden transition-all duration-200"
                style={{ maxHeight: isOpen ? "200px" : "0px" }}
              >
                <div className="px-[14px] pb-[14px] pl-[56px]">
                  <ul className="flex flex-col gap-[6px] m-0 p-0 list-none">
                    {cat.reasons.map((r) => (
                      <li key={r} className="flex items-start gap-[6px]">
                        <span
                          className="w-[5px] h-[5px] rounded-full shrink-0 mt-[6px]"
                          style={{ backgroundColor: cat.color }}
                        />
                        <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px] leading-[1.6]">
                          {r}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
