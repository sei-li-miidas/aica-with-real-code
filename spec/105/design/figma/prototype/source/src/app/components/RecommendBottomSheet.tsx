import { useState } from "react";
import { Sparkles, X, ThumbsUp, ThumbsDown, Target, Heart, TrendingUp } from "lucide-react";

const insights = [
  {
    icon: Target,
    title: "スキルマッチ",
    score: 92,
    detail: "React, TypeScript, Webフロントエンド開発の経験が高く評価されています",
  },
  {
    icon: Heart,
    title: "カルチャーフィット",
    score: 88,
    detail: "チームワーク重視・成長環境を求めるあなたの志向に合致しています",
  },
  {
    icon: TrendingUp,
    title: "キャリアパス",
    score: 95,
    detail: "エンジニアとしてのキャリアアップが見込める環境です",
  },
];

export function RecommendBottomSheet() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Trigger button */}
      <button
        onClick={() => setIsOpen(true)}
        className="w-full flex items-center gap-[10px] bg-gradient-to-r from-[#1bc2f5]/10 to-[#6366f1]/10 rounded-[12px] px-[14px] py-[12px] cursor-pointer border border-[#1bc2f5]/30"
      >
        <div className="w-[36px] h-[36px] rounded-full bg-gradient-to-br from-[#1bc2f5] to-[#6366f1] flex items-center justify-center">
          <Sparkles className="w-[18px] h-[18px] text-white" />
        </div>
        <div className="flex-1 text-left">
          <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[13px]" style={{ fontWeight: 700 }}>
            AIがあなたに推薦しています
          </p>
          <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[11px]">
            タップして推薦理由を確認
          </p>
        </div>
        <div className="bg-[#1bc2f5] text-white px-[10px] py-[4px] rounded-full">
          <span className="font-['Noto_Sans_JP',sans-serif] text-[12px]" style={{ fontWeight: 700 }}>92%</span>
        </div>
      </button>

      {/* Overlay */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-end justify-center">
          <div className="absolute inset-0 bg-black/40" onClick={() => setIsOpen(false)} />
          
          {/* Sheet */}
          <div className="relative w-full max-w-[400px] bg-white rounded-t-[20px] max-h-[80vh] overflow-auto animate-slide-up">
            {/* Handle */}
            <div className="flex justify-center pt-[10px] pb-[6px]">
              <div className="w-[40px] h-[4px] bg-[#dae3ec] rounded-full" />
            </div>

            {/* Close */}
            <button
              onClick={() => setIsOpen(false)}
              className="absolute top-[14px] right-[14px] w-[28px] h-[28px] rounded-full bg-[#f3f6fa] flex items-center justify-center cursor-pointer border-none"
            >
              <X className="w-[16px] h-[16px] text-[#6c85a1]" />
            </button>

            <div className="px-[20px] pb-[32px]">
              {/* Header */}
              <div className="text-center mb-[20px]">
                <div className="w-[56px] h-[56px] rounded-full bg-gradient-to-br from-[#1bc2f5] to-[#6366f1] flex items-center justify-center mx-auto mb-[10px]">
                  <Sparkles className="w-[28px] h-[28px] text-white" />
                </div>
                <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[16px]" style={{ fontWeight: 700 }}>
                  AI推薦レポート
                </p>
                <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[12px] mt-[4px]">
                  総合マッチ度
                </p>
                <p className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[36px] mt-[4px]" style={{ fontWeight: 700 }}>
                  92<span className="text-[16px] text-[#6c85a1]">%</span>
                </p>
              </div>

              {/* Insights */}
              <div className="flex flex-col gap-[14px] mb-[24px]">
                {insights.map((item) => {
                  const Icon = item.icon;
                  return (
                    <div key={item.title} className="bg-[#f8fafc] rounded-[12px] p-[14px]">
                      <div className="flex items-center justify-between mb-[8px]">
                        <div className="flex items-center gap-[8px]">
                          <Icon className="w-[18px] h-[18px] text-[#1bc2f5]" />
                          <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[13px]" style={{ fontWeight: 700 }}>
                            {item.title}
                          </span>
                        </div>
                        <span className="font-['Noto_Sans_JP',sans-serif] text-[#1bc2f5] text-[14px]" style={{ fontWeight: 700 }}>
                          {item.score}%
                        </span>
                      </div>
                      <div className="w-full h-[4px] bg-[#e0e8f2] rounded-full mb-[8px] overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-[#1bc2f5] to-[#34d399] rounded-full"
                          style={{ width: `${item.score}%` }}
                        />
                      </div>
                      <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[12px] leading-[1.5]">
                        {item.detail}
                      </p>
                    </div>
                  );
                })}
              </div>

              {/* Feedback */}
              <div className="bg-[#f3f6fa] rounded-[12px] p-[14px] text-center">
                <p className="font-['Noto_Sans_JP',sans-serif] text-[#6c85a1] text-[12px] mb-[10px]">
                  この推薦は参考になりましたか？
                </p>
                <div className="flex items-center justify-center gap-[12px]">
                  <button className="flex items-center gap-[4px] bg-white border border-[#dae3ec] rounded-full px-[16px] py-[8px] cursor-pointer">
                    <ThumbsUp className="w-[14px] h-[14px] text-[#1bc2f5]" />
                    <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px]">はい</span>
                  </button>
                  <button className="flex items-center gap-[4px] bg-white border border-[#dae3ec] rounded-full px-[16px] py-[8px] cursor-pointer">
                    <ThumbsDown className="w-[14px] h-[14px] text-[#8999ab]" />
                    <span className="font-['Noto_Sans_JP',sans-serif] text-[#354659] text-[12px]">いいえ</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); }
          to { transform: translateY(0); }
        }
        .animate-slide-up {
          animation: slideUp 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
