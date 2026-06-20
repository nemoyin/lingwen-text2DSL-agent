import { useState } from 'react'

const kpiData = [
  { label: '返回行数', value: '1,247' },
  { label: '查询耗时', value: '847ms' },
  { label: 'Token消耗', value: '2,341' },
  { label: '数据源', value: '三公经费库' },
]

const tabs = ['图表', '数据表格', 'AI分析']

const chartTypes = ['柱状图', '折线图', '饼图']

const tableHeaders = ['排名', '单位名称', '因公出国', '公务用车', '公务接待', '合计(万元)']

const tableData = [
  { rank: '1', name: '市教育局', abroad: '48.52', car: '126.30', reception: '35.18', total: '210.00' },
  { rank: '2', name: '市公安局', abroad: '32.14', car: '98.67', reception: '28.43', total: '159.24' },
  { rank: '3', name: '市卫健委', abroad: '25.80', car: '87.42', reception: '22.66', total: '135.88' },
]

// Bar chart data - heights from the design (180, 158, 142, 130, 118, 104, 92, 78, 65, 52)
const barData = [
  { value: 180, color: 'bg-primary' },
  { value: 158, color: 'bg-primary' },
  { value: 142, color: 'bg-primary' },
  { value: 130, color: 'bg-accent' },
  { value: 118, color: 'bg-accent' },
  { value: 104, color: 'bg-primary-muted' },
  { value: 92, color: 'bg-primary-muted' },
  { value: 78, color: 'bg-muted-fg' },
  { value: 65, color: 'bg-muted-fg' },
  { value: 52, color: 'bg-[#94A3B8]' },
]

