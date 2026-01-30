import React from 'react'
import { useParams, Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Empresas.css'

function EmpresasPorSegmento() {
  const { id } = useParams()
  const { user } = useAuth()

  const { data, isLoading } = useQuery(
    ['segmento', id],
    async () => {
      const response = await api.get(`/api/segmento/${id}`)
      return response.data
    },
    { enabled: !!user && !!id }
  )

  if (isLoading) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Carregando...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="empresas-container">
      <div className="container-fluid">
        <nav aria-label="breadcrumb" className="mb-4">
          <ol className="breadcrumb">
            <li className="breadcrumb-item">
              <Link to="/segmentos" style={{ textDecoration: 'none', color: '#64748b' }}>
                <i className="bi bi-grid-fill me-1"></i>Segmentos
              </Link>
            </li>
            <li className="breadcrumb-item active fw-bold" style={{ color: '#1B365D' }}>{data?.segmento?.nome}</li>
          </ol>
        </nav>

        <div className="page-header-empresas d-flex align-items-center gap-3">
          <div style={{
            width: '48px', height: '48px',
            background: 'linear-gradient(135deg, #005bb5 0%, #1B365D 100%)',
            borderRadius: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center',
            color: 'white', fontSize: '1.5rem', boxShadow: '0 4px 12px rgba(0, 91, 181, 0.25)'
          }}>
            <i className="bi bi-tag-fill"></i>
          </div>
          <h1 className="mb-0">{data?.segmento?.nome}</h1>
        </div>

        {data?.empresas && data.empresas.length > 0 ? (
          <div className="empresas-grid">
            {data.empresas.map((empresa) => (
              <div key={empresa.id} className="card-empresa">
                <div className="card-empresa-header">
                  <div className="card-empresa-identificacao">
                    <div className="card-empresa-avatar">
                      {empresa.nome.charAt(0).toUpperCase()}
                    </div>
                    <div className="card-empresa-info">
                      <h3 className="card-empresa-nome">{empresa.nome}</h3>
                      <span className="card-empresa-tipo">Empresa</span>
                    </div>
                  </div>
                </div>

                <div className="card-empresa-metrics">
                  <div className="metric-item">
                    <span className="metric-label">Pendentes</span>
                    <span className={`metric-value ${empresa.abertas > 0 ? 'pendentes' : ''}`}>
                      {empresa.abertas || 0}
                    </span>
                  </div>
                  <div className="metric-item">
                    <span className="metric-label">Resolvidas</span>
                    <span className="metric-value resolvidas">
                      {empresa.resolvidas || 0}
                    </span>
                  </div>
                </div>

                <div className="card-empresa-footer">
                  <div className="btn-group-card" style={{ gridTemplateColumns: '1fr' }}>
                    <Link
                      to={`/dashboard?empresa=${encodeURIComponent(empresa.nome)}`}
                      className="btn-card btn-card-primary"
                    >
                      <i className="bi bi-arrow-right-circle"></i> Ver Pendências
                    </Link>
                    <Link
                      to={`/pendencias-resolvidas?empresa=${empresa.nome}`}
                      className="btn-card btn-card-secondary"
                    >
                      <i className="bi bi-check2-circle"></i> Ver Resolvidas
                    </Link>
                  </div>
                  <div className="btn-group-card mt-2">
                    <Link
                      to={`/relatorio-mensal?empresa_id=${empresa.id}`}
                      className="btn-card btn-card-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.4rem' }}
                    >
                      <i className="bi bi-file-earmark-text"></i> Relatório
                    </Link>
                    <Link
                      to={`/nova-pendencia?empresa=${empresa.nome}`}
                      className="btn-card btn-card-secondary"
                      style={{ fontSize: '0.8rem', padding: '0.4rem', border: '1px solid #f59e0b', color: '#d97706' }}
                    >
                      <i className="bi bi-plus-lg"></i> Nova
                    </Link>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="alert alert-info shadow-sm border-0 bg-white">
            <i className="bi bi-info-circle me-2 text-primary"></i>
            Nenhuma empresa encontrada neste segmento.
          </div>
        )}
      </div>
    </div>
  )
}

export default EmpresasPorSegmento
