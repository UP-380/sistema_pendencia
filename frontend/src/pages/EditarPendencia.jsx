import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function EditarPendencia() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  
  const [formData, setFormData] = useState({
    tipo_pendencia: '',
    banco: '',
    data: '',
    fornecedor_cliente: '',
    valor: '',
    observacao: '',
    status: ''
  })

  const { data: pendencia, isLoading } = useQuery(
    ['pendencia', id],
    async () => {
      const response = await api.get(`/api/pendencia/${id}`)
      return response.data
    }
  )

  useEffect(() => {
    if (pendencia) {
      setFormData({
        tipo_pendencia: pendencia.tipo_pendencia || '',
        banco: pendencia.banco || '',
        data: pendencia.data ? pendencia.data.split('T')[0] : '',
        fornecedor_cliente: pendencia.fornecedor_cliente || '',
        valor: pendencia.valor ? pendencia.valor.toFixed(2) : '',
        observacao: pendencia.observacao || '',
        status: pendencia.status || ''
      })
    }
  }, [pendencia])

  const editarMutation = useMutation(
    async (data) => {
      const response = await api.put(`/api/pendencia/${id}`, data)
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

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    editarMutation.mutate(formData)
  }

  if (!['adm', 'supervisor'].includes(user?.tipo)) {
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
      <h2 className="mb-4">Editar Pendência #{id}</h2>
      
      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="row">
              <div className="col-md-6 mb-3">
                <label className="form-label">Tipo de Pendência</label>
                <input
                  type="text"
                  className="form-control"
                  name="tipo_pendencia"
                  value={formData.tipo_pendencia}
                  onChange={handleChange}
                  readOnly
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Banco</label>
                <input
                  type="text"
                  className="form-control"
                  name="banco"
                  value={formData.banco}
                  onChange={handleChange}
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Data</label>
                <input
                  type="date"
                  className="form-control"
                  name="data"
                  value={formData.data}
                  onChange={handleChange}
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Fornecedor/Cliente</label>
                <input
                  type="text"
                  className="form-control"
                  name="fornecedor_cliente"
                  value={formData.fornecedor_cliente}
                  onChange={handleChange}
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Valor</label>
                <input
                  type="text"
                  className="form-control"
                  name="valor"
                  value={formData.valor}
                  onChange={handleChange}
                  placeholder="0.00"
                />
              </div>

              <div className="col-md-6 mb-3">
                <label className="form-label">Status</label>
                <select
                  className="form-select"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                >
                  <option value="PENDENTE CLIENTE">PENDENTE CLIENTE</option>
                  <option value="PENDENTE OPERADOR UP">PENDENTE OPERADOR UP</option>
                  <option value="PENDENTE SUPERVISOR">PENDENTE SUPERVISOR</option>
                  <option value="PENDENTE COMPLEMENTO CLIENTE">PENDENTE COMPLEMENTO CLIENTE</option>
                  <option value="RESOLVIDA">RESOLVIDA</option>
                </select>
              </div>

              <div className="col-md-12 mb-3">
                <label className="form-label">Observação</label>
                <textarea
                  className="form-control"
                  name="observacao"
                  value={formData.observacao}
                  onChange={handleChange}
                  rows="3"
                ></textarea>
              </div>
            </div>

            {editarMutation.isError && (
              <div className="alert alert-danger">
                {editarMutation.error?.response?.data?.error || 'Erro ao editar pendência'}
              </div>
            )}

            <div className="d-flex gap-2">
              <button
                type="submit"
                className="btn btn-primary"
                disabled={editarMutation.isLoading}
              >
                {editarMutation.isLoading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Salvando...
                  </>
                ) : (
                  <>
                    <i className="bi bi-save me-2"></i>
                    Salvar Alterações
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
    </div>
  )
}

export default EditarPendencia
