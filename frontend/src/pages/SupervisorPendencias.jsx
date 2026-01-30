import React, { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function SupervisorPendencias() {
  const [searchParams, setSearchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()

  const empresa = searchParams.get('empresa') || ''
  const empresas_selecionadas = searchParams.get('empresas') || ''
  const tipoFiltro = searchParams.get('tipo_pendencia') || ''
  const busca = searchParams.get('busca') || ''
  const filtroStatus = searchParams.get('filtro_status') || ''
  const filtroPrazo = searchParams.get('filtro_prazo') || ''
  const filtroValor = searchParams.get('filtro_valor') || ''

  const [selectedIds, setSelectedIds] = useState([])
  const [showModalRecusar, setShowModalRecusar] = useState(null)
  const [showModalHistorico, setShowModalHistorico] = useState(null)
  const [motivoRecusa, setMotivoRecusa] = useState('')

  const { data, isLoading } = useQuery(
    ['supervisor-pendencias', empresa, empresas_selecionadas, tipoFiltro, busca, filtroStatus, filtroPrazo, filtroValor],
    async () => {
      const params = new URLSearchParams()
      if (empresa) params.append('empresa', empresa)
      if (empresas_selecionadas) params.append('empresas', empresas_selecionadas)
      if (tipoFiltro) params.append('tipo_pendencia', tipoFiltro)
      if (busca) params.append('busca', busca)
      if (filtroStatus) params.append('filtro_status', filtroStatus)
      if (filtroPrazo) params.append('filtro_prazo', filtroPrazo)
      if (filtroValor) params.append('filtro_valor', filtroValor)

      const response = await api.get(`/api/supervisor/pendencias?${params.toString()}`)
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) }
  )

  const resolverMutation = useMutation(
    async (id) => {
      const response = await api.post(`/api/supervisor/pendencia/${id}/resolver`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['supervisor-pendencias'])
      }
    }
  )

  const recusarMutation = useMutation(
    async ({ id, motivo }) => {
      const response = await api.post(`/api/supervisor/pendencia/${id}/recusar`, {
        motivo_recusa_supervisor: motivo
      })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['supervisor-pendencias'])
        setShowModalRecusar(null)
        setMotivoRecusa('')
      }
    }
  )

  const loteResolverMutation = useMutation(
    async (ids) => {
      const response = await api.post('/api/supervisor/pendencias/lote-resolver', { ids })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['supervisor-pendencias'])
        setSelectedIds([])
      }
    }
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

  const handleSelectAll = (checked) => {
    if (checked) {
      const allIds = data?.pendencias?.map(p => p.id) || []
      setSelectedIds(allIds)
    } else {
      setSelectedIds([])
    }
  }

  const handleSelectPendencia = (id, checked) => {
    if (checked) {
      setSelectedIds(prev => [...prev, id])
    } else {
      setSelectedIds(prev => prev.filter(i => i !== id))
    }
  }

  const handleResolverLote = () => {
    if (selectedIds.length === 0) return
    if (window.confirm(`Resolver ${selectedIds.length} pendência(s)?`)) {
      loteResolverMutation.mutate(selectedIds)
    }
  }

  const handleResolver = (id) => {
    if (window.confirm('Deseja resolver esta pendência?')) {
      resolverMutation.mutate(id)
    }
  }

  const handleRecusar = (pendencia) => {
    setShowModalRecusar(pendencia)
    setMotivoRecusa('')
  }

  const handleSubmitRecusar = () => {
    if (!motivoRecusa.trim()) {
      alert('Motivo da recusa é obrigatório')
      return
    }
    recusarMutation.mutate({
      id: showModalRecusar.id,
      motivo: motivoRecusa
    })
  }

  if (!['adm', 'supervisor'].includes(user?.tipo)) {
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

  const pendencias = data?.pendencias || []
  const empresas = data?.empresas || []
  const pendenciasAbertasPorEmpresa = data?.pendencias_abertas_por_empresa || []
  const logsPorPendencia = data?.logs_por_pendencia || {}
  const tipos = data?.tipos_pendencia || []
  const metricas = data?.metricas || { total: 0, valor_alto: 0, atrasadas: 0 }

  return (
    <div className="container-fluid mt-4">
      <div className="d-flex flex-wrap justify-content-between align-items-center mb-3 gap-2">
        <h2 className="mb-0">
          <i className="bi bi-person-check-fill text-primary"></i> Painel do Supervisor
        </h2>
        <div className="d-flex gap-2">
          <Link to="/dashboard" className="btn btn-secondary btn-sm">
            <i className="bi bi-arrow-left"></i> Voltar
          </Link>
        </div>
      </div>

      {/* Cards de Resumo */}
      <div className="row mb-4 justify-content-center">
        <div className="col-6 col-md-3 mb-3">
          <div className="card bg-primary text-white h-100 text-center">
            <div className="card-body">
              <i className="bi bi-clock-history fs-1"></i>
              <h4 className="mt-2">{metricas.total}</h4>
              <p className="mb-0">Aguardando Aprovação</p>
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3 mb-3">
          <div className="card bg-warning text-white h-100 text-center">
            <div className="card-body">
              <i className="bi bi-exclamation-triangle fs-1"></i>
              <h4 className="mt-2">{metricas.valor_alto}</h4>
              <p className="mb-0">Valor Alto (&gt;R$ 5k)</p>
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3 mb-3">
          <div className="card bg-danger text-white h-100 text-center">
            <div className="card-body">
              <i className="bi bi-calendar-x fs-1"></i>
              <h4 className="mt-2">{metricas.atrasadas}</h4>
              <p className="mb-0">Atrasadas (&gt;7 dias)</p>
            </div>
          </div>
        </div>
        <div className="col-6 col-md-3 mb-3">
          <div className="card bg-success text-white h-100 text-center">
            <div className="card-body">
              <i className="bi bi-check-circle fs-1"></i>
              <h4 className="mt-2">{metricas.total}</h4>
              <p className="mb-0">Total Pendências</p>
            </div>
          </div>
        </div>
      </div>

      {/* Indicadores por Empresa */}
      {pendenciasAbertasPorEmpresa.length > 0 && (
        <div className="row mb-4 justify-content-center">
          <div className="col-12 col-lg-10">
            <div className="card border-danger">
              <div className="card-header bg-danger text-white">
                <h5 className="mb-0">
                  <i className="bi bi-exclamation-triangle-fill"></i>
                  Pendências Aguardando Aprovação por Empresa
                </h5>
              </div>
              <div className="card-body">
                <div className="row">
                  {pendenciasAbertasPorEmpresa.map((item) => {
                    const qtd = item.quantidade
                    const badgeClass = qtd >= 10 ? 'danger' : qtd >= 5 ? 'warning' : 'primary'
                    return (
                      <div key={item.empresa} className="col-md-4 col-lg-3 mb-3">
                        <div className={`card h-100 border-${badgeClass}`}>
                          <div className="card-body text-center">
                            <h6 className="card-title text-truncate" title={item.empresa}>
                              {item.empresa}
                            </h6>
                            <div className="mb-2">
                              <span className={`badge bg-${badgeClass} fs-6`}>
                                {qtd} pendência{qtd > 1 ? 's' : ''} aguardando
                              </span>
                            </div>
                            <button
                              className={`btn btn-outline-${badgeClass} btn-sm`}
                              onClick={() => handleFilterChange('empresa', item.empresa)}
                            >
                              <i className="bi bi-eye"></i> Ver pendências
                            </button>
                          </div>
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filtros Avançados */}
      <div className="card mb-4 shadow-sm border-0">
        <div className="card-header bg-light">
          <h5 className="mb-0"><i className="bi bi-funnel"></i> Filtros Avançados</h5>
        </div>
        <div className="card-body">
          <form className="row g-3 align-items-end justify-content-center">
            <div className="col-12 col-md-3">
              <label className="form-label">Empresas</label>
              <select
                className="form-select"
                value={empresa}
                onChange={(e) => handleFilterChange('empresa', e.target.value)}
              >
                <option value="">Todas</option>
                {empresas.map(emp => (
                  <option key={emp} value={emp}>{emp}</option>
                ))}
              </select>
            </div>
            <div className="col-12 col-md-2">
              <label className="form-label">Status</label>
              <select
                className="form-select"
                value={filtroStatus}
                onChange={(e) => handleFilterChange('filtro_status', e.target.value)}
              >
                <option value="">Todos</option>
                <option value="PENDENTE SUPERVISOR UP">Aguardando Aprovação</option>
              </select>
            </div>
            <div className="col-12 col-md-2">
              <label className="form-label">Tipo</label>
              <select
                className="form-select"
                value={tipoFiltro}
                onChange={(e) => handleFilterChange('tipo_pendencia', e.target.value)}
              >
                <option value="">Todos</option>
                {tipos.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
            <div className="col-12 col-md-2">
              <label className="form-label">Prazo</label>
              <select
                className="form-select"
                value={filtroPrazo}
                onChange={(e) => handleFilterChange('filtro_prazo', e.target.value)}
              >
                <option value="">Todos</option>
                <option value="atrasadas">Atrasadas</option>
                <option value="recentes">Recentes</option>
              </select>
            </div>
            <div className="col-12 col-md-2">
              <label className="form-label">Valor</label>
              <select
                className="form-select"
                value={filtroValor}
                onChange={(e) => handleFilterChange('filtro_valor', e.target.value)}
              >
                <option value="">Todos</option>
                <option value="alto">Alto</option>
                <option value="baixo">Baixo</option>
              </select>
            </div>
            <div className="col-12 col-md-1">
              <button type="button" className="btn btn-primary w-100">
                <i className="bi bi-search"></i>
              </button>
            </div>
          </form>
        </div>
      </div>

      {/* Tabela de Pendências */}
      <div className="card">
        <div className="card-header d-flex justify-content-between align-items-center">
          <h5 className="mb-0">Pendências Aguardando Aprovação</h5>
          {selectedIds.length > 0 && (
            <button
              type="button"
              className="btn btn-success btn-sm"
              onClick={handleResolverLote}
            >
              <i className="bi bi-check-circle"></i> Resolver {selectedIds.length} selecionada(s)
            </button>
          )}
        </div>
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-hover">
              <thead>
                <tr>
                  <th>
                    <input
                      type="checkbox"
                      checked={selectedIds.length === pendencias.length && pendencias.length > 0}
                      onChange={(e) => handleSelectAll(e.target.checked)}
                    />
                  </th>
                  <th>ID</th>
                  <th>Empresa</th>
                  <th>Tipo</th>
                  <th>Banco</th>
                  <th>Data</th>
                  <th>Fornecedor/Cliente</th>
                  <th>Valor</th>
                  <th>Natureza de Operação</th>
                  <th>Anexo</th>
                  <th>Ações</th>
                  <th>Histórico</th>
                </tr>
              </thead>
              <tbody>
                {pendencias.length > 0 ? (
                  pendencias.map((pendencia) => {
                    const isUrgente = pendencia.valor >= 5000 || (pendencia.dias_aberto || 0) > 7
                    return (
                      <tr key={pendencia.id} className={isUrgente ? 'table-danger' : ''}>
                        <td>
                          <input
                            type="checkbox"
                            checked={selectedIds.includes(pendencia.id)}
                            onChange={(e) => handleSelectPendencia(pendencia.id, e.target.checked)}
                          />
                        </td>
                        <td><strong>#{pendencia.id}</strong></td>
                        <td>{pendencia.empresa}</td>
                        <td>
                          {pendencia.tipo_pendencia}
                          {(pendencia.tipo_pendencia === 'Lançamento Não Encontrado em Sistema' || pendencia.tipo_pendencia === 'Lançamento Não Encontrado em Extrato') && pendencia.tipo_credito_debito && (
                            <div className="mt-1">
                              <span className={`badge ${pendencia.tipo_credito_debito === 'CREDITO' ? 'bg-success' : 'bg-danger'}`}>
                                <i className={`bi bi-${pendencia.tipo_credito_debito === 'CREDITO' ? 'arrow-down-circle' : 'arrow-up-circle'}`}></i>
                                {' '}{pendencia.tipo_credito_debito === 'CREDITO' ? 'Crédito' : 'Débito'}
                              </span>
                            </div>
                          )}
                        </td>
                        <td>{pendencia.banco || '—'}</td>
                        <td>
                          {pendencia.data ? new Date(pendencia.data).toLocaleDateString('pt-BR') : '—'}
                        </td>
                        <td>{pendencia.fornecedor_cliente}</td>
                        <td>
                          <strong>R$ {pendencia.valor?.toFixed(2) || '0.00'}</strong>
                          {pendencia.valor >= 5000 && (
                            <span className="badge bg-danger ms-1">Alto</span>
                          )}
                        </td>
                        <td>{pendencia.natureza_operacao || '—'}</td>
                        <td>
                          {pendencia.nota_fiscal_arquivo ? (
                            <a
                              href={`/static/${pendencia.nota_fiscal_arquivo}`}
                              className="btn btn-sm btn-outline-primary"
                              target="_blank"
                              rel="noopener noreferrer"
                            >
                              <i className="bi bi-download"></i> Anexo
                            </a>
                          ) : (
                            <span className="text-muted">-</span>
                          )}
                        </td>
                        <td>
                          <div className="btn-group" role="group">
                            <button
                              className="btn btn-success btn-sm"
                              onClick={() => handleResolver(pendencia.id)}
                              disabled={resolverMutation.isLoading}
                            >
                              <i className="bi bi-check-circle"></i> Resolver
                            </button>
                            <button
                              className="btn btn-warning btn-sm"
                              onClick={() => handleRecusar(pendencia)}
                            >
                              <i className="bi bi-x-circle"></i> Recusar
                            </button>
                          </div>
                        </td>
                        <td>
                          <button
                            className="btn btn-outline-secondary btn-sm"
                            onClick={() => setShowModalHistorico(pendencia)}
                          >
                            <i className="bi bi-clock-history"></i> Histórico
                          </button>
                        </td>
                      </tr>
                    )
                  })
                ) : (
                  <tr>
                    <td colSpan="12" className="text-center text-muted">
                      <i className="bi bi-check-circle"></i> Nenhuma pendência aguardando aprovação.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Modal Recusar */}
      {showModalRecusar && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-x-circle text-warning"></i> Recusar e Devolver ao Operador - Pendência #{showModalRecusar.id}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowModalRecusar(null)
                    setMotivoRecusa('')
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <div className="alert alert-warning">
                  <i className="bi bi-exclamation-triangle"></i>
                  <strong>Atenção!</strong> Ao recusar, a pendência será devolvida ao operador para correção.
                </div>
                <div className="mb-3">
                  <label className="form-label">
                    <strong>Motivo da Recusa *</strong>
                  </label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={motivoRecusa}
                    onChange={(e) => setMotivoRecusa(e.target.value)}
                    placeholder="Informe detalhadamente o motivo da recusa e o que precisa ser corrigido..."
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowModalRecusar(null)
                    setMotivoRecusa('')
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="btn btn-warning"
                  onClick={handleSubmitRecusar}
                  disabled={recusarMutation.isLoading}
                >
                  {recusarMutation.isLoading ? 'Processando...' : 'Confirmar Recusa'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Histórico */}
      {showModalHistorico && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Histórico da Pendência #{showModalHistorico.id}</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowModalHistorico(null)}
                ></button>
              </div>
              <div className="modal-body">
                <div className="table-responsive">
                  <table className="table table-bordered table-sm">
                    <thead>
                      <tr>
                        <th>Data/Hora</th>
                        <th>Usuário</th>
                        <th>Tipo</th>
                        <th>Ação</th>
                        <th>Campo Alterado</th>
                        <th>Valor Anterior</th>
                        <th>Valor Novo</th>
                      </tr>
                    </thead>
                    <tbody>
                      {logsPorPendencia[showModalHistorico.id]?.length > 0 ? (
                        logsPorPendencia[showModalHistorico.id].map((log) => (
                          <tr key={log.id}>
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
                            Nenhum histórico para esta pendência.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModalHistorico(null)}
                >
                  Fechar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default SupervisorPendencias
