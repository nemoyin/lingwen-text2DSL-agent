function Header() {
  return (
    <header className="h-[52px] w-full bg-primary flex items-center justify-between flex-shrink-0" style={{ padding: '0 20px' }}>
      {/* 左侧品牌区 */}
      <div className="flex items-center gap-[10px]">
        <div className="w-7 h-7 bg-accent rounded-[2px] flex items-center justify-center">
          <span className="text-white text-base font-bold font-[Noto_Sans_SC] leading-none">问</span>
        </div>
        <span className="text-white text-base font-bold font-[Noto_Sans_SC]">天府一网监</span>
        <div className="w-px h-5 bg-primary-light" />
        <span className="text-[#94A3B8] text-[13px] font-normal font-[Noto_Sans_SC]">AI智能问数平台</span>
      </div>

      {/* 右侧操作区 */}
      <div className="flex items-center gap-3">
        <span className="text-[#94A3B8] text-xs font-medium font-[Noto_Sans_SC]">数据源</span>
        <div className="bg-primary-light rounded-[2px] flex items-center gap-1.5" style={{ padding: '4px 10px' }}>
          <span className="text-[#E2E8F0] text-xs font-medium font-[Noto_Sans_SC]">天府监督数据库</span>
          <span className="text-muted-fg text-[10px] leading-none">▾</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 bg-accent rounded-[14px] flex items-center justify-center">
            <span className="text-white text-xs font-semibold font-[Noto_Sans_SC]">纪</span>
          </div>
          <span className="text-[#E2E8F0] text-xs font-medium font-[Noto_Sans_SC]">纪检监督员</span>
        </div>
      </div>
    </header>
  )
}

export default Header
