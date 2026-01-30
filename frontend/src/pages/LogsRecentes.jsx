import React from 'react'
import { useQuery } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function LogsRecentes() {
  const { user } = useAuth()

  const { data, isLoading } = useQuery(
    'logs-recentes',
    async () => {
      const response = await api.get('/api/logs-recentes')
      return response.data
    },
    { enabled: !!user }
  )

  if (!['adm', 'supervisor', 'cliente_supervisor'].includes(user?.tipo)) {
    return (
      <div className="alert alert-danger">
        Você não tem permissão para acessar esta página.
      </div>
    )
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
    <div className="container">
      <h2 className="mb-4">Logs Recentes</h2>
      
      {data?.logs && data.logs.length > 0 ? (
        <div className="table-responsive">
          <table className="table table-hover">
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
              {data.logs.map((log) => (
                <tr key={log.id}>
                  <td>{new Date(log.data_hora).toLocaleString('pt-BR')}</td>
                  <td>{log.usuario}</td>
                  <td>{log.tipo_usuario}</td>
                  <td>{log.acao}</td>
                  <td>{log.campo_alterado || '—'}</td>
                  <td>{log.valor_anterior || '—'}</td>
                  <td>{log.valor_novo || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="alert alert-info">
          Nenhum log encontrado.
        </div>
      )}
    </div>
  )
}

export default LogsRecentes
