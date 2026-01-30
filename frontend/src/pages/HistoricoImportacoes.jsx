import React from 'react'
import { useQuery } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function HistoricoImportacoes() {
  const { user } = useAuth()

  const { data, isLoading } = useQuery(
    'historico-importacoes',
    async () => {
      const response = await api.get('/api/historico-importacoes')
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
    <div className="container">
      <h2 className="mb-4">Histórico de Importações</h2>
      
      {data?.importacoes && data.importacoes.length > 0 ? (
        <div className="table-responsive">
          <table className="table table-hover">
            <thead>
              <tr>
                <th>Data/Hora</th>
                <th>Arquivo</th>
                <th>Usuário</th>
                <th>Status</th>
                <th>Mensagem</th>
              </tr>
            </thead>
            <tbody>
              {data.importacoes.map((imp) => (
                <tr key={imp.id}>
                  <td>{new Date(imp.data_hora).toLocaleString('pt-BR')}</td>
                  <td>{imp.nome_arquivo}</td>
                  <td>{imp.usuario}</td>
                  <td>
                    <span className={`badge ${
                      imp.status === 'CONCLUIDO' || imp.status === 'Sucesso' ? 'bg-success' :
                      imp.status === 'ERRO' || imp.status === 'Erro' ? 'bg-danger' :
                      'bg-warning'
                    }`}>
                      {imp.status}
                    </span>
                  </td>
                  <td>{imp.mensagem_erro || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="alert alert-info">
          Nenhuma importação encontrada.
        </div>
      )}
    </div>
  )
}

export default HistoricoImportacoes
