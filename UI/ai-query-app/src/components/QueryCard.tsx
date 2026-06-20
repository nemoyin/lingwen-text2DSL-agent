function QueryCard() {
  return (
    <div className="bg-card rounded-lg flex flex-col gap-3 shadow-[0_2px_8px_rgba(0,0,0,0.06)]" style={{ padding: '16px 20px' }}>
      {/* 标题 */}
      <span className="text-primary text-sm font-bold font-[Noto_Sans_SC]">
        灵问 · 智能Text-to-SQL引擎
      </span>

      {/* 输入行 */}
      <div className="flex gap-2 w-full">
        <div className="flex-1 bg-bg rounded-[2px] flex items-center gap-2 border border-border" style={{ padding: '10px 14px' }}>
          <svg className="w-[14px] h-[14px] flex-shrink-0 text-muted-fg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
          <span className="text-[#94A3B8] text-[13px] font-normal font-[Noto_Sans_SC] flex-1">
            输入自然语言查询，例如：查询2024年度三公经费支出前十单位
          </span>
        </div>
        <button className="bg-primary rounded-[2px] flex items-center justify-center flex-shrink-0" style={{ padding: '10px 20px' }}>
          <span className="text-white text-[13px] font-semibold font-[Noto_Sans_SC]">提交查询</span>
        </button>
      </div>
    </div>
  )
}

export default QueryCard