function ResultCard() {
  const [activeTab, setActiveTab] = useState(0)
  const [activeChartType, setActiveChartType] = useState(0)

  return (
    <div className="bg-card rounded-lg shadow-[0_2px_8px_rgba(0,0,0,0.06)] flex flex-col flex-1 min-h-0 overflow-hidden">
      {/* ========== KPI 行 ========== */}
      <div className="flex gap-6 items-center flex-shrink-0" style={{ padding: '12px 20px' }}>
        {kpiData.map((kpi) => (
          <div key={kpi.label} className="flex flex-col gap-0.5 flex-1">
            <span className="text-muted-fg text-[11px] font-normal font-[Noto_Sans_SC] leading-4">
              {kpi.label}
            </span>
            <span className="text-primary text-xl font-bold font-[Noto_Sans_SC] leading-[26px]">
              {kpi.value}
            </span>
          </div>
        ))}
      </div>

      {/* 分隔线 */}
      <div className="w-full h-px bg-border flex-shrink-0" />

      {/* ========== Tab 栏 ========== */}
      <div className="flex flex-shrink-0" style={{ padding: '0 20px' }}>
        {tabs.map((tab, i) => (
          <div
            key={tab}
            className={`flex items-center cursor-pointer border-b-2 transition-colors ${activeTab === i ? 'border-accent' : 'border-transparent'}`}
            style={{ padding: '10px 16px' }}
            onClick={() => setActiveTab(i)}
          >
            <span
              className={`text-[13px] font-[Noto_Sans_SC] ${activeTab === i ? 'text-primary font-semibold' : 'text-muted-fg font-normal'}`}
            >
              {tab}
            </span>
          </div>
        ))}
      </div>

      {/* ========== 图表区域 ========== */}
      <div className="flex flex-col gap-3 flex-shrink-0" style={{ padding: '16px 20px' }}>
        {/* 图表标题 + 类型切换 */}
        <div className="flex justify-between items-center">
          <span className="text-primary text-sm font-semibold font-[Noto_Sans_SC]">
            2024年度三公经费支出排行（前十单位）
          </span>
          <div className="bg-[#F1F5F9] rounded-[2px] flex items-center" style={{ padding: 2, gap: 2 }}>
            {chartTypes.map((ct, i) => (
              <div
                key={ct}
                className={`rounded-[2px] cursor-pointer flex items-center transition-colors ${activeChartType === i ? 'bg-accent' : ''}`}
                style={{ padding: '4px 10px' }}
                onClick={() => setActiveChartType(i)}
              >
                <span
                  className={`text-[11px] font-[Noto_Sans_SC] whitespace-nowrap ${activeChartType === i ? 'text-white font-medium' : 'text-muted-fg font-normal'}`}
                >
                  {ct}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 图表 Canvas - 柱状图 */}
        <div className="h-[240px] bg-bg rounded-[2px] flex items-end" style={{ padding: '20px 20px 0 20px', gap: 8 }}>
          {barData.map((bar, i) => (
            <div
              key={i}
              className={`flex-1 rounded-t-[2px] ${bar.color} transition-all duration-300`}
              style={{ height: `${bar.value}px` }}
            />
          ))}
        </div>
      </div>

      {/* ========== 表格分隔线 ========== */}
      <div className="w-full h-px bg-border flex-shrink-0" />

      {/* ========== 数据表格 ========== */}
      <div className="flex flex-col flex-shrink-0" style={{ padding: '0 20px' }}>
        {/* 表头 */}
        <div className="flex bg-bg h-9 items-center">
          {tableHeaders.map((h, i) => (
            <div
              key={h}
              className={`flex items-center ${h === '排名' ? 'w-12' : h === '合计(万元)' ? 'w-[100px]' : 'flex-1'}`}
              style={{ padding: '8px 12px' }}
            >
              <span className="text-muted-fg text-[11px] font-semibold font-[Noto_Sans_SC]">{h}</span>
            </div>
          ))}
        </div>

        {/* 数据行 */}
        {tableData.map((row, ri) => (
          <div
            key={row.rank}
            className={`flex h-9 items-center ${ri % 2 === 1 ? 'bg-bg' : ''}`}
          >
            <div className="w-12 flex items-center" style={{ padding: '8px 12px' }}>
              <span className="text-primary text-xs font-semibold font-[Noto_Sans_SC]">{row.rank}</span>
            </div>
            <div className="flex-1 flex items-center" style={{ padding: '8px 12px' }}>
              <span className="text-foreground text-xs font-normal font-[Noto_Sans_SC]">{row.name}</span>
            </div>
            <div className="flex-1 flex items-center" style={{ padding: '8px 12px' }}>
              <span className="text-primary-light text-xs font-normal font-[Noto_Sans_SC]">{row.abroad}</span>
            </div>
            <div className="flex-1 flex items-center" style={{ padding: '8px 12px' }}>
              <span className="text-primary-light text-xs font-normal font-[Noto_Sans_SC]">{row.car}</span>
            </div>
            <div className="flex-1 flex items-center" style={{ padding: '8px 12px' }}>
              <span className="text-primary-light text-xs font-normal font-[Noto_Sans_SC]">{row.reception}</span>
            </div>
            <div className="w-[100px] flex items-center" style={{ padding: '8px 12px' }}>
              <span className="text-primary text-xs font-semibold font-[Noto_Sans_SC]">{row.total}</span>
            </div>
          </div>
        ))}

        {/* 截断提示 */}
        <div className="flex bg-[#FEF3C7] rounded-[2px] items-center flex-shrink-0" style={{ padding: '8px 12px', marginTop: 0 }}>
          <span className="text-[#92400E] text-[11px] font-normal font-[Noto_Sans_SC]">
            ⚠ 数据已截断：共1,247条记录，图表展示前50行，表格展示前50行
          </span>
        </div>
      </div>

      {/* ========== 操作栏分隔线 ========== */}
      <div className="w-full h-px bg-border flex-shrink-0" />

      {/* ========== 操作栏 ========== */}
      <div className="flex justify-between items-center flex-shrink-0" style={{ padding: '10px 20px' }}>
        <div className="flex gap-2">
          {/* CSV 按钮 */}
          <button className="border border-border rounded-[2px] flex items-center gap-1.5 cursor-pointer hover:bg-muted transition-colors" style={{ padding: '6px 14px' }}>
            <span className="text-xs">📥</span>
            <span className="text-primary-light text-xs font-medium font-[Noto_Sans_SC]">导出CSV</span>
          </button>

          {/* Excel 按钮 */}
          <button className="bg-accent rounded-[2px] flex items-center gap-1.5 cursor-pointer hover:opacity-90 transition-opacity" style={{ padding: '6px 14px' }}>
            <span className="text-xs">📊</span>
            <span className="text-white text-xs font-medium font-[Noto_Sans_SC]">导出Excel</span>
          </button>
        </div>

        <span className="text-[#94A3B8] text-[11px] font-normal font-[Noto_Sans_SC]">
          耗时847ms · Token 2,341 · 数据源: 三公经费库
        </span>
      </div>
    </div>
  )
}

export default ResultCard
