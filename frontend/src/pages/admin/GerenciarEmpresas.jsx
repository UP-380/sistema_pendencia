import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'

function GerenciarEmpresas() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [showModalExcluir, setShowModalExcluir] = useState(false)
  const [showModalImpedimento, setShowModalImpedimento] = useState(false)
  const [modalMode, setModalMode] = useState('create')
  const [empresaSelecionada, setEmpresaSelecionada] = useState(null)
  const [motivoImpedimento, setMotivoImpedimento] = useState(null)
  const [formData, setFormData] = useState({
    nome: '',
    segmento_id: ''
  })

  const { data: empresasData, isLoading } = useQuery(
    'empresas-admin',
    async () => {
      const response = await api.get('/api/admin/empresas')
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) }
  )

  const { data: segmentosData } = useQuery(
    'segmentos-admin',
    async () => {
      const response = await api.get('/api/admin/segmentos')
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) }
  )

  const criarMutation = useMutation(
    async (data) => {
      const response = await api.post('/api/admin/empresa', data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('empresas-admin')
        setShowModal(false)
        resetForm()
      }
    }
  )

  const editarMutation = useMutation(
    async ({ id, data }) => {
      const response = await api.put(`/api/admin/empresa/${id}`, data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('empresas-admin')
        setShowModal(false)
        resetForm()
      }
    }
  )

  const excluirMutation = useMutation(
    async (id) => {
      const response = await api.delete(`/api/admin/empresa/${id}`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('empresas-admin')
        setShowModalExcluir(false)
        setEmpresaSelecionada(null)
      },
      onError: (error) => {
        if (error.response?.data?.error) {
          setMotivoImpedimento(error.response.data)
          setShowModalExcluir(false)
          setShowModalImpedimento(true)
        }
      }
    }
  )

  const resetForm = () => {
    setFormData({
      nome: '',
      segmento_id: ''
    })
    setEmpresaSelecionada(null)
  }

  const handleNovaEmpresa = () => {
    setModalMode('create')
    resetForm()
    setShowModal(true)
  }

  const handleEditar = async (empresa) => {
    try {
      const response = await api.get(`/api/admin/empresa/${empresa.id}`)
      const data = response.data
      setModalMode('edit')
      setEmpresaSelecionada(data)
      setFormData({
        nome: data.nome,
        segmento_id: data.segmento_id || ''
      })
      setShowModal(true)
    } catch (error) {
      console.error('Erro ao carregar empresa:', error)
    }
  }

  const handleConfirmarExcluir = () => {
    if (empresaSelecionada) {
      excluirMutation.mutate(empresaSelecionada.id)
    }
  }

  const handleTentarExcluir = (empresa) => {
    setEmpresaSelecionada(empresa)
    setShowModalExcluir(true)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const dataToSend = {
      nome: formData.nome,
      segmento_id: formData.segmento_id || null
    }

    if (modalMode === 'create') {
      criarMutation.mutate(dataToSend)
    } else {
      editarMutation.mutate({ id: empresaSelecionada.id, data: dataToSend })
    }
  }

  // Agrupar empresas por segmento para o resumo
  const resumoPorSegmento = {}
  empresasData?.empresas?.forEach(emp => {
    const segNome = emp.segmento_nome || 'Sem Segmento'
    resumoPorSegmento[segNome] = (resumoPorSegmento[segNome] || 0) + 1
  })

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
        <h2>Gerenciar Empresas</h2>
        <button className="btn btn-primary" onClick={handleNovaEmpresa}>
          <i className="bi bi-plus-circle me-2"></i>
          Nova Empresa
        </button>
      </div>

      {/* Resumo por Segmento */}
      <div className="row g-3 mb-4">
        {Object.entries(resumoPorSegmento).map(([segmento, quantidade]) => (
          <div key={segmento} className="col-md-3 col-sm-6">
            <div className={`card ${segmento === 'Sem Segmento' ? 'bg-secondary' : 'bg-primary'} text-white`}>
              <div className="card-body text-center">
                <h5 className="card-title">{segmento}</h5>
                <h2 className="mb-0">{quantidade}</h2>
                <small>empresa{quantidade !== 1 ? 's' : ''}</small>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="table-responsive">
        <table className="table table-hover table-striped">
          <thead>
            <tr>
              <th>ID</th>
              <th>Nome</th>
              <th>Segmento</th>
              <th>Usuários</th>
              <th>Pendências</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {empresasData?.empresas?.map((empresa) => (
              <tr key={empresa.id}>
                <td>
                  <span className="badge bg-secondary">{empresa.id}</span>
                </td>
                <td>
                  <strong>{empresa.nome}</strong>
                </td>
                <td>
                  {empresa.segmento_nome ? (
                    <span className="badge bg-primary">{empresa.segmento_nome}</span>
                  ) : (
                    <span className="badge bg-secondary">Sem Segmento</span>
                  )}
                </td>
                <td>
                  <span className="badge bg-info">{empresa.total_usuarios}</span>
                </td>
                <td>
                  <span className={`badge ${empresa.total_pendencias > 0 ? 'bg-warning' : 'bg-success'}`}>
                    {empresa.total_pendencias}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-sm btn-outline-primary me-2"
                    onClick={() => handleEditar(empresa)}
                  >
                    <i className="bi bi-pencil"></i> Editar
                  </button>
                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleTentarExcluir(empresa)}
                    disabled={empresa.total_pendencias > 0 || empresa.total_usuarios > 0}
                  >
                    <i className="bi bi-trash"></i> Excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Criar/Editar Empresa */}
      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {modalMode === 'create' ? 'Nova Empresa' : 'Editar Empresa'}
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
                    <label className="form-label">Nome da Empresa *</label>
                    <input
                      type="text"
                      className="form-control"
                      placeholder="Ex: ALIANZE, AUTOBRAS, PLANO PAI, etc."
                      value={formData.nome}
                      onChange={(e) => setFormData(prev => ({ ...prev, nome: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Segmento</label>
                    <select
                      className="form-select"
                      value={formData.segmento_id}
                      onChange={(e) => setFormData(prev => ({ ...prev, segmento_id: e.target.value }))}
                    >
                      <option value="">-- Sem Segmento --</option>
                      {segmentosData?.segmentos?.map((seg) => (
                        <option key={seg.id} value={seg.id}>
                          {seg.nome}
                        </option>
                      ))}
                    </select>
                  </div>

                  {modalMode === 'edit' && empresaSelecionada && (
                    <div className="alert alert-info">
                      <strong>ID:</strong> {empresaSelecionada.id}<br />
                      <strong>Segmento Atual:</strong> {empresaSelecionada.segmento_nome || 'Sem Segmento'}<br />
                      <strong>Usuários Vinculados:</strong> {empresaSelecionada.total_usuarios}
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

      {/* Modal Confirmação Exclusão */}
      {showModalExcluir && empresaSelecionada && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header bg-danger text-white">
                <h5 className="modal-title">Confirmar Exclusão</h5>
                <button
                  type="button"
                  className="btn-close btn-close-white"
                  onClick={() => {
                    setShowModalExcluir(false)
                    setEmpresaSelecionada(null)
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <p>Tem certeza que deseja excluir a empresa <strong>{empresaSelecionada.nome}</strong>?</p>
                <p className="text-danger"><strong>Esta ação é irreversível!</strong></p>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => {
                    setShowModalExcluir(false)
                    setEmpresaSelecionada(null)
                  }}
                >
                  Cancelar
                </button>
                <button
                  type="button"
                  className="btn btn-danger"
                  onClick={handleConfirmarExcluir}
                >
                  Sim, Excluir
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Modal Impedimento de Exclusão */}
      {showModalImpedimento && motivoImpedimento && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog">
            <div className="modal-content">
              <div className="modal-header bg-warning">
                <h5 className="modal-title">Não é possível excluir</h5>
                <button
                  type="button"
                  className="btn-close"
                  onClick={() => {
                    setShowModalImpedimento(false)
                    setMotivoImpedimento(null)
                  }}
                ></button>
              </div>
              <div className="modal-body">
                <p><strong>{motivoImpedimento.error}</strong></p>
                {motivoImpedimento.total_pendencias > 0 && (
                  <p>Pendências vinculadas: <strong>{motivoImpedimento.total_pendencias}</strong></p>
                )}
                {motivoImpedimento.total_usuarios > 0 && (
                  <p>Usuários vinculados: <strong>{motivoImpedimento.total_usuarios}</strong></p>
                )}
                <p className="mt-3">Para excluir esta empresa, é necessário:</p>
                <ul>
                  {motivoImpedimento.total_pendencias > 0 && (
                    <li>Resolver ou excluir todas as pendências vinculadas</li>
                  )}
                  {motivoImpedimento.total_usuarios > 0 && (
                    <li>Remover todos os usuários vinculados</li>
                  )}
                </ul>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => {
                    setShowModalImpedimento(false)
                    setMotivoImpedimento(null)
                  }}
                >
                  Entendi
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default GerenciarEmpresas
