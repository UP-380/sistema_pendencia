import React, { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function VerPendencia() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const [resposta, setResposta] = useState('')
  const [arquivo, setArquivo] = useState(null)

  const { data: pendencia, isLoading } = useQuery(
    ['pendencia', id],
    async () => {
      const response = await api.get(`/api/pendencia/${id}`)
      return response.data
    }
  )

  const responderMutation = useMutation(
    async (data) => {
      const response = await api.post(`/api/pendencia/${id}/responder`, data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['pendencia', id])
        queryClient.invalidateQueries(['dashboard'])
        navigate('/dashboard')
      }
    }
  )

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!resposta.trim()) {
      alert('Por favor, preencha a resposta')
      return
    }
    responderMutation.mutate({ resposta_cliente: resposta })
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

  if (!pendencia) {
    return (
      <div className="alert alert-danger">
        Pendência não encontrada.
      </div>
    )
  }

  return (
    <div className="container">
      <h2 className="mb-4">Responder Pendência #{id}</h2>
      
      <div className="card mb-4">
        <div className="card-header">
          <h5 className="mb-0">Detalhes da Pendência</h5>
        </div>
        <div className="card-body">
          <div className="row">
            <div className="col-md-6">
              <p><strong>Empresa:</strong> {pendencia.empresa}</p>
              <p><strong>Tipo:</strong> {pendencia.tipo_pendencia}</p>
              <p><strong>Banco:</strong> {pendencia.banco || '—'}</p>
              <p><strong>Data:</strong> {pendencia.data ? new Date(pendencia.data).toLocaleDateString('pt-BR') : '—'}</p>
              <p><strong>Fornecedor/Cliente:</strong> {pendencia.fornecedor_cliente}</p>
              <p><strong>Valor:</strong> R$ {pendencia.valor?.toFixed(2) || '0.00'}</p>
            </div>
            <div className="col-md-6">
              <p><strong>Status:</strong> 
                <span className={`badge ms-2 ${
                  pendencia.status === 'RESOLVIDA' ? 'bg-success' :
                  pendencia.status?.includes('PENDENTE') ? 'bg-warning' :
                  'bg-danger'
                }`}>
                  {pendencia.status}
                </span>
              </p>
              <p><strong>Observação:</strong> {pendencia.observacao || '—'}</p>
              {pendencia.resposta_cliente && (
                <div className="alert alert-info">
                  <strong>Resposta Anterior:</strong>
                  <p className="mb-0">{pendencia.resposta_cliente}</p>
                </div>
              )}
              {(pendencia.motivo_recusa || pendencia.motivo_recusa_supervisor) && (
                <div className="alert alert-warning">
                  <strong>Motivo da Recusa:</strong>
                  {pendencia.motivo_recusa && (
                    <p className="mb-1">Operador: {pendencia.motivo_recusa}</p>
                  )}
                  {pendencia.motivo_recusa_supervisor && (
                    <p className="mb-0">Supervisor: {pendencia.motivo_recusa_supervisor}</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {pendencia.status !== 'RESOLVIDA' && (
        <div className="card">
          <div className="card-header">
            <h5 className="mb-0">Responder Pendência</h5>
          </div>
          <div className="card-body">
            <form onSubmit={handleSubmit}>
              <div className="mb-3">
                <label htmlFor="resposta" className="form-label">
                  {pendencia.resposta_cliente ? 'Complementar Resposta' : 'Resposta'}
                </label>
                <textarea
                  className="form-control"
                  id="resposta"
                  rows="5"
                  value={resposta}
                  onChange={(e) => setResposta(e.target.value)}
                  required
                  placeholder="Digite sua resposta aqui..."
                ></textarea>
              </div>
              <div className="mb-3">
                <label htmlFor="arquivo" className="form-label">
                  Anexar Documento (Opcional)
                </label>
                <input
                  type="file"
                  className="form-control"
                  id="arquivo"
                  accept=".pdf,.jpg,.jpeg,.png"
                  onChange={(e) => setArquivo(e.target.files[0])}
                />
                <small className="form-text text-muted">
                  Formatos aceitos: PDF, JPG, PNG
                </small>
              </div>
              <div className="d-flex gap-2">
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={responderMutation.isLoading}
                >
                  {responderMutation.isLoading ? (
                    <>
                      <span className="spinner-border spinner-border-sm me-2"></span>
                      Enviando...
                    </>
                  ) : (
                    <>
                      <i className="bi bi-send me-2"></i>
                      {pendencia.resposta_cliente ? 'Complementar Resposta' : 'Enviar Resposta'}
                    </>
                  )}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => navigate('/dashboard')}
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default VerPendencia
