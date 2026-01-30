import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'

function GerenciarSegmentos() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [segmentoSelecionado, setSegmentoSelecionado] = useState(null)
  const [formData, setFormData] = useState({
    nome: ''
  })

  const { data: segmentosData, isLoading } = useQuery(
    'segmentos-admin',
    async () => {
      const response = await api.get('/api/admin/segmentos')
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) }
  )

  const criarMutation = useMutation(
    async (data) => {
      const response = await api.post('/api/admin/segmento', data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('segmentos-admin')
        setShowModal(false)
        resetForm()
      }
    }
  )

  const editarMutation = useMutation(
    async ({ id, data }) => {
      const response = await api.put(`/api/admin/segmento/${id}`, data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('segmentos-admin')
        setShowModal(false)
        resetForm()
      }
    }
  )

  const excluirMutation = useMutation(
    async (id) => {
      const response = await api.delete(`/api/admin/segmento/${id}`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('segmentos-admin')
      },
      onError: (error) => {
        if (error.response?.data?.error) {
          alert(error.response.data.error)
        }
      }
    }
  )

  const resetForm = () => {
    setFormData({
      nome: ''
    })
    setSegmentoSelecionado(null)
  }

  const handleNovoSegmento = () => {
    setModalMode('create')
    resetForm()
    setShowModal(true)
  }

  const handleEditar = async (segmento) => {
    try {
      const response = await api.get(`/api/admin/segmento/${segmento.id}`)
      const data = response.data
      setModalMode('edit')
      setSegmentoSelecionado(data)
      setFormData({
        nome: data.nome
      })
      setShowModal(true)
    } catch (error) {
      console.error('Erro ao carregar segmento:', error)
    }
  }

  const handleExcluir = (segmento) => {
    if (segmento.total_empresas > 0) {
      alert(`Não é possível excluir o segmento "${segmento.nome}" pois ele possui ${segmento.total_empresas} empresa(s) vinculada(s).`)
      return
    }

    if (window.confirm(`Tem certeza que deseja excluir o segmento "${segmento.nome}"?`)) {
      excluirMutation.mutate(segmento.id)
    }
  }

  const handleVerEmpresas = (segmentoId) => {
    navigate(`/segmento/${segmentoId}`)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const dataToSend = {
      nome: formData.nome.trim().toUpperCase()
    }

    if (modalMode === 'create') {
      criarMutation.mutate(dataToSend)
    } else {
      editarMutation.mutate({ id: segmentoSelecionado.id, data: dataToSend })
    }
  }

  const getSegmentoIcon = (nome) => {
    const nomeUpper = nome.toUpperCase()
    if (nomeUpper.includes('FUNERÁRIA') || nomeUpper.includes('FUNERARIA')) {
      return '❤️'
    } else if (nomeUpper.includes('PROTEÇÃO') || nomeUpper.includes('VEICULAR')) {
      return '🛡️'
    } else if (nomeUpper.includes('FARMÁCIA') || nomeUpper.includes('FARMACIA')) {
      return '💊'
    }
    return '📁'
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
      <div className="d-flex justify-content-center align-items-center" style={{ minHeight: '50vh' }}>
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Carregando...</span>
        </div>
      </div>
    )
  }

  return (
    <div className="container mt-4">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h2>Gerenciar Segmentos</h2>
        <button className="btn btn-primary" onClick={handleNovoSegmento}>
          <i className="bi bi-plus-circle me-2"></i>
          Novo Segmento
        </button>
      </div>

      <div className="table-responsive">
        <table className="table table-hover table-striped">
          <thead>
            <tr>
              <th>Nome do Segmento</th>
              <th>Total de Empresas</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {segmentosData?.segmentos?.map((segmento) => (
              <tr key={segmento.id}>
                <td>
                  <strong>
                    <span className="me-2">{getSegmentoIcon(segmento.nome)}</span>
                    {segmento.nome}
                  </strong>
                </td>
                <td>
                  <span className="badge bg-primary rounded-pill">{segmento.total_empresas}</span>
                </td>
                <td>
                  <button
                    className="btn btn-sm btn-outline-info me-2"
                    onClick={() => handleVerEmpresas(segmento.id)}
                    title="Ver Empresas"
                  >
                    <i className="bi bi-eye"></i>
                  </button>
                  <button
                    className="btn btn-sm btn-outline-primary me-2"
                    onClick={() => handleEditar(segmento)}
                    title="Editar"
                  >
                    <i className="bi bi-pencil"></i>
                  </button>
                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleExcluir(segmento)}
                    disabled={segmento.total_empresas > 0 || user?.tipo !== 'adm'}
                    title="Excluir"
                  >
                    <i className="bi bi-trash"></i>
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Criar/Editar Segmento */}
      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {modalMode === 'create' ? 'Novo Segmento' : 'Editar Segmento'}
                </h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowModal(false)
                    resetForm()
                  }}
                ></button>
              </div>
              <form onSubmit={handleSubmit}>
                <div className="modal-body">
                  <div className="mb-3">
                    <label className="form-label">Nome do Segmento *</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Ex: PROTEÇÃO VEICULAR, FUNERÁRIA, FARMÁCIA"
                      value={formData.nome}
                      onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                      required
                    />
                    <small className="form-text text-muted">
                      O nome será convertido automaticamente para MAIÚSCULAS.
                    </small>
                  </div>

                  {modalMode === 'edit' && segmentoSelecionado && (
                    <div className="alert alert-info">
                      <strong>Total de Empresas Vinculadas:</strong> {segmentoSelecionado.total_empresas}
                    </div>
                  )}
                </div>
                <div className="modal-footer">
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => {
                      setShowModal(false)
                      resetForm()
                    }}
                  >
                    Cancelar
                  </button>
                  <button type="submit" className="btn btn-primary">
                    {modalMode === 'create' ? 'Criar' : 'Salvar'}
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GerenciarSegmentos
