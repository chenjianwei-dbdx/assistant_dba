import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import Dashboard from './pages/Dashboard'
import Query from './pages/Query'
import Monitor from './pages/Monitor'
import Connections from './pages/Connections'
import Chat from './pages/Chat'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="query" element={<Query />} />
        <Route path="monitor" element={<Monitor />} />
        <Route path="connections" element={<Connections />} />
        <Route path="chat" element={<Chat />} />
      </Route>
    </Routes>
  )
}

export default App
