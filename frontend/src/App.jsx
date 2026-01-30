import React from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import Layout from './components/Layout/Layout'
import Login from './pages/Login'
import Empresas from './pages/Empresas'
import Dashboard from './pages/Dashboard'
import Segmentos from './pages/Segmentos'
import EmpresasPorSegmento from './pages/EmpresasPorSegmento'
import ImportarPlanilha from './pages/ImportarPlanilha'
import OperadorPendencias from './pages/OperadorPendencias'
import SupervisorPendencias from './pages/SupervisorPendencias'
import RelatorioMensal from './pages/RelatorioMensal'
import GerenciarUsuarios from './pages/admin/GerenciarUsuarios'
import GerenciarSegmentos from './pages/admin/GerenciarSegmentos'
import GerenciarEmpresas from './pages/admin/GerenciarEmpresas'
import NovaPendencia from './pages/NovaPendencia'
import VerPendencia from './pages/VerPendencia'
import EditarPendencia from './pages/EditarPendencia'
import LogsRecentes from './pages/LogsRecentes'
import HistoricoImportacoes from './pages/HistoricoImportacoes'
import PendenciasResolvidas from './pages/PendenciasResolvidas'
import PendenciasList from './pages/PendenciasList'
import LogsPendencia from './pages/LogsPendencia'

function PrivateRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  
  if (loading) {
    return <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '100vh' }}>
      <div className="spinner-border text-primary" role="status">
        <span className="visually-hidden">Carregando...</span>
      </div>
    </div>
  }
  
  return isAuthenticated ? children : <Navigate to="/login" />
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      
      <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
        <Route index element={<Navigate to="/empresas" replace />} />
        <Route path="empresas" element={<Empresas />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="segmentos" element={<Segmentos />} />
        <Route path="segmento/:id" element={<EmpresasPorSegmento />} />
        <Route path="importar-planilha" element={<ImportarPlanilha />} />
        <Route path="operador" element={<OperadorPendencias />} />
        <Route path="supervisor" element={<SupervisorPendencias />} />
        <Route path="relatorio-mensal" element={<RelatorioMensal />} />
        <Route path="gerenciar/usuarios" element={<GerenciarUsuarios />} />
        <Route path="gerenciar/segmentos" element={<GerenciarSegmentos />} />
        <Route path="gerenciar/empresas" element={<GerenciarEmpresas />} />
        <Route path="nova-pendencia" element={<NovaPendencia />} />
        <Route path="pendencia/:id" element={<VerPendencia />} />
        <Route path="pendencia/:id/editar" element={<EditarPendencia />} />
        <Route path="logs-recentes" element={<LogsRecentes />} />
        <Route path="historico-importacoes" element={<HistoricoImportacoes />} />
        <Route path="pendencias-resolvidas" element={<PendenciasResolvidas />} />
        <Route path="pendencias" element={<PendenciasList />} />
        <Route path="pendencia/:id/logs" element={<LogsPendencia />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}

export default App

