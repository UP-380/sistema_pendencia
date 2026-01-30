import React from 'react'
import { useParams, Link, useNavigate } from 'react-router-dom'
import { useQuery } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function LogsPendencia() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { user } = useAuth()

  const { data, isLoading } = useQuery(
    ['logs-pendencia', id],
    async () => {
      const response = await api.get(`/api/pendencia/${id}/logs`)
      return response.data
    },
    { enabled: !!user && !!id }
  )

  const handleExportarCSV = async () => {
    try {
      window.open(`/exportar_logs/${id}`, '_blank')
    } catch (error) {
      console.error('Erro ao exportar:', error)
      alert('Erro ao exportar logs. Tente novamente.')
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

  const pendencia = data?.pendencia
  const logs = data?.logs || []

  if (!pendencia) {
    return (
      <div className="container mt-4">
        <div className="alert alert-warning">
          Pendência não encontrada.
        </div>
      </div>
    )
  }

  return (
    <div className="container mt-4">
      <h2>Logs da Pendência #{pendencia.id}</h2>
      
      {/* Informações da Pendência */}
      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0">Informações da Pendência</h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <p><strong>Empresa:</strong> {pendencia.empresa}</p>
              <p><strong>Fornecedor/Cliente:</strong> {pendencia.fornecedor_cliente}</p>
              <p><strong>Valor:</strong> R$ {pendencia.valor?.toFixed(2) || '0.00'}</p>
            </div>
            <div className="col-md-6">
              <p><strong>Status:</strong> {pendencia.status}</p>
              <p><strong>Tipo:</strong> {pendencia.tipo_pendencia}</p>
              {pendencia.nota_fiscal_arquivo ? (
                <p>
                  <strong>Anexo:</strong>{' '}
                  <a
                    href={`/static/${pendencia.nota_fiscal_arquivo}`}
                    className="btn btn-sm btn-outline-primary"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <i className="bi bi-download"></i> Baixar Anexo
                  </a>
                </p>
              ) : (
                <p><strong>Anexo:</strong> <span className="text-muted">Nenhum anexo</span></p>
              )}
            </div>
          </div>
        </div>
      </div>
      
      <div className="mb-3 d-flex justify-content-between align-items-center">
        <button onClick={() => navigate(-1)} className="btn btn-secondary">
          <i className="bi bi-arrow-left"></i> Voltar
        </button>
        <button onClick={handleExportarCSV} className="btn btn-outline-success">
          <i className="bi bi-download"></i> Exportar Logs (CSV)
        </button>
      </div>
      
      <div className="table-responsive">
        <table className="table table-striped table-bordered">
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
            {logs.length > 0 ? (
              logs.map((log) => (
                <tr
                  key={log.id}
                  style={
                    log.tipo_usuario === 'cliente' || log.campo_alterado === 'status'
                      ? { background: '#fff0f3', fontWeight: 'bold' }
                      : {}
                  }
                >
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
                  Nenhum log encontrado para esta pendência.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default LogsPendencia

