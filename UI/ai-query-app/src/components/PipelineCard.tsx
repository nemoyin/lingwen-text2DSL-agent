const steps = [
  { label: '意图识别', active: true },
  { label: 'Schema匹配', active: false },
  { label: 'Few-shot', active: false },
  { label: 'SQL生成', active: false },
  { label: 'SQL审计', active: false },
  { label: '执行', active: false },
  { label: 'AI总结', active: false },
]

function PipelineCard() {
  return (
    <div className="bg-card rounded-lg flex items-center shadow-[0_2px_8px_rgba(0,0,0,0.06)]" style={{ padding: '10px 16px' }}>
      <span className="text-muted-fg text-[11px] font-bold font-[Noto_Sans_SC] mr-0 flex-shrink-0">
        查询管线
      </span>

      {steps.map((step, i) => (
        <span key={step.label} className="contents">
          {i > 0 && (
            <span className="text-[#CBD5E1] text-[10px] mx-0">→</span>
          )}
          <div
            className={`flex items-center gap-1 rounded-[2px] ${step.active ? 'bg-accent' : 'bg-muted'}`}
            style={{ padding: '4px 8px' }}
          >
            <div className={`w-1.5 h-1.5 rounded-full ${step.active ? 'bg-white' : 'bg-muted-fg'}`} />
            <span
              className={`text-[10px] font-[Noto_Sans_SC] whitespace-nowrap ${step.active ? 'text-white font-medium' : 'text-muted-fg font-normal'}`}
            >
              {step.label}
            </span>
          </div>
        </span>
      ))}
    </div>
  )
}

export default PipelineCard
