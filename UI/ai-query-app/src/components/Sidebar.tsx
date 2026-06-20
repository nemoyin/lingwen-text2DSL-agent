const menuItems = [
  { label: '三公经费', count: '1,247', active: true },
  { label: '政府采购', count: '3,892', active: false },
  { label: '惠农补贴', count: '5,610', active: false },
  { label: '民政救助', count: '2,103', active: false },
  { label: '工程项目', count: '879', active: false },
]

const historyItems = [
  { query: '2024年三公经费同比分析', time: '6分钟前 · 12条结果' },
  { query: '高标准农田招投标异常分析', time: '2小时前 · 8条结果' },
  { query: '近三年惠农补贴发放趋势', time: '昨天 · 24条结果' },
]

function Sidebar() {
  return (
    <aside className="w-[260px] bg-card flex flex-col gap-1 flex-shrink-0 overflow-y-auto" style={{ padding: '16px 12px' }}>
      {/* 监督数据域 */}
      <span className="text-muted-fg text-[11px] font-bold font-[Noto_Sans_SC] leading-4 block" style={{ paddingBottom: 0 }}>
        监督数据域
      </span>

      {menuItems.map((item) => (
        <div
          key={item.label}
          className={`flex items-center gap-2 rounded-[2px] h-9 w-full ${item.active ? 'bg-[#F1F5F9]' : ''}`}
          style={{ padding: '8px 10px' }}
        >
          <div
            className={`w-4 h-4 rounded-[2px] flex-shrink-0 ${item.active ? 'bg-accent' : 'bg-border'}`}
          />
          <span
            className={`text-[13px] font-[Noto_Sans_SC] flex-1 ${item.active ? 'text-primary font-medium' : 'text-primary-light font-normal'}`}
          >
            {item.label}
          </span>
          <span className="text-muted-fg text-[11px] font-normal font-[Noto_Sans_SC]">
            {item.count}
          </span>
        </div>
      ))}

      {/* 分隔线 */}
      <div className="w-full h-px bg-border flex-shrink-0" />

      {/* 查询历史 */}
      <span className="text-muted-fg text-[11px] font-bold font-[Noto_Sans_SC] leading-4 block pb-0">
        查询历史
      </span>

      {historyItems.map((item) => (
        <div key={item.query} className="flex flex-col gap-0.5 rounded-[2px] w-full" style={{ padding: '6px 8px' }}>
          <span className="text-primary-light text-xs font-normal font-[Noto_Sans_SC] leading-[17px]">
            {item.query}
          </span>
          <span className="text-[#94A3B8] text-[10px] font-normal font-[Noto_Sans_SC] leading-[14px]">
            {item.time}
          </span>
        </div>
      ))}
    </aside>
  )
}

export default Sidebar
