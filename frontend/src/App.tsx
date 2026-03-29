import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import PatientDetail from './pages/PatientDetail'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/patient/:patientId" element={<PatientDetail />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
