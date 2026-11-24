import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Upload from './pages/Upload'
import Timeline from './pages/Timeline'
import Stores from './pages/Stores'
import Products from './pages/Products'
import Scans from './pages/Scans'
import { ToastProvider } from './hooks/useToast'

function App() {
  return (
    <ToastProvider>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/timeline" element={<Timeline />} />
          <Route path="/stores" element={<Stores />} />
          <Route path="/products" element={<Products />} />
          <Route path="/scans" element={<Scans />} />
        </Routes>
      </Layout>
    </ToastProvider>
  )
}

export default App
