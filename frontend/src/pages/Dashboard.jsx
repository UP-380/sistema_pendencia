import React, { useState } from 'react'
import { useSearchParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function Dashboard() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const empresa = searchParams.get('empresa')
  const tipoFiltro = searchParams.get('tipo_pendencia') || ''
  const busca = searchParams.get('busca') || ''
  const { user } = useAuth()
  const [pendenciaSelecionada, setPendenciaSelecionada] = useState(null)
  const [showModal, setShowModal] = useState(false)

  const { data, isLoading } = useQuery(
    ['dashboard', empresa, tipoFiltro, busca],
    async () => {
      const params = new URLSearchParams()
      if (empresa) params.append('empresa', empresa)
      if (tipoFiltro) params.append('tipo_pendencia', tipoFiltro)
      if (busca) params.append('busca', busca)
      const response = await api.get(`/api/dashboard?${params.toString()}`)
      return response.data
    },
    { enabled: !!user }
  )

  const resolverMutation = useMutation(
    async (id) => {
      const response = await api.post(`/api/pendencia/${id}/resolver`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['dashboard'])
        setShowModal(false)
        setPendenciaSelecionada(null)
      }
    }
  )

  const excluirMutation = useMutation(
    async (id) => {
      const response = await api.delete(`/api/pendencia/${id}`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['dashboard'])
        setShowModal(false)
        setPendenciaSelecionada(null)
      }
    }
  )

  const handleVerPendencia = async (pendencia) => {
    try {
      const response = await api.get(`/api/pendencia/${pendencia.id}`)
      setPendenciaSelecionada(response.data)
      setShowModal(true)
    } catch (error) {
      console.error('Erro ao carregar pendência:', error)
    }
  }

  const handleResolver = () => {
    if (pendenciaSelecionada && window.confirm('Deseja marcar esta pendência como resolvida?')) {
      resolverMutation.mutate(pendenciaSelecionada.id)
    }
  }

  const handleExcluir = () => {
    if (pendenciaSelecionada && window.confirm('Tem certeza que deseja excluir esta pendência?')) {
      excluirMutation.mutate(pendenciaSelecionada.id)
    }
  }

  const handleTipoClick = (tipo) => {
    const params = new URLSearchParams(searchParams)
    params.set('tipo_pendencia', tipo)
    navigate(`/dashboard?${params.toString()}`)
  }

  const handleTipoChange = (e) => {
    const params = new URLSearchParams(searchParams)
    params.set('tipo_pendencia', e.target.value)
    navigate(`/dashboard?${params.toString()}`)
  }

  const handleBuscaSubmit = (e) => {
    e.preventDefault()
    const formData = new FormData(e.target)
    const buscaValue = formData.get('busca')
    const params = new URLSearchParams(searchParams)
    if (buscaValue) {
      params.set('busca', buscaValue)
    } else {
      params.delete('busca')
    }
    navigate(`/dashboard?${params.toString()}`)
  }

  const formatarData = (dataStr) => {
    if (!dataStr) return '—'
    try {
      const data = new Date(dataStr)
      return data.toLocaleDateString('pt-BR')
    } catch {
      return '—'
    }
  }

  const formatarDataHora = (dataStr) => {
    if (!dataStr) return '—'
    try {
      const data = new Date(dataStr)
      return data.toLocaleString('pt-BR')
    } catch {
      return '—'
    }
  }

  const formatarMoeda = (valor) => {
    if (!valor) return 'R$ 0,00'
    return new Intl.NumberFormat('pt-BR', {
      style: 'currency',
      currency: 'BRL'
    }).format(valor)
  }

  const getStatusBadge = (status) => {
    if (!status) return <span className="badge bg-secondary">—</span>

    const statusUpper = status.toUpperCase()
    if (statusUpper.includes('RESOLVIDA') || statusUpper === 'RESOLVIDA') {
      return <span className="badge bg-success"><i className="bi bi-check-circle"></i> Resolvida</span>
    } else if (statusUpper.includes('PENDENTE CLIENTE') || statusUpper === 'PENDENTE CLIENTE') {
      return <span className="badge bg-warning"><i className="bi bi-clock"></i> Pendente Cliente</span>
    } else if (statusUpper.includes('PENDENTE OPERADOR')) {
      return <span className="badge bg-info"><i className="bi bi-person-gear"></i> Operador UP</span>
    } else if (statusUpper.includes('PENDENTE SUPERVISOR')) {
      return <span className="badge bg-danger"><i className="bi bi-person-check"></i> Supervisor</span>
    } else if (statusUpper.includes('PENDENTE')) {
      return <span className="badge bg-warning">{status}</span>
    }
    return <span className="badge bg-secondary">{status}</span>
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

  if (!data) {
    return (
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <div className="alert alert-warning">Nenhum dado disponível.</div>
      </div>
    )
  }

  const empresaFiltro = empresa || data.empresas?.[0] || ''
  const tipoFiltroAtual = tipoFiltro || data.tipos_pendencia?.[0] || ''

  return (
    <div className="container-fluid">
      {/* Breadcrumb */}
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item">
            <Link to="/empresas">Empresas</Link>
          </li>
          <li className="breadcrumb-item active" aria-current="page">
            {empresaFiltro || 'Painel de Pendências'}
          </li>
        </ol>
      </nav>

      {/* Cards de Resumo por Tipo */}
      <div className="row mb-4">
        {data.tipos_pendencia?.map((tipo) => {
          const quantidade = data.pendencias_por_tipo?.[tipo] || 0
          return (
            <div key={tipo} className="col-lg-3 col-md-4 mb-3">
              <div
                className="card-resumo card-hover"
                style={{ cursor: 'pointer' }}
                onClick={() => handleTipoClick(tipo)}
              >
                <span className="icon"><i className="bi bi-tag"></i></span>
                <div>
                  <div className="value">{quantidade}</div>
                  <div className="label">{tipo}</div>
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {/* Filtros Sticky */}
      <div className="filtro-sticky mb-4">
        <form method="get" className="row g-2 align-items-end">
          <input type="hidden" name="empresa" value={empresaFiltro} />
          <div className="col-auto">
            <label htmlFor="tipo_pendencia" className="form-label mb-0">Tipo de Pendência:</label>
            <select
              className="form-select"
              id="tipo_pendencia"
              name="tipo_pendencia"
              value={tipoFiltroAtual}
              onChange={handleTipoChange}
            >
              {data.tipos_pendencia?.map((tipo) => (
                <option key={tipo} value={tipo}>{tipo}</option>
              ))}
            </select>
          </div>
          <div className="col-auto">
            <Link
              to={`/dashboard?empresa=${empresaFiltro}`}
              className="btn btn-secondary"
            >
              Limpar
            </Link>
          </div>
        </form>
      </div>

      {/* Busca */}
      <div className="mb-3">
        <form onSubmit={handleBuscaSubmit} className="row g-2 align-items-end">
          <input type="hidden" name="empresa" value={empresaFiltro} />
          <input type="hidden" name="tipo_pendencia" value={tipoFiltroAtual} />
          <div className="col-md-3">
            <input
              type="text"
              className="form-control"
              name="busca"
              placeholder="Buscar por fornecedor, valor, etc."
              defaultValue={busca}
            />
          </div>
          <div className="col-md-1">
            <button type="submit" className="btn btn-primary">Pesquisar</button>
          </div>
        </form>
      </div>

      {/* Título e Botões */}
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1>Painel de Pendências</h1>
        {user?.tipo === 'adm' && (
          <Link to="/importar-planilha" className="btn btn-secondary">
            <i className="bi bi-upload"></i> Importar Planilha
          </Link>
        )}
      </div>

      {/* Tabela de Pendências */}
      <div className="card mb-4">
        <div className="card-body">
          <div className="table-responsive">
            <table className="table table-hover">
              <thead>
                <tr>
                  {data.colunas_tipo?.map((coluna) => {
                    if (coluna !== 'modificado_por') {
                      return (
                        <th key={coluna}>{data.todas_colunas?.[coluna] || coluna}</th>
                      )
                    }
                    return null
                  })}
                  <th>Ações</th>
                  <th>Modificado por</th>
                  <th>Anexo</th>
                </tr>
              </thead>
              <tbody>
                {data.pendencias && data.pendencias.length > 0 ? (
                  data.pendencias.map((pendencia) => (
                    <tr key={pendencia.id}>
                      {data.colunas_tipo?.map((coluna) => {
                        if (coluna === 'modificado_por') return null

                        let conteudo = '—'
                        if (coluna === 'tipo') {
                          conteudo = pendencia.tipo_pendencia
                        } else if (coluna === 'banco') {
                          conteudo = pendencia.banco || '—'
                        } else if (coluna === 'tipo_credito_debito') {
                          if (pendencia.tipo_credito_debito) {
                            return (
                              <td key={coluna}>
                                <span className={`badge ${pendencia.tipo_credito_debito === 'CREDITO' ? 'bg-success' : 'bg-danger'}`}>
                                  <i className={`bi bi-${pendencia.tipo_credito_debito === 'CREDITO' ? 'arrow-down-circle' : 'arrow-up-circle'}`}></i>
                                  {' '}{pendencia.tipo_credito_debito === 'CREDITO' ? 'Crédito' : 'Débito'}
                                </span>
                              </td>
                            )
                          }
                          conteudo = '—'
                        } else if (coluna === 'data') {
                          conteudo = formatarData(pendencia.data)
                        } else if (coluna === 'data_abertura') {
                          conteudo = formatarDataHora(pendencia.data_abertura)
                        } else if (coluna === 'fornecedor_cliente') {
                          conteudo = pendencia.fornecedor_cliente
                        } else if (coluna === 'valor') {
                          conteudo = formatarMoeda(pendencia.valor)
                        } else if (coluna === 'codigo_lancamento') {
                          conteudo = pendencia.codigo_lancamento || '—'
                        } else if (coluna === 'data_competencia') {
                          conteudo = formatarData(pendencia.data_competencia)
                        } else if (coluna === 'data_baixa') {
                          conteudo = formatarData(pendencia.data_baixa)
                        } else if (coluna === 'observacao') {
                          conteudo = pendencia.observacao || '—'
                        } else if (coluna === 'status') {
                          return (
                            <td key={coluna}>{getStatusBadge(pendencia.status)}</td>
                          )
                        }

                        return <td key={coluna}>{conteudo}</td>
                      })}
                      <td className="acoes-cell" style={{ textAlign: 'center' }}>
                        <button
                          type="button"
                          className="btn btn-sm btn-primary"
                          onClick={() => handleVerPendencia(pendencia)}
                          title="Verificar Pendência"
                        >
                          <i className="bi bi-eye"></i> Verificar
                        </button>
                      </td>
                      <td>
                        {pendencia.modificado_por === 'USUARIO' ? 'USUARIO' : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                      <td style={{ textAlign: 'center', verticalAlign: 'middle' }}>
                        {pendencia.nota_fiscal_arquivo ? (
                          <a
                            href={`/api/pendencia/${pendencia.id}/anexo`}
                            className="btn btn-sm btn-outline-primary"
                            title="Baixar anexo"
                          >
                            <i className="bi bi-download"></i> Anexo
                          </a>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={10} className="text-center">
                      Nenhuma pendência encontrada.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Links para outras páginas */}
      <div className="mt-3 d-flex gap-2">
        <Link
          to={`/pendencias-resolvidas?empresa=${empresaFiltro}`}
          className="btn btn-outline-success"
        >
          <i className="bi bi-check-circle"></i> Pendências Resolvidas
        </Link>
        <Link
          to={`/relatorio-mensal?empresa=${empresaFiltro}`}
          className="btn btn-outline-primary"
        >
          <i className="bi bi-calendar-month"></i> Relatório Mensal
        </Link>
      </div>

      {/* Modal Verificar Pendência */}
      {showModal && pendenciaSelecionada && (
        <div className="modal show d-block" tabIndex="-1" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}>
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header bg-primary text-white">
                <h5 className="modal-title">
                  <i className="bi bi-file-earmark-text"></i> Verificar Pendência #{pendenciaSelecionada.id} - {pendenciaSelecionada.empresa}
                </h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => {
                    setShowModal(false)
                    setPendenciaSelecionada(null)
                  }}
                ></button>
              </div>
              <div className="modal-body" style={{ maxHeight: '70vh', overflowY: 'auto' }}>
                {/* Informações da Pendência */}
                <div className="card mb-3">
                  <div className="card-header py-2 bg-light">
                    <h6 className="mb-0"><i className="bi bi-info-circle"></i> Informações da Pendência</h6>
                  </div>
                  <div className="card-body py-3">
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Empresa:</strong></div>
                      <div className="col-md-8">{pendenciaSelecionada.empresa}</div>
                    </div>
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Tipo:</strong></div>
                      <div className="col-md-8">{pendenciaSelecionada.tipo_pendencia}</div>
                    </div>
                    {pendenciaSelecionada.banco && (
                      <div className="row mb-2">
                        <div className="col-md-4"><strong>Banco:</strong></div>
                        <div className="col-md-8">{pendenciaSelecionada.banco}</div>
                      </div>
                    )}
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Data:</strong></div>
                      <div className="col-md-8">
                        {pendenciaSelecionada.data
                          ? formatarData(pendenciaSelecionada.data)
                          : pendenciaSelecionada.data_abertura
                            ? formatarDataHora(pendenciaSelecionada.data_abertura)
                            : <span className="text-muted">—</span>}
                      </div>
                    </div>
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Fornecedor/Cliente:</strong></div>
                      <div className="col-md-8">{pendenciaSelecionada.fornecedor_cliente}</div>
                    </div>
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Valor:</strong></div>
                      <div className="col-md-8">
                        <span className="text-primary fw-bold">{formatarMoeda(pendenciaSelecionada.valor)}</span>
                      </div>
                    </div>
                    {pendenciaSelecionada.codigo_lancamento && (
                      <div className="row mb-2">
                        <div className="col-md-4"><strong>Código Lançamento:</strong></div>
                        <div className="col-md-8">{pendenciaSelecionada.codigo_lancamento}</div>
                      </div>
                    )}
                    {pendenciaSelecionada.data_competencia && (
                      <div className="row mb-2">
                        <div className="col-md-4"><strong>Data Competência:</strong></div>
                        <div className="col-md-8">{formatarData(pendenciaSelecionada.data_competencia)}</div>
                      </div>
                    )}
                    {pendenciaSelecionada.data_baixa && (
                      <div className="row mb-2">
                        <div className="col-md-4"><strong>Data Baixa:</strong></div>
                        <div className="col-md-8">{formatarData(pendenciaSelecionada.data_baixa)}</div>
                      </div>
                    )}
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Status:</strong></div>
                      <div className="col-md-8">{getStatusBadge(pendenciaSelecionada.status)}</div>
                    </div>
                    <div className="row mb-2">
                      <div className="col-md-4"><strong>Observação:</strong></div>
                      <div className="col-md-8" style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                        {pendenciaSelecionada.observacao || '—'}
                      </div>
                    </div>
                    {pendenciaSelecionada.nota_fiscal_arquivo && (
                      <div className="row mb-2">
                        <div className="col-md-4"><strong>Anexo:</strong></div>
                        <div className="col-md-8">
                          <a
                            href={`/api/pendencia/${pendenciaSelecionada.id}/anexo`}
                            className="btn btn-sm btn-outline-primary"
                          >
                            <i className="bi bi-download"></i> Baixar Anexo
                          </a>
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* Motivo da Recusa */}
                {(pendenciaSelecionada.motivo_recusa || pendenciaSelecionada.motivo_recusa_supervisor) && (
                  <div className="card mb-3 border-warning">
                    <div className="card-header bg-warning text-dark py-2">
                      <h6 className="mb-0"><i className="bi bi-exclamation-triangle"></i> Motivo da Recusa</h6>
                    </div>
                    <div className="card-body py-3">
                      {pendenciaSelecionada.motivo_recusa_supervisor && (
                        <div className="alert alert-warning mb-2">
                          <strong><i className="bi bi-person-check"></i> Recusado pelo Supervisor:</strong>
                          <p className="mb-0 mt-2" style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                            {pendenciaSelecionada.motivo_recusa_supervisor}
                          </p>
                        </div>
                      )}
                      {pendenciaSelecionada.motivo_recusa && (
                        <div className="alert alert-warning mb-0">
                          <strong><i className="bi bi-person-gear"></i> Recusado pelo Operador:</strong>
                          <p className="mb-0 mt-2" style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                            {pendenciaSelecionada.motivo_recusa}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Primeira Resposta do Cliente */}
                {(pendenciaSelecionada.motivo_recusa || pendenciaSelecionada.motivo_recusa_supervisor) && pendenciaSelecionada.primeira_resposta && (
                  <div className="card mb-3 border-info">
                    <div className="card-header bg-info text-white py-2">
                      <h6 className="mb-0"><i className="bi bi-chat-left-quote"></i> Primeira Resposta do Cliente</h6>
                    </div>
                    <div className="card-body py-3" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                      <p className="mb-2" style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                        {pendenciaSelecionada.primeira_resposta.valor}
                      </p>
                      <small className="text-muted">
                        <i className="bi bi-clock"></i> Enviada em: {formatarDataHora(pendenciaSelecionada.primeira_resposta.data_hora)}
                      </small>
                    </div>
                  </div>
                )}

                {/* Resposta do Cliente */}
                {pendenciaSelecionada.resposta_cliente && (
                  <div className="card mb-3">
                    <div className="card-header bg-success text-white py-2">
                      <h6 className="mb-0"><i className="bi bi-chat-dots"></i> Resposta do Cliente</h6>
                    </div>
                    <div className="card-body py-3" style={{ maxHeight: '150px', overflowY: 'auto' }}>
                      <p className="mb-2" style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                        {pendenciaSelecionada.resposta_cliente}
                      </p>
                    </div>
                  </div>
                )}

                {/* Natureza de Operação */}
                {pendenciaSelecionada.natureza_operacao && (
                  <div className="card mb-3">
                    <div className="card-header bg-info text-white py-2">
                      <h6 className="mb-0"><i className="bi bi-gear"></i> Natureza de Operação</h6>
                    </div>
                    <div className="card-body py-3" style={{ maxHeight: '150px', overflowY: 'auto' }}>
                      <p className="mb-0" style={{ wordWrap: 'break-word', whiteSpace: 'pre-wrap' }}>
                        {pendenciaSelecionada.natureza_operacao}
                      </p>
                    </div>
                  </div>
                )}
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowModal(false)
                    setPendenciaSelecionada(null)
                  }}
                >
                  <i className="bi bi-x-circle"></i> Fechar
                </button>

                {/* Botões para ADMIN e SUPERVISOR */}
                {['adm', 'supervisor'].includes(user?.tipo) && pendenciaSelecionada.status !== 'RESOLVIDA' && (
                  <>
                    <Link
                      to={`/pendencia/${pendenciaSelecionada.id}/editar`}
                      className="btn btn-warning"
                    >
                      <i className="bi bi-pencil"></i> Editar
                    </Link>
                    <button
                      className="btn btn-success"
                      onClick={handleResolver}
                      disabled={resolverMutation.isLoading}
                    >
                      {resolverMutation.isLoading ? (
                        <span className="spinner-border spinner-border-sm me-1"></span>
                      ) : (
                        <i className="bi bi-check-circle"></i>
                      )}
                      Resolver
                    </button>
                    {user?.tipo === 'adm' && (
                      <button
                        className="btn btn-outline-danger"
                        onClick={handleExcluir}
                        disabled={excluirMutation.isLoading}
                      >
                        {excluirMutation.isLoading ? (
                          <span className="spinner-border spinner-border-sm me-1"></span>
                        ) : (
                          <i className="bi bi-trash"></i>
                        )}
                        Excluir
                      </button>
                    )}
                  </>
                )}

                {/* Botão para CLIENTE e CLIENTE SUPERVISOR */}
                {['cliente', 'cliente_supervisor'].includes(user?.tipo) && pendenciaSelecionada.status !== 'RESOLVIDA' && (
                  <Link
                    to={`/pendencia/${pendenciaSelecionada.id}`}
                    className="btn btn-primary"
                  >
                    <i className="bi bi-chat-dots"></i> Responder Pendência
                  </Link>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Dashboard
