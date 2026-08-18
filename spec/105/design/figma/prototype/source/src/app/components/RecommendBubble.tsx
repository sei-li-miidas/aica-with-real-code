import { Sparkles } from "lucide-react";

const reasons = [
  "あなたのReact・TypeScript経験とマッチ度が高いです",
  "キャリアチェンジ歓迎で、未経験分野への挑戦をサポートする環境です",
  "週休2日制・年間休日120日以上で、ワークライフバランスも良好です",
];

export function RecommendBubble() {
  return (
    <div className="w-full flex gap-[10px] items-start">
      {/* AI Avatar */}
      <div className="shrink-0">
        <div className="w-[44px] h-[44px] rounded-full bg-gradient-to-br from-[#1bc2f5] to-[#6366f1] flex items-center justify-center shadow-[0_2px_8px_rgba(27,194,245,0.3)]">
          <Sparkles className="w-[22px] h-[22px] text-white" />
        </div>
        <p className="font-['Noto_Sans_JP',sans-serif] text-[10px] text-[#6c85a1] text-center mt-[4px]">AI</p>
      </div>

      {/* Speech bubble */}
      <div className="flex-1 relative">
        {/* Bubble arrow */}
        <div
          className="absolute left-[-6px] top-[14px] w-0 h-0"
          style={{
            borderTop: "6px solid transparent",
            borderBottom: "6px solid transparent",
            borderRight: "6px solid #f0f7ff",
          }}
        />

        <div className="bg-[#f0f7ff] rounded-[12px] rounded-tl-[4px] p-[14px]">
          <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[13px] mb-[10px]" style={{ fontWeight: 700 }}>
            この求人をおすすめする理由
          </p>

          <div className="flex flex-col gap-[10px]">
            {reasons.map((reason, i) => (
              <div key={i} className="flex items-start gap-[8px]">
                <span className="font-['Noto_Sans_JP',sans-serif] text-[11px] text-white bg-[#1bc2f5] rounded-full w-[20px] h-[20px] flex items-center justify-center shrink-0 mt-[1px]" style={{ fontWeight: 700 }}>
                  {i + 1}
                </span>
                <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px] leading-[1.6]">{reason}</p>
              </div>
            ))}
          </div>

          <div className="mt-[12px] pt-[10px] border-t border-[#d8e8f5]">
            <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[11px] leading-[1.5]">
              あなたの経歴・希望条件をもとに、AIが最適な求人を選定しています
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
