import React, { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function OperadorPendencias() {
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
  const [showModalMotivo, setShowModalMotivo] = useState(null)
  const [motivoRecusa, setMotivoRecusa] = useState('')
  const [showModalNatureza, setShowModalNatureza] = useState(null)
  const [naturezaOperacao, setNaturezaOperacao] = useState('')

  const { data, isLoading } = useQuery(
    ['operador-pendencias', empresa, empresas_selecionadas, tipoFiltro, busca, filtroStatus, filtroPrazo, filtroValor],
    async () => {
      const params = new URLSearchParams()
      if (empresa) params.append('empresa', empresa)
      if (empresas_selecionadas) params.append('empresas', empresas_selecionadas)
      if (tipoFiltro) params.append('tipo_pendencia', tipoFiltro)
      if (busca) params.append('busca', busca)
      if (filtroStatus) params.append('filtro_status', filtroStatus)
      if (filtroPrazo) params.append('filtro_prazo', filtroPrazo)
      if (filtroValor) params.append('filtro_valor', filtroValor)

      const response = await api.get(`/api/operador/pendencias?${params.toString()}`)
      return response.data
    },
    { enabled: !!user && ['adm', 'operador', 'supervisor'].includes(user?.tipo) }
  )

  const naturezaMutation = useMutation(
    async ({ id, natureza }) => {
      const response = await api.post(`/api/operador/pendencia/${id}/natureza`, {
        natureza_operacao: natureza
      })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['operador-pendencias'])
        setShowModalNatureza(null)
        setNaturezaOperacao('')
      }
    }
  )

  const recusarMutation = useMutation(
    async ({ id, motivo }) => {
      const response = await api.post(`/api/operador/pendencia/${id}/recusar`, {
        motivo_recusa: motivo
      })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['operador-pendencias'])
        setShowModalRecusar(null)
        setMotivoRecusa('')
      }
    }
  )

  const loteEnviarMutation = useMutation(
    async (ids) => {
      const response = await api.post('/api/operador/pendencias/lote-enviar', { ids })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['operador-pendencias'])
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

  const handleEnviarLote = () => {
    if (selectedIds.length === 0) return
    if (window.confirm(`Enviar ${selectedIds.length} pendência(s) ao supervisor?`)) {
      loteEnviarMutation.mutate(selectedIds)
    }
  }

  const handleInformarNatureza = (pendencia) => {
    setShowModalNatureza(pendencia)
    setNaturezaOperacao(pendencia.natureza_operacao || '')
  }

  const handleSubmitNatureza = () => {
    if (!naturezaOperacao.trim()) {
      alert('Natureza de Operação é obrigatória')
      return
    }
    naturezaMutation.mutate({
      id: showModalNatureza.id,
      natureza: naturezaOperacao
    })
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

  if (!['adm', 'operador', 'supervisor'].includes(user?.tipo)) {
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

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2>
            <i className="bi bi-person-gear"></i> Painel do Operador
            {user?.tipo === 'supervisor' && (
              <span className="badge bg-warning ms-2">
                <i className="bi bi-tools"></i> Atuando como Operador
              </span>
            )}
          </h2>
          {user?.tipo === 'supervisor' && (
            <p className="text-muted mb-0">Como supervisor, você pode executar todas as ações do operador</p>
          )}
        </div>
        <div>
          <Link to="/dashboard" className="btn btn-secondary">
            <i className="bi bi-arrow-left"></i> Voltar ao Dashboard
          </Link>
        </div>
      </div>

      {/* Indicadores por Empresa */}
      {pendenciasAbertasPorEmpresa.length > 0 && (
        <div className="row mb-4">
          <div className="col-12">
            <div className="card border-warning">
              <div className="card-header bg-warning text-dark">
                <h5 className="mb-0">
                  <i className="bi bi-exclamation-triangle-fill"></i>
                  Pendências em Aberto por Empresa
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
                                {qtd} pendência{qtd > 1 ? 's' : ''} em aberto
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

      {/* Filtros */}
      <form className="row g-3 mb-3 align-items-end">
        <div className="col-md-3">
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
        <div className="col-md-2">
          <label className="form-label">Status</label>
          <select
            className="form-select"
            value={filtroStatus}
            onChange={(e) => handleFilterChange('filtro_status', e.target.value)}
          >
            <option value="">Todos</option>
            <option value="PENDENTE OPERADOR UP">Aguardando Operador</option>
            <option value="PENDENTE COMPLEMENTO CLIENTE">Aguardando Cliente</option>
            <option value="RESOLVIDA">Resolvidas</option>
          </select>
        </div>
        <div className="col-md-2">
          <label className="form-label">Prazo</label>
          <select
            className="form-select"
            value={filtroPrazo}
            onChange={(e) => handleFilterChange('filtro_prazo', e.target.value)}
          >
            <option value="">Todos</option>
            <option value="atrasadas">Atrasadas (&gt;7 dias)</option>
            <option value="recentes">Recentes (≤7 dias)</option>
          </select>
        </div>
        <div className="col-md-2">
          <label className="form-label">Valor</label>
          <select
            className="form-select"
            value={filtroValor}
            onChange={(e) => handleFilterChange('filtro_valor', e.target.value)}
          >
            <option value="">Todos</option>
            <option value="alto">Acima de R$ 5.000</option>
            <option value="baixo">Até R$ 5.000</option>
          </select>
        </div>
        <div className="col-md-3">
          <label className="form-label">Busca Avançada</label>
          <input
            type="text"
            className="form-control"
            value={busca}
            onChange={(e) => handleFilterChange('busca', e.target.value)}
            placeholder="Fornecedor, valor, data, status..."
          />
        </div>
      </form>

      {/* Painel de Prioridade */}
      <div className="alert alert-info mb-3">
        <i className="bi bi-exclamation-triangle-fill"></i>
        <strong>Pendências prioritárias aparecem no topo!</strong> Mais antigas e de valor alto são destacadas.
      </div>

      {/* Tabela de Pendências */}
      <form>
        <div className="card">
          <div className="card-header d-flex justify-content-between align-items-center">
            <h5 className="mb-0">Pendências Aguardando Ação do Operador</h5>
            {selectedIds.length > 0 && (
              <button
                type="button"
                className="btn btn-success btn-sm"
                onClick={handleEnviarLote}
              >
                <i className="bi bi-arrow-up-circle"></i> Enviar {selectedIds.length} selecionada(s) ao supervisor
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
                    <th>Tipo</th>
                    <th>Banco</th>
                    <th>Data</th>
                    <th>Fornecedor/Cliente</th>
                    <th>Valor</th>
                    <th>Resposta do Cliente</th>
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
                          <td>
                            {pendencia.resposta_cliente ? (
                              <span
                                className="text-truncate d-inline-block"
                                style={{ maxWidth: '200px' }}
                                title={pendencia.resposta_cliente}
                              >
                                {pendencia.resposta_cliente.length > 50
                                  ? `${pendencia.resposta_cliente.substring(0, 50)}...`
                                  : pendencia.resposta_cliente}
                              </span>
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
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
                            {pendencia.status === 'PENDENTE OPERADOR UP' && (
                              <div className="btn-group" role="group">
                                <button
                                  className="btn btn-primary btn-sm"
                                  onClick={() => handleInformarNatureza(pendencia)}
                                >
                                  <i className="bi bi-pencil-square"></i> Informar Natureza
                                </button>
                                <button
                                  className="btn btn-warning btn-sm"
                                  onClick={() => handleRecusar(pendencia)}
                                >
                                  <i className="bi bi-x-circle"></i> Recusar
                                </button>
                              </div>
                            )}
                            {pendencia.status === 'DEVOLVIDA AO OPERADOR' && (
                              <div className="btn-group" role="group">
                                <button
                                  className="btn btn-warning btn-sm"
                                  onClick={() => handleInformarNatureza(pendencia)}
                                >
                                  <i className="bi bi-arrow-clockwise"></i> Corrigir e Reenviar
                                </button>
                                {pendencia.motivo_recusa_supervisor && (
                                  <button
                                    className="btn btn-info btn-sm"
                                    onClick={() => setShowModalMotivo(pendencia)}
                                  >
                                    <i className="bi bi-info-circle"></i> Ver Motivo
                                  </button>
                                )}
                              </div>
                            )}
                            {pendencia.status === 'PENDENTE COMPLEMENTO CLIENTE' && (
                              <span className="badge bg-warning text-dark">
                                <i className="bi bi-clock"></i> Aguardando Cliente
                              </span>
                            )}
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
                      <td colSpan="11" className="text-center text-muted">
                        <i className="bi bi-check-circle"></i> Nenhuma pendência aguardando operador.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </form>

      {/* Modal Informar Natureza */}
      {showModalNatureza && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  Informar Natureza de Operação - Pendência #{showModalNatureza.id}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowModalNatureza(null)
                    setNaturezaOperacao('')
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <div className="mb-3">
                  <label className="form-label">
                    <strong>Natureza de Operação *</strong>
                  </label>
                  <textarea
                    className="form-control"
                    rows="4"
                    value={naturezaOperacao}
                    onChange={(e) => setNaturezaOperacao(e.target.value)}
                    placeholder="Ex: Serviços - 3.01.02"
                    required
                  />
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowModalNatureza(null)
                    setNaturezaOperacao('')
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={handleSubmitNatureza}
                  disabled={naturezaMutation.isLoading}
                >
                  {naturezaMutation.isLoading ? 'Enviando...' : 'Enviar ao Supervisor'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Recusar */}
      {showModalRecusar && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  <i className="bi bi-x-circle text-warning"></i> Recusar Resposta - Pendência #{showModalRecusar.id}
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
                  <strong>Atenção!</strong> Ao recusar a resposta, a pendência será devolvida ao cliente para complemento.
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
                    placeholder="Informe detalhadamente o que está faltando ou incompleto na resposta do cliente..."
                    required
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label"><strong>Resposta Atual do Cliente:</strong></label>
                  <div className="border rounded p-2 bg-light">
                    {showModalRecusar.resposta_cliente || 'Nenhuma resposta fornecida'}
                  </div>
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

      {/* Modal Motivo Recusa Supervisor */}
      {showModalMotivo && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header bg-warning text-dark">
                <h5 className="modal-title">
                  <i className="bi bi-exclamation-triangle"></i> Motivo da Recusa - Pendência #{showModalMotivo.id}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => setShowModalMotivo(null)}
                ></button>
              </div>
              <div className="modal-body">
                <div className="alert alert-warning">
                  <i className="bi bi-info-circle"></i>
                  <strong>Pendência devolvida pelo Supervisor</strong><br />
                  Esta pendência foi recusada e devolvida para correção.
                </div>
                <div className="mb-3">
                  <label className="form-label"><strong>Motivo da Recusa:</strong></label>
                  <div className="border rounded p-3 bg-light">
                    <i className="bi bi-chat-quote"></i> {showModalMotivo.motivo_recusa_supervisor}
                  </div>
                </div>
                <div className="mb-3">
                  <label className="form-label"><strong>Natureza de Operação Atual:</strong></label>
                  <div className="border rounded p-2 bg-light">
                    {showModalMotivo.natureza_operacao || 'Não informada'}
                  </div>
                </div>
                <div className="alert alert-info">
                  <i className="bi bi-lightbulb"></i>
                  <strong>Próximos passos:</strong>
                  <ul className="mb-0 mt-2">
                    <li>Analise o motivo da recusa</li>
                    <li>Corrija as informações conforme solicitado</li>
                    <li>Clique em "Corrigir e Reenviar" para enviar novamente ao supervisor</li>
                  </ul>
                </div>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => setShowModalMotivo(null)}
                >
                  Fechar
                </button>
                <button
                  type="button"
                  className="btn btn-warning"
                  onClick={() => {
                    setShowModalMotivo(null)
                    handleInformarNatureza(showModalMotivo)
                  }}
                >
                  <i className="bi bi-arrow-clockwise"></i> Corrigir e Reenviar
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default OperadorPendencias
