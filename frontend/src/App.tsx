import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { useEffect } from 'react'
import { Layout } from './components/Layout'
import Dashboard from './pages/Dashboard'
import Query from './pages/Query'
import Monitor from './pages/Monitor'
import Connections from './pages/Connections'
import Chat from './pages/Chat'
import Templates from './pages/Templates'

function App() {
  const location = useLocation()

  // 记录页面访问
  useEffect(() => {
    const recordVisit = async () => {
      try {
        await fetch('/api/visit', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ page: location.pathname })
        })
      } catch (e) {
        console.error('记录访问失败:', e)
      }
    }
    recordVisit()
  }, [location])

  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="query" element={<Query />} />
        <Route path="monitor" element={<Monitor />} />
        <Route path="connections" element={<Connections />} />
        <Route path="templates" element={<Templates />} />
        <Route path="chat" element={<Chat />} />
      </Route>
    </Routes>
  )
}

export default App
