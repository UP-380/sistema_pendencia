import React, { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../../services/api'
import { useAuth } from '../../contexts/AuthContext'

function GerenciarUsuarios() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [modalMode, setModalMode] = useState('create') // 'create' ou 'edit'
  const [usuarioSelecionado, setUsuarioSelecionado] = useState(null)
  const [formData, setFormData] = useState({
    email: '',
    senha: '',
    tipo: '',
    empresas_ids: [],
    ativo: true,
    permissoes: {}
  })

  const { data: usuariosData, isLoading } = useQuery(
    'usuarios',
    async () => {
      const response = await api.get('/api/usuarios')
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) }
  )

  const { data: empresasData } = useQuery(
    'empresas-admin',
    async () => {
      const response = await api.get('/api/admin/empresas')
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) }
  )

  const { data: funcionalidadesData } = useQuery(
    'funcionalidades',
    async () => {
      const response = await api.get('/api/funcionalidades')
      return response.data
    },
    { enabled: !!user && ['adm', 'supervisor'].includes(user?.tipo) && modalMode === 'edit' }
  )

  const criarMutation = useMutation(
    async (data) => {
      const response = await api.post('/api/usuario', data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('usuarios')
        setShowModal(false)
        resetForm()
      }
    }
  )

  const editarMutation = useMutation(
    async ({ id, data }) => {
      const response = await api.put(`/api/usuario/${id}`, data)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('usuarios')
        setShowModal(false)
        resetForm()
      }
    }
  )

  const excluirMutation = useMutation(
    async (id) => {
      const response = await api.delete(`/api/usuario/${id}`)
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries('usuarios')
      }
    }
  )

  const carregarUsuarioMutation = useMutation(
    async (id) => {
      const response = await api.get(`/api/usuario/${id}`)
      return response.data
    },
    {
      onSuccess: (data) => {
        setUsuarioSelecionado(data)
        setFormData({
          email: data.email,
          senha: '',
          tipo: data.tipo,
          empresas_ids: data.empresas_permitidas || [],
          ativo: data.ativo !== false,
          permissoes: data.permissoes || {}
        })
        setShowModal(true)
      }
    }
  )

  const resetForm = () => {
    setFormData({
      email: '',
      senha: '',
      tipo: '',
      empresas_ids: [],
      ativo: true,
      permissoes: {}
    })
    setUsuarioSelecionado(null)
  }

  const handleNovoUsuario = () => {
    setModalMode('create')
    resetForm()
    setShowModal(true)
  }

  const handleEditar = (usuario) => {
    setModalMode('edit')
    carregarUsuarioMutation.mutate(usuario.id)
  }

  const handleExcluir = (usuario) => {
    if (window.confirm(`Tem certeza que deseja excluir o usuário ${usuario.email}?`)) {
      excluirMutation.mutate(usuario.id)
    }
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    
    const dataToSend = {
      email: formData.email,
      tipo: formData.tipo,
      empresas_ids: formData.tipo !== 'adm' ? formData.empresas_ids : [],
      ativo: formData.ativo
    }

    if (modalMode === 'create') {
      dataToSend.senha = formData.senha
      criarMutation.mutate(dataToSend)
    } else {
      if (formData.senha) {
        dataToSend.nova_senha = formData.senha
      }
      dataToSend.permissoes = formData.permissoes
      editarMutation.mutate({ id: usuarioSelecionado.id, data: dataToSend })
    }
  }

  const handleTipoChange = (e) => {
    const tipo = e.target.value
    setFormData(prev => ({
      ...prev,
      tipo,
      empresas_ids: tipo === 'adm' ? [] : prev.empresas_ids
    }))
  }

  const toggleEmpresa = (empresaId) => {
    setFormData(prev => ({
      ...prev,
      empresas_ids: prev.empresas_ids.includes(empresaId)
        ? prev.empresas_ids.filter(id => id !== empresaId)
        : [...prev.empresas_ids, empresaId]
    }))
  }

  const togglePermissao = (funcionalidade) => {
    setFormData(prev => ({
      ...prev,
      permissoes: {
        ...prev.permissoes,
        [funcionalidade]: !prev.permissoes[funcionalidade]
      }
    }))
  }

  const getPermissaoPadrao = (funcionalidade) => {
    if (!funcionalidadesData) return false
    return funcionalidadesData.permissoes_padrao_operador[funcionalidade] || false
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
        <h2>Gerenciar Usuários</h2>
        <button className="btn btn-primary" onClick={handleNovoUsuario}>
          <i className="bi bi-plus-circle me-2"></i>
          Novo Usuário
        </button>
      </div>

      <div className="table-responsive">
        <table className="table table-hover table-striped">
          <thead>
            <tr>
              <th>Email</th>
              <th>Tipo</th>
              <th>Empresas Permitidas</th>
              <th>Status</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            {usuariosData?.usuarios?.map((usuario) => (
              <tr key={usuario.id}>
                <td>{usuario.email}</td>
                <td>
                  <span className="badge bg-secondary">{usuario.tipo}</span>
                </td>
                <td>
                  {usuario.tipo === 'adm' ? (
                    <span className="badge bg-success">Todas as empresas</span>
                  ) : usuario.empresas && usuario.empresas.length > 0 ? (
                    usuario.empresas.map((emp) => (
                      <span key={emp.id} className="badge bg-primary me-1">
                        {emp.nome}
                      </span>
                    ))
                  ) : (
                    <span className="badge bg-warning">Nenhuma empresa</span>
                  )}
                </td>
                <td>
                  <span className={`badge ${usuario.ativo !== false ? 'bg-success' : 'bg-danger'}`}>
                    {usuario.ativo !== false ? 'Ativo' : 'Inativo'}
                  </span>
                </td>
                <td>
                  <button
                    className="btn btn-sm btn-outline-primary me-2"
                    onClick={() => handleEditar(usuario)}
                  >
                    <i className="bi bi-pencil"></i> Editar
                  </button>
                  <button
                    className="btn btn-sm btn-outline-danger"
                    onClick={() => handleExcluir(usuario)}
                  >
                    <i className="bi bi-trash"></i> Excluir
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Modal Criar/Editar Usuário */}
      {showModal && (
        <div className="modal show d-block" style={{ backgroundColor: 'rgba(0,0,0,0.5)' }} tabIndex="-1">
          <div className="modal-dialog modal-lg">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">
                  {modalMode === 'create' ? 'Novo Usuário' : 'Editar Usuário'}
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
                    <label className="form-label">Email *</label>
                    <input
                      type="email"
                      className="form-control"
                      value={formData.email}
                      onChange={(e) => setFormData(prev => ({ ...prev, email: e.target.value }))}
                      required
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label">
                      {modalMode === 'create' ? 'Senha *' : 'Nova Senha (deixe em branco para manter)'}
                    </label>
                    <input
                      type="password"
                      className="form-control"
                      value={formData.senha}
                      onChange={(e) => setFormData(prev => ({ ...prev, senha: e.target.value }))}
                      required={modalMode === 'create'}
                    />
                  </div>

                  <div className="mb-3">
                    <label className="form-label">Tipo de Usuário *</label>
                    <select
                      className="form-select"
                      value={formData.tipo}
                      onChange={handleTipoChange}
                      required
                    >
                      <option value="">Selecione...</option>
                      <option value="adm">Administrador</option>
                      <option value="supervisor">Supervisor</option>
                      <option value="operador">Operador</option>
                      <option value="cliente">Cliente</option>
                      <option value="cliente_supervisor">Cliente Supervisor</option>
                    </select>
                  </div>

                  {formData.tipo && formData.tipo !== 'adm' && empresasData?.empresas && (
                    <div className="mb-3">
                      <label className="form-label">Empresas Permitidas</label>
                      <div className="border rounded p-3" style={{ maxHeight: '200px', overflowY: 'auto' }}>
                        {empresasData.empresas.map((empresa) => (
                          <div key={empresa.id} className="form-check">
                            <input
                              className="form-check-input"
                              type="checkbox"
                              checked={formData.empresas_ids.includes(empresa.id)}
                              onChange={() => toggleEmpresa(empresa.id)}
                            />
                            <label className="form-check-label">
                              {empresa.nome}
                            </label>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {modalMode === 'edit' && funcionalidadesData && (
                    <div className="mb-3">
                      <label className="form-label">Permissões do Usuário</label>
                      <div className="border rounded p-3" style={{ maxHeight: '300px', overflowY: 'auto' }}>
                        {funcionalidadesData.funcionalidades.map(([categoria, funcionalidades]) => (
                          <div key={categoria} className="mb-3">
                            <h6 className="text-primary">{categoria}</h6>
                            {funcionalidades.map(([func, nome]) => (
                              <div key={func} className="form-check">
                                <input
                                  className="form-check-input"
                                  type="checkbox"
                                  checked={formData.permissoes[func] !== undefined 
                                    ? formData.permissoes[func] 
                                    : getPermissaoPadrao(func)}
                                  onChange={() => togglePermissao(func)}
                                />
                                <label className="form-check-label">{nome}</label>
                              </div>
                            ))}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}

                  {modalMode === 'edit' && (
                    <div className="mb-3">
                      <div className="form-check">
                        <input
                          className="form-check-input"
                          type="checkbox"
                          checked={formData.ativo}
                          onChange={(e) => setFormData(prev => ({ ...prev, ativo: e.target.checked }))}
                        />
                        <label className="form-check-label">Usuário Ativo</label>
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

export default GerenciarUsuarios
