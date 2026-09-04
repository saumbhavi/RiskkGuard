import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import ModelMetrics from './pages/ModelMetrics'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/metrics" element={<ModelMetrics />} />
      </Route>
    </Routes>
  )
}
