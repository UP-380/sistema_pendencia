import React, { useState, useEffect } from 'react'
import { useQuery } from 'react-query'
import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'
import { Pie, Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
  Title
} from 'chart.js'
import './Empresas.css'

ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale, LinearScale, BarElement, Title)

function Empresas() {
  const { user } = useAuth()
  const [filtros, setFiltros] = useState({
    data_abertura_inicio: '',
    data_abertura_fim: '',
    data_resolucao_inicio: '',
    data_resolucao_fim: '',
    segmentos: [],
    clientes: [],
    operadores: [],
    supervisores: []
  })

  const { data, isLoading, refetch } = useQuery(
    ['empresas', filtros],
    async () => {
      const params = new URLSearchParams()
      Object.entries(filtros).forEach(([key, value]) => {
        if (Array.isArray(value)) {
          value.forEach(v => params.append(key, v))
        } else if (value) {
          params.append(key, value)
        }
      })
      const response = await api.get(`/api/empresas?${params.toString()}`)
      return response.data
    },
    {
      keepPreviousData: true,
      enabled: !!user
    }
  )

  const handleFiltroChange = (key, value) => {
    setFiltros(prev => ({ ...prev, [key]: value }))
  }

  const limparFiltros = () => {
    setFiltros({
      data_abertura_inicio: '',
      data_abertura_fim: '',
      data_resolucao_inicio: '',
      data_resolucao_fim: '',
      segmentos: [],
      clientes: [],
      operadores: [],
      supervisores: []
    })
  }

  const chartDataTipo = {
    labels: data?.tipos_labels || [],
    datasets: [{
      label: 'Quantidade',
      data: data?.tipos_valores || [],
      backgroundColor: [
        '#005bb5', '#1B365D', '#FF6B35', '#10b981', '#8b5cf6', '#f59e0b'
      ]
    }]
  }

  const chartDataStatus = {
    labels: ['Abertas', 'Resolvidas'],
    datasets: [{
      label: 'Pendências',
      data: [data?.abertas_count || 0, data?.resolvidas_count || 0],
      backgroundColor: ['#f59e0b', '#10b981']
    }]
  }

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
        <div className="page-header-empresas d-flex justify-content-between align-items-center">
          <h1 className="mb-0">Empresas - Pendências em Aberto</h1>
          {user?.tipo !== 'cliente' && (
            <span>
              <Link to="/dashboard" className="btn btn-outline-primary me-2">
                <i className="bi bi-clock-history"></i> Ver Últimas Pendências
              </Link>
              <Link to="/logs-recentes" className="btn btn-outline-secondary">
                <i className="bi bi-list-check"></i> Ver Logs Recentes
              </Link>
            </span>
          )}
        </div>

        {user?.tipo !== 'cliente' && (
          <div className="filtro-datas">
            <h5 className="mb-3">
              <i className="bi bi-calendar-range me-2"></i>Filtrar Pendências por Data
            </h5>
            <div className="row g-3">
              <div className="col-md-3">
                <label className="form-label">Data Abertura - Início</label>
                <input
                  type="date"
                  className="form-control"
                  value={filtros.data_abertura_inicio}
                  onChange={(e) => handleFiltroChange('data_abertura_inicio', e.target.value)}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label">Data Abertura - Fim</label>
                <input
                  type="date"
                  className="form-control"
                  value={filtros.data_abertura_fim}
                  onChange={(e) => handleFiltroChange('data_abertura_fim', e.target.value)}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label">Data Resolução - Início</label>
                <input
                  type="date"
                  className="form-control"
                  value={filtros.data_resolucao_inicio}
                  onChange={(e) => handleFiltroChange('data_resolucao_inicio', e.target.value)}
                />
              </div>
              <div className="col-md-3">
                <label className="form-label">Data Resolução - Fim</label>
                <input
                  type="date"
                  className="form-control"
                  value={filtros.data_resolucao_fim}
                  onChange={(e) => handleFiltroChange('data_resolucao_fim', e.target.value)}
                />
              </div>
              <div className="col-12">
                <button onClick={() => refetch()} className="btn btn-primary me-2">
                  <i className="bi bi-filter me-2"></i>Aplicar Filtros
                </button>
                <button onClick={limparFiltros} className="btn btn-secondary">
                  <i className="bi bi-x-circle me-2"></i>Limpar Todos os Filtros
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Nota: Filtros avançados (multiselect) podem ser adicionados aqui posteriormente */}

        {user?.tipo !== 'cliente' && data && (
          <div className="row graficos-container mb-4">
            <div className="col-lg-6 col-xl-5">
              <div className="card card-grafico h-100">
                <h5 className="card-grafico-title">
                  <i className="bi bi-pie-chart me-2"></i>Quantidade por Tipo de Pendência
                </h5>
                {data.tipos_labels?.length > 0 ? (
                  <div className="chart-wrapper">
                    <Pie
                      data={chartDataTipo}
                      options={{
                        maintainAspectRatio: false,
                        plugins: {
                          legend: {
                            position: 'bottom',
                            labels: {
                              boxWidth: 12,
                              padding: 10,
                              font: { size: 11 }
                            }
                          }
                        }
                      }}
                    />
                  </div>
                ) : (
                  <p className="text-muted">Nenhum dado disponível</p>
                )}
              </div>
            </div>
            <div className="col-lg-6 col-xl-7">
              <div className="card card-grafico h-100">
                <h5 className="card-grafico-title">
                  <i className="bi bi-bar-chart me-2"></i>Pendências Abertas vs Resolvidas
                </h5>
                <div className="chart-wrapper">
                  <Bar
                    data={chartDataStatus}
                    options={{
                      maintainAspectRatio: false,
                      plugins: {
                        legend: { display: false }
                      },
                      scales: {
                        y: {
                          beginAtZero: true,
                          ticks: { font: { size: 11 } }
                        },
                        x: {
                          ticks: { font: { size: 11 } }
                        }
                      }
                    }}
                  />
                </div>
                <div className="chart-summary">
                  <span className="badge bg-warning text-dark me-2">
                    <i className="bi bi-clock me-1"></i>Abertas: {data.abertas_count || 0}
                  </span>
                  <span className="badge bg-success">
                    <i className="bi bi-check-circle me-1"></i>Resolvidas: {data.resolvidas_count || 0}
                  </span>
                </div>
              </div>
            </div>
          </div>
        )}

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
                      <span className="card-empresa-tipo">Cliente</span>
                    </div>
                  </div>
                  {/* Menu de ações ou ícone extra opcional aqui */}
                </div>

                <div className="card-empresa-metrics">
                  <div className="metric-item">
                    <span className="metric-label">Pendentes</span>
                    <span className={`metric-value ${empresa.abertas > 0 ? 'pendentes' : ''}`}>
                      {empresa.abertas}
                    </span>
                  </div>
                  {/* Podemos adicionar mais métricas futuramente, ex: Total, Resolvidas, etc. */}
                  {user?.tipo !== 'cliente' && (
                    <div className="metric-item">
                      <span className="metric-label">Status</span>
                      <span className="metric-value" style={{ fontSize: '1rem', alignSelf: 'center' }}>
                        {empresa.abertas > 0 ? '⚠️ Ação' : '✅ Ok'}
                      </span>
                    </div>
                  )}
                </div>

                <div className="card-empresa-footer">
                  {user?.tipo === 'cliente' ? (
                    <Link
                      to={`/dashboard?empresa=${encodeURIComponent(empresa.nome)}`}
                      className="btn-card btn-card-primary"
                    >
                      <i className="bi bi-eye"></i> Ver Pendências
                    </Link>
                  ) : (
                    <>
                      <div className="btn-group-card">
                        <Link
                          to={`/dashboard?empresa=${encodeURIComponent(empresa.nome)}`}
                          className="btn-card btn-card-primary"
                        >
                          <i className="bi bi-list-check"></i> Pendências
                        </Link>
                        {['adm', 'operador', 'supervisor'].includes(user?.tipo) && (
                          <Link
                            to={`/nova-pendencia?empresa=${empresa.nome}`}
                            className="btn-card btn-card-secondary"
                          >
                            <i className="bi bi-plus-lg"></i> Nova
                          </Link>
                        )}
                      </div>

                      {['adm', 'supervisor'].includes(user?.tipo) && (
                        <div className="btn-group-card mt-2">
                          <Link
                            to={`/pendencias-resolvidas?empresa=${empresa.nome}`}
                            className="btn-card btn-card-secondary"
                            style={{ fontSize: '0.8rem', padding: '0.4rem' }}
                          >
                            <i className="bi bi-check2-circle"></i> Resolvidas
                          </Link>
                          <Link
                            to={`/relatorio-mensal?empresa_id=${empresa.id}`}
                            className="btn-card btn-card-secondary"
                            style={{ fontSize: '0.8rem', padding: '0.4rem' }}
                          >
                            <i className="bi bi-file-earmark-text"></i> Relatório
                          </Link>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="alert alert-info" role="alert">
            <i className="bi bi-info-circle me-2"></i>
            <strong>Nenhuma empresa encontrada</strong> com os filtros aplicados.
          </div>
        )}
      </div>
    </div>
  )
}

export default Empresas
