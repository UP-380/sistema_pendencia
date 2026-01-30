import React, { useState } from 'react'
import { useSearchParams, Link } from 'react-router-dom'
import { useQuery } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function PendenciasList() {
  const [searchParams, setSearchParams] = useSearchParams()
  const { user } = useAuth()
  
  const status = searchParams.get('status') || ''
  const empresa = searchParams.get('empresa') || ''
  const page = parseInt(searchParams.get('page') || '1')
  const perPage = parseInt(searchParams.get('per_page') || '50')

  const { data, isLoading } = useQuery(
    ['pendencias-list', status, empresa, page, perPage],
    async () => {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      if (empresa) params.append('empresa', empresa)
      params.append('page', page.toString())
      params.append('per_page', perPage.toString())
      
      const response = await api.get(`/api/pendencias?${params.toString()}`)
      return response.data
    },
    { enabled: !!user, keepPreviousData: true }
  )

  const handleFilterChange = (key, value) => {
    const newParams = new URLSearchParams(searchParams)
    if (value) {
      newParams.set(key, value)
    } else {
      newParams.delete(key)
    }
    newParams.set('page', '1') // Reset to first page on filter change
    setSearchParams(newParams)
  }

  const handlePageChange = (newPage) => {
    const newParams = new URLSearchParams(searchParams)
    newParams.set('page', newPage.toString())
    setSearchParams(newParams)
  }

  const handleExportarCSV = async () => {
    try {
      window.open(`/exportar_pendencias_csv?empresa=${empresa || ''}&status=${status || ''}`, '_blank')
    } catch (error) {
      console.error('Erro ao exportar:', error)
      alert('Erro ao exportar pendências. Tente novamente.')
    }
  }

  if (!['adm', 'supervisor', 'operador', 'cliente_supervisor'].includes(user?.tipo)) {
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
  const pagination = data?.pagination || {}
  const empresas = data?.empresas || []

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Listagem de Pendências</h2>
        <Link to="/dashboard" className="btn btn-secondary">
          <i className="bi bi-arrow-left"></i> Voltar ao Dashboard
        </Link>
      </div>

      {/* Breadcrumbs */}
      <nav aria-label="breadcrumb" className="mb-3">
        <ol className="breadcrumb">
          <li className="breadcrumb-item"><Link to="/empresas">Empresas</Link></li>
          {empresa && (
            <li className="breadcrumb-item">
              <Link to={`/dashboard?empresa=${encodeURIComponent(empresa)}`}>{empresa}</Link>
            </li>
          )}
          <li className="breadcrumb-item active">Pendências</li>
        </ol>
      </nav>

      {/* Filtros */}
      <div className="card mb-4">
        <div className="card-body">
          <form className="row g-3">
            <div className="col-md-3">
              <label htmlFor="empresa" className="form-label">Empresa</label>
              <select
                className="form-select"
                id="empresa"
                value={empresa}
                onChange={(e) => handleFilterChange('empresa', e.target.value)}
              >
                <option value="">Todas as empresas</option>
                {empresas.map(emp => (
                  <option key={emp} value={emp}>{emp}</option>
                ))}
              </select>
            </div>
            <div className="col-md-3">
              <label htmlFor="status" className="form-label">Status</label>
              <select
                className="form-select"
                id="status"
                value={status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
              >
                <option value="">Todos os status</option>
                <option value="PENDENTE CLIENTE">Pendente Cliente</option>
                <option value="PENDENTE OPERADOR UP">Pendente Operador UP</option>
                <option value="PENDENTE SUPERVISOR UP">Pendente Supervisor UP</option>
                <option value="PENDENTE COMPLEMENTO CLIENTE">Pendente Complemento Cliente</option>
                <option value="RESOLVIDA">Resolvida</option>
              </select>
            </div>
            <div className="col-md-2">
              <label htmlFor="per_page" className="form-label">Por página</label>
              <select
                className="form-select"
                id="per_page"
                value={perPage}
                onChange={(e) => handleFilterChange('per_page', e.target.value)}
              >
                <option value="25">25</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
            <div className="col-md-2 d-flex align-items-end">
              <button type="button" className="btn btn-primary w-100" onClick={() => {}}>
                <i className="bi bi-funnel"></i> Filtrar
              </button>
            </div>
            <div className="col-md-2 d-flex align-items-end">
              <Link to="/pendencias" className="btn btn-outline-secondary w-100">
                <i className="bi bi-x-circle"></i> Limpar
              </Link>
            </div>
          </form>
        </div>
      </div>

      {/* Estatísticas */}
      <div className="row mb-3">
        <div className="col-md-6">
          <div className="alert alert-info">
            <i className="bi bi-info-circle"></i>
            <strong>{pagination.total || 0}</strong> pendência{pagination.total !== 1 ? 's' : ''} encontrada{pagination.total !== 1 ? 's' : ''}
            {empresa && ` para ${empresa}`}
            {status && ` com status ${status}`}
          </div>
        </div>
        <div className="col-md-6 text-end">
          {pagination.total > 0 && (
            <button onClick={handleExportarCSV} className="btn btn-success">
              <i className="bi bi-download"></i> Exportar CSV
            </button>
          )}
        </div>
      </div>

      {/* Tabela */}
      {pendencias.length > 0 ? (
        <>
          <div className="table-responsive">
            <table className="table table-striped table-hover">
              <thead className="table-dark">
                <tr>
                  <th>ID</th>
                  <th>Empresa</th>
                  <th>Tipo</th>
                  <th>Status</th>
                  <th>Data da Pendência</th>
                  <th>Data de Abertura</th>
                  <th>Fornecedor/Cliente</th>
                  <th>Valor</th>
                  <th>Observação</th>
                  <th>Ações</th>
                </tr>
              </thead>
              <tbody>
                {pendencias.map((pendencia) => (
                  <tr key={pendencia.id}>
                    <td><strong>#{pendencia.id}</strong></td>
                    <td>{pendencia.empresa}</td>
                    <td>
                      <span className="badge bg-secondary">{pendencia.tipo_pendencia}</span>
                    </td>
                    <td>
                      <span className={`badge ${
                        pendencia.status === 'RESOLVIDA' ? 'bg-success' :
                        pendencia.status === 'PENDENTE CLIENTE' ? 'bg-warning' :
                        pendencia.status === 'PENDENTE OPERADOR UP' ? 'bg-info' :
                        pendencia.status === 'PENDENTE SUPERVISOR UP' ? 'bg-primary' :
                        'bg-secondary'
                      }`}>
                        {pendencia.status}
                      </span>
                    </td>
                    <td>
                      {pendencia.data ? new Date(pendencia.data).toLocaleDateString('pt-BR') : '—'}
                    </td>
                    <td>
                      {pendencia.data_abertura ? new Date(pendencia.data_abertura).toLocaleString('pt-BR') : '—'}
                    </td>
                    <td>{pendencia.fornecedor_cliente}</td>
                    <td>R$ {pendencia.valor?.toFixed(2) || '0.00'}</td>
                    <td>
                      {pendencia.observacao ? (
                        <span title={pendencia.observacao}>
                          {pendencia.observacao.length > 50 
                            ? `${pendencia.observacao.substring(0, 50)}...` 
                            : pendencia.observacao}
                        </span>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td>
                      <div className="btn-group" role="group">
                        <Link
                          to={`/pendencia/${pendencia.id}`}
                          className="btn btn-sm btn-outline-primary"
                          title="Ver detalhes"
                        >
                          <i className="bi bi-eye"></i>
                        </Link>
                        {['adm', 'supervisor'].includes(user?.tipo) && (
                          <Link
                            to={`/pendencia/${pendencia.id}/editar`}
                            className="btn btn-sm btn-outline-warning"
                            title="Editar"
                          >
                            <i className="bi bi-pencil"></i>
                          </Link>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Paginação */}
          {pagination.pages > 1 && (
            <nav aria-label="Paginação" className="mt-4">
              <ul className="pagination justify-content-center">
                {pagination.has_prev && (
                  <li className="page-item">
                    <button
                      className="page-link"
                      onClick={() => handlePageChange(pagination.prev_num)}
                    >
                      <i className="bi bi-chevron-left"></i> Anterior
                    </button>
                  </li>
                )}
                
                {Array.from({ length: Math.min(5, pagination.pages) }, (_, i) => {
                  let pageNum
                  if (pagination.pages <= 5) {
                    pageNum = i + 1
                  } else if (pagination.page <= 3) {
                    pageNum = i + 1
                  } else if (pagination.page >= pagination.pages - 2) {
                    pageNum = pagination.pages - 4 + i
                  } else {
                    pageNum = pagination.page - 2 + i
                  }
                  
                  return (
                    <li key={pageNum} className={`page-item ${pagination.page === pageNum ? 'active' : ''}`}>
                      <button
                        className="page-link"
                        onClick={() => handlePageChange(pageNum)}
                      >
                        {pageNum}
                      </button>
                    </li>
                  )
                })}
                
                {pagination.has_next && (
                  <li className="page-item">
                    <button
                      className="page-link"
                      onClick={() => handlePageChange(pagination.next_num)}
                    >
                      Próxima <i className="bi bi-chevron-right"></i>
                    </button>
                  </li>
                )}
              </ul>
            </nav>
          )}
        </>
      ) : (
        <div className="text-center py-5">
          <i className="bi bi-inbox display-1 text-muted"></i>
          <h4 className="mt-3 text-muted">Nenhuma pendência encontrada</h4>
          <p className="text-muted">
            {empresa && status
              ? `Nenhuma pendência ${status.toLowerCase()} para ${empresa} foi encontrada.`
              : empresa
              ? `Nenhuma pendência para ${empresa} foi encontrada.`
              : status
              ? `Nenhuma pendência com status ${status} foi encontrada.`
              : 'Nenhuma pendência foi encontrada.'}
          </p>
          <div className="mt-3">
            <Link to="/pendencias" className="btn btn-primary">
              <i className="bi bi-arrow-clockwise"></i> Ver todas as pendências
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}

export default PendenciasList

