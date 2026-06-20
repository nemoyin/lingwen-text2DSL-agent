import Header from './components/Header'
import Sidebar from './components/Sidebar'
import QueryCard from './components/QueryCard'
import PipelineCard from './components/PipelineCard'
import ResultCard from './components/ResultCard'

function App() {
  return (
    <div className="w-screen h-screen flex flex-col bg-bg overflow-hidden">
      <Header />

      {/* Body: Sidebar + Main Content */}
      <div className="flex flex-1 min-h-0">
        <Sidebar />

        {/* Main Content */}
        <main className="flex-1 flex flex-col gap-3 min-w-0 overflow-y-auto" style={{ padding: '16px 20px' }}>
          <QueryCard />
          <PipelineCard />
          <ResultCard />
        </main>
      </div>
    </div>
  )
}

export default App
