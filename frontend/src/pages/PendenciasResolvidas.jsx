import React, { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function PendenciasResolvidas() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const { user } = useAuth()
  
  const empresa = searchParams.get('empresa') || ''
  const tipo = searchParams.get('tipo_pendencia') || ''
  const dataInicio = searchParams.get('data_inicio') || ''
  const dataFim = searchParams.get('data_fim') || ''
  const [expandedLogs, setExpandedLogs] = useState({})

  // Buscar empresas disponíveis
  const { data: empresasData } = useQuery(
    ['empresas'],
    async () => {
      const response = await api.get('/api/empresas')
      return response.data
    },
    { enabled: !!user }
  )

  // Buscar tipos de pendência
  const { data: tiposData } = useQuery(
    ['tipos-pendencia'],
    async () => {
      const response = await api.get('/api/tipos-pendencia')
      return response.data
    },
    { enabled: !!user }
  )

  // Buscar pendências resolvidas
  const { data, isLoading } = useQuery(
    ['resolvidas', empresa, tipo, dataInicio, dataFim],
    async () => {
      const params = new URLSearchParams()
      if (empresa) params.append('empresa', empresa)
      if (tipo) params.append('tipo_pendencia', tipo)
      if (dataInicio) params.append('data_inicio', dataInicio)
      if (dataFim) params.append('data_fim', dataFim)
      params.append('status', 'RESOLVIDA')
      
      const response = await api.get(`/api/pendencias?${params.toString()}`)
      return response.data
    },
    { enabled: !!user }
  )

  const handleFilterChange = (key, value) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(key, value)
    } else {
      newParams.delete(key)
    }
    setSearchParams(newParams)
  }

  const toggleLogs = (pendenciaId) => {
    setExpandedLogs(prev => ({
      ...prev,
      [pendenciaId]: !prev[pendenciaId]
    }))
  }

  const handleExportarExcel = async () => {
    try {
      const params = new URLSearchParams()
      if (empresa) params.append('empresa', empresa)
      if (tipo) params.append('tipo_pendencia', tipo)
      params.append('status', 'RESOLVIDA')
      if (dataInicio) params.append('data_inicio', dataInicio)
      if (dataFim) params.append('data_fim', dataFim)
      
      window.open(`/api/exportar-pendencias-excel?${params.toString()}`, '_blank')
    } catch (error) {
      console.error('Erro ao exportar:', error)
      alert('Erro ao exportar pendências. Tente novamente.')
    }
  }

  if (!['adm', 'supervisor', 'cliente_supervisor'].includes(user?.tipo)) {
    return (
      <div className="container mt-4">
        <div className="alert alert-danger">
          Você não tem permissão para acessar esta página.
        </div>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mt-4">
        <div className="d-flex justify-content-center">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Carregando...</span>
          </div>
        </div>
      </div>
    )
  }

  const empresas = empresasData?.empresas?.map(e => e.nome) || []
  const tipos = tiposData?.tipos || []
  const resolvidas = data?.pendencias || []
  const logsPorPendencia = data?.logs_por_pendencia || {}

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Pendências Resolvidas</h2>
        <div>
          <button onClick={handleExportarExcel} className="btn btn-success me-2">
            <i className="bi bi-download"></i> Exportar Excel
          </button>
          <Link to="/dashboard" className="btn btn-secondary">
            <i className="bi bi-arrow-left"></i> Voltar
          </Link>
        </div>
      </div>

      <form className="row g-3 mb-4">
        <div className="col-md-3">
          <label htmlFor="empresa" className="form-label">Empresa</label>
          <select
            className="form-select"
            id="empresa"
            value={empresa}
            onChange={(e) => handleFilterChange('empresa', e.target.value)}
          >
            <option value="">Todas</option>
            {empresas.map(emp => (
              <option key={emp} value={emp}>{emp}</option>
            ))}
          </select>
        </div>
        <div className="col-md-3">
          <label htmlFor="tipo_pendencia" className="form-label">Tipo de Pendência</label>
          <select
            className="form-select"
            id="tipo_pendencia"
            value={tipo}
            onChange={(e) => handleFilterChange('tipo_pendencia', e.target.value)}
          >
            <option value="">Todos</option>
            {tipos.map(t => (
              <option key={t} value={t}>{t}</option>
            ))}
          </select>
        </div>
        <div className="col-md-3">
          <label htmlFor="data_inicio" className="form-label">Data Inicial</label>
          <input
            type="date"
            className="form-control"
            id="data_inicio"
            value={dataInicio}
            onChange={(e) => handleFilterChange('data_inicio', e.target.value)}
          />
        </div>
        <div className="col-md-3">
          <label htmlFor="data_fim" className="form-label">Data Final</label>
          <input
            type="date"
            className="form-control"
            id="data_fim"
            value={dataFim}
            onChange={(e) => handleFilterChange('data_fim', e.target.value)}
          />
        </div>
      </form>

      {resolvidas.length > 0 ? (
        <div className="table-responsive">
          <table className="table table-striped table-bordered">
            <thead>
              <tr>
                <th>Tipo</th>
                <th>Empresa</th>
                <th>Banco</th>
                <th>Data</th>
                <th>Fornecedor/Cliente</th>
                <th>Valor</th>
                <th>Observação</th>
                <th>Natureza de Operação</th>
                <th>Modificado por</th>
                <th>Anexo</th>
                <th>Logs</th>
              </tr>
            </thead>
            <tbody>
              {resolvidas.map((pendencia) => (
                <React.Fragment key={pendencia.id}>
                  <tr>
                    <td>{pendencia.tipo_pendencia}</td>
                    <td>{pendencia.empresa}</td>
                    <td>{pendencia.banco || '—'}</td>
                    <td>{pendencia.data ? new Date(pendencia.data).toLocaleDateString('pt-BR') : '—'}</td>
                    <td>{pendencia.fornecedor_cliente}</td>
                    <td>R$ {pendencia.valor?.toFixed(2) || '0.00'}</td>
                    <td>{pendencia.observacao || '—'}</td>
                    <td>{pendencia.natureza_operacao || '—'}</td>
                    <td>{pendencia.modificado_por || '—'}</td>
                    <td>
                      {pendencia.nota_fiscal_arquivo ? (
                        <a
                          href={`/static/${pendencia.nota_fiscal_arquivo}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn btn-sm btn-outline-primary"
                        >
                          <i className="bi bi-download"></i> Anexo
                        </a>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                    <td>
                      <button
                        className="btn btn-sm btn-outline-info"
                        onClick={() => toggleLogs(pendencia.id)}
                      >
                        <i className={`bi bi-chevron-${expandedLogs[pendencia.id] ? 'up' : 'down'}`}></i>
                        {expandedLogs[pendencia.id] ? 'Ocultar' : 'Ver'} Logs
                      </button>
                    </td>
                  </tr>
                  {expandedLogs[pendencia.id] && (
                    <tr>
                      <td colSpan="11" style={{ padding: 0, background: '#f9f9f9' }}>
                        <div style={{ padding: '0.5em 1em' }}>
                          <strong>Logs de Alteração:</strong>
                          <div className="table-responsive mt-2">
                            <table className="table table-sm table-bordered mb-0">
                              <thead>
                                <tr>
                                  <th>Data/Hora</th>
                                  <th>Usuário</th>
                                  <th>Tipo</th>
                                  <th>Ação</th>
                                  <th>Campo</th>
                                  <th>De</th>
                                  <th>Para</th>
                                </tr>
                              </thead>
                              <tbody>
                                {logsPorPendencia[pendencia.id]?.length > 0 ? (
                                  logsPorPendencia[pendencia.id].map((log, idx) => (
                                    <tr key={idx}>
                                      <td>{new Date(log.data_hora).toLocaleString('pt-BR')}</td>
                                      <td>{log.usuario}</td>
                                      <td>{log.tipo_usuario}</td>
                                      <td>{log.acao}</td>
                                      <td>{log.campo_alterado || '—'}</td>
                                      <td>{log.valor_anterior || '—'}</td>
                                      <td>{log.valor_novo || '—'}</td>
                                    </tr>
                                  ))
                                ) : (
                                  <tr>
                                    <td colSpan="7" className="text-center">
                                      Nenhum log para esta pendência.
                                    </td>
                                  </tr>
                                )}
                              </tbody>
                            </table>
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="alert alert-info">
          Nenhuma pendência resolvida encontrada.
        </div>
      )}
    </div>
  )
}

export default PendenciasResolvidas

