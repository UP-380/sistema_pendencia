import React from 'react'
import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'
import './Segmentos.css'

function Segmentos() {
  const { user } = useAuth()
  
  const { data, isLoading } = useQuery(
    'segmentos',
    async () => {
      const response = await api.get('/api/segmentos')
      return response.data
    },
    { enabled: !!user }
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
    <div className="segmentos-container">
      <div className="container">
        <div className="page-header-segmentos mb-4">
          <h1 className="mb-0">
            <i className="bi bi-grid-3x3-gap me-2"></i>
            Segmentos
          </h1>
          <p className="text-muted mb-0">Selecione um segmento para ver as empresas</p>
        </div>

        {data?.segmentos && data.segmentos.length > 0 ? (
          <div className="row g-4">
            {data.segmentos.map((segmento) => (
              <div key={segmento.id} className="col-12 col-sm-6 col-md-4">
                <Link
                  to={`/segmento/${segmento.id}`}
                  className="text-decoration-none"
                  style={{ display: 'block' }}
                >
                  <div className="card h-100 shadow-sm segmento-card">
                    <div className="card-body p-4">
                      <div className="d-flex justify-content-between align-items-start mb-3">
                        <h5 className="mb-0 fw-bold text-white">{segmento.nome}</h5>
                        <i className="bi bi-grid-3x3-gap fs-4 text-white" style={{ opacity: 0.8 }}></i>
                      </div>
                      <div className="mb-3">
                        <div className="d-flex align-items-center mb-2">
                          <i className="bi bi-building me-2 text-white" style={{ opacity: 0.8 }}></i>
                          <span className="text-white">
                            <strong>{segmento.total_empresas || 0}</strong> Empresas
                          </span>
                        </div>
                        <div className="d-flex align-items-center">
                          <i className="bi bi-clock-history me-2 text-white" style={{ opacity: 0.8 }}></i>
                          <span className="text-white">
                            <strong>{segmento.total_abertas || 0}</strong> Pendências
                          </span>
                        </div>
                      </div>
                      <div className="text-center">
                        <span className="badge bg-light text-dark px-3 py-2">
                          Ver Empresas <i className="bi bi-arrow-right ms-1"></i>
                        </span>
                      </div>
                    </div>
                  </div>
                </Link>
              </div>
            ))}
          </div>
        ) : (
          <div className="alert alert-info" role="alert">
            <i className="bi bi-info-circle me-2"></i>
            <strong>Nenhum segmento encontrado</strong>
          </div>
        )}
      </div>
    </div>
  )
}

export default Segmentos

