import React, { useState, useEffect } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from 'react-query'
import api from '../services/api'
import { useAuth } from '../contexts/AuthContext'

function NovaPendencia() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const { user } = useAuth()
  const empresaPreselecionada = searchParams.get('empresa')

  const [formData, setFormData] = useState({
    empresa: empresaPreselecionada || '',
    tipo_pendencia: '',
    banco: '',
    data: '',
    fornecedor_cliente: '',
    valor: '',
    codigo_lancamento: '',
    data_competencia: '',
    data_baixa: '',
    natureza_sistema: '',
    tipo_credito_debito: '',
    observacao: 'DO QUE SE TRATA?',
    email_cliente: '',
    nota_fiscal_arquivo: null
  })

  const { data: tiposData } = useQuery(
    'tipos-pendencia',
    async () => {
      const response = await api.get('/api/tipos-pendencia')
      return response.data
    }
  )

  const { data: empresasData } = useQuery(
    'empresas',
    async () => {
      const response = await api.get('/api/empresas')
      return response.data
    }
  )

  const criarMutation = useMutation(
    async (data) => {
      const formDataToSend = new FormData()
      Object.keys(data).forEach(key => {
        if (key === 'nota_fiscal_arquivo' && data[key]) {
          formDataToSend.append(key, data[key])
        } else if (data[key] !== null && data[key] !== undefined && data[key] !== '') {
          formDataToSend.append(key, data[key])
        }
      })

      const response = await api.post('/api/pendencia/nova', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
      return response.data
    },
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['dashboard'])
        queryClient.invalidateQueries(['empresas'])
        navigate('/dashboard')
      }
    }
  )

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const handleFileChange = (e) => {
    setFormData(prev => ({ ...prev, nota_fiscal_arquivo: e.target.files[0] }))
  }

  const formatarMoeda = (input) => {
    let valor = input.value.replace(/\D/g, '')
    if (!valor) {
      input.value = 'R$ 0,00'
      return
    }
    let numero = parseInt(valor) / 100
    input.value = numero.toLocaleString('pt-BR', {
      style: 'currency',
      currency: 'BRL',
      minimumFractionDigits: 2
    })
  }

  const handleValorChange = (e) => {
    formatarMoeda(e.target)
    const valor = e.target.value.replace(/[^\d,.-]/g, '').replace(',', '.')
    setFormData(prev => ({ ...prev, valor }))
  }

  const handleSubmit = (e) => {
    e.preventDefault()

    // Validar campos obrigatórios
    const regrasTipo = tiposData?.regras?.[formData.tipo_pendencia] || {}
    const camposObrigatorios = regrasTipo.required || []

    for (const campo of camposObrigatorios) {
      if (!formData[campo] || formData[campo] === '') {
        alert(`O campo ${campo} é obrigatório para este tipo de pendência.`)
        return
      }
    }

    // Converter valor para formato numérico
    const valorNumerico = formData.valor.replace(/[^\d,.-]/g, '').replace(',', '.')

    criarMutation.mutate({
      ...formData,
      valor: valorNumerico
    })
  }

  const regrasTipo = tiposData?.regras?.[formData.tipo_pendencia] || {}
  const camposObrigatorios = regrasTipo.required || []
  const camposProibidos = regrasTipo.forbidden || []
  const labels = regrasTipo.labels || {}
  const observacaoHint = regrasTipo.observacao_hint || ''

  // Determinar quais campos mostrar/ocultar
  const mostrarBanco = !camposProibidos.includes('banco')
  const mostrarData = !camposProibidos.includes('data')
  const mostrarDataCompetencia = camposObrigatorios.includes('data_competencia')
  const mostrarDataBaixa = camposObrigatorios.includes('data_baixa')
  const mostrarFornecedor = !camposProibidos.includes('fornecedor_cliente')
  const mostrarValor = !camposProibidos.includes('valor')
  const mostrarCodigo = camposObrigatorios.includes('codigo_lancamento')
  const mostrarNaturezaSistema = camposObrigatorios.includes('natureza_sistema') || formData.tipo_pendencia === 'Natureza Errada'
  const mostrarTipoCreditoDebito = formData.tipo_pendencia === 'Lançamento Não Encontrado em Sistema' || formData.tipo_pendencia === 'Lançamento Não Encontrado em Extrato'
  const mostrarUpload = formData.tipo_pendencia === 'Documento Não Anexado'

  if (!['adm', 'operador', 'supervisor'].includes(user?.tipo)) {
    return (
      <div className="container">
        <div className="alert alert-danger">
          Você não tem permissão para acessar esta página.
        </div>
      </div>
    )
  }

  return (
    <div className="container">
      <div className="row justify-content-center">
        <div className="col-md-8">
          <div className="card">
            <div className="card-header">
              <h2 className="card-title mb-0">Nova Pendência</h2>
            </div>
            <div className="card-body">
              <form onSubmit={handleSubmit} encType="multipart/form-data">
                <div className="mb-3">
                  <label htmlFor="empresa" className="form-label">Empresa *</label>
                  <select
                    className="form-select"
                    id="empresa"
                    name="empresa"
                    value={formData.empresa}
                    onChange={handleChange}
                    required
                  >
                    <option value="" disabled>Selecione a empresa</option>
                    {empresasData?.empresas?.map(emp => (
                      <option key={emp.nome} value={emp.nome}>{emp.nome}</option>
                    ))}
                  </select>
                </div>

                <div className="mb-3">
                  <label htmlFor="tipo_pendencia" className="form-label">Tipo de Pendência *</label>
                  <select
                    className="form-select"
                    id="tipo_pendencia"
                    name="tipo_pendencia"
                    value={formData.tipo_pendencia}
                    onChange={handleChange}
                    required
                  >
                    <option value="">Selecione...</option>
                    {tiposData?.tipos?.map(tipo => (
                      <option key={tipo} value={tipo}>{tipo}</option>
                    ))}
                  </select>
                </div>

                {/* Banco */}
                {mostrarBanco && (
                  <div className="mb-3">
                    <label htmlFor="banco" className="form-label">
                      Banco {camposObrigatorios.includes('banco') && '*'}
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="banco"
                      name="banco"
                      value={formData.banco}
                      onChange={handleChange}
                      placeholder="Ex: Banco do Brasil, Itaú, Bradesco..."
                      required={camposObrigatorios.includes('banco')}
                    />
                  </div>
                )}

                {/* Data da Pendência */}
                {mostrarData && (
                  <div className="mb-3">
                    <label htmlFor="data" className="form-label">
                      {labels.data || 'Data da Pendência'} {camposObrigatorios.includes('data') && '*'}
                    </label>
                    <input
                      type="date"
                      className="form-control"
                      id="data"
                      name="data"
                      value={formData.data}
                      onChange={handleChange}
                      required={camposObrigatorios.includes('data')}
                    />
                    {formData.tipo_pendencia === 'Documento Não Anexado' && (
                      <div className="form-text">Data do lançamento/extrato. Para "Nota Fiscal Não Identificada", deixe em branco.</div>
                    )}
                  </div>
                )}

                {/* Data Competência */}
                {mostrarDataCompetencia && (
                  <div className="mb-3">
                    <label htmlFor="data_competencia" className="form-label">
                      {labels.data_competencia || 'Data Competência'} *
                    </label>
                    <input
                      type="date"
                      className="form-control"
                      id="data_competencia"
                      name="data_competencia"
                      value={formData.data_competencia}
                      onChange={handleChange}
                      required
                    />
                  </div>
                )}

                {/* Data Baixa */}
                {mostrarDataBaixa && (
                  <div className="mb-3">
                    <label htmlFor="data_baixa" className="form-label">
                      {labels.data_baixa || 'Data da Baixa'} *
                    </label>
                    <input
                      type="date"
                      className="form-control"
                      id="data_baixa"
                      name="data_baixa"
                      value={formData.data_baixa}
                      onChange={handleChange}
                      required
                    />
                  </div>
                )}

                {/* Fornecedor/Cliente */}
                {mostrarFornecedor && (
                  <div className="mb-3">
                    <label htmlFor="fornecedor_cliente" className="form-label">
                      Fornecedor/Cliente {camposObrigatorios.includes('fornecedor_cliente') && '*'}
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="fornecedor_cliente"
                      name="fornecedor_cliente"
                      value={formData.fornecedor_cliente}
                      onChange={handleChange}
                      required={camposObrigatorios.includes('fornecedor_cliente')}
                    />
                  </div>
                )}

                {/* Valor */}
                {mostrarValor && (
                  <div className="mb-3">
                    <label htmlFor="valor" className="form-label">
                      Valor {camposObrigatorios.includes('valor') && '*'}
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="valor"
                      name="valor"
                      value={formData.valor}
                      onChange={handleValorChange}
                      placeholder="R$ 0,00"
                      required={camposObrigatorios.includes('valor')}
                    />
                  </div>
                )}

                {/* Código do Lançamento */}
                {mostrarCodigo && (
                  <div className="mb-3">
                    <label htmlFor="codigo_lancamento" className="form-label">
                      Código do Lançamento {camposObrigatorios.includes('codigo_lancamento') && '*'}
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="codigo_lancamento"
                      name="codigo_lancamento"
                      value={formData.codigo_lancamento}
                      onChange={handleChange}
                      required={camposObrigatorios.includes('codigo_lancamento')}
                    />
                  </div>
                )}

                {/* Natureza do Sistema */}
                {mostrarNaturezaSistema && (
                  <div className="mb-3">
                    <label htmlFor="natureza_sistema" className="form-label">
                      Natureza Atual no Sistema {camposObrigatorios.includes('natureza_sistema') && '*'}
                    </label>
                    <input
                      type="text"
                      className="form-control"
                      id="natureza_sistema"
                      name="natureza_sistema"
                      value={formData.natureza_sistema}
                      onChange={handleChange}
                      placeholder="Ex.: Serviços - 3.01.02"
                      required={camposObrigatorios.includes('natureza_sistema')}
                    />
                    <div className="form-text">Natureza que está atualmente no ERP</div>
                  </div>
                )}

                {/* Tipo Crédito/Débito */}
                {mostrarTipoCreditoDebito && (
                  <div className="mb-3">
                    <label htmlFor="tipo_credito_debito" className="form-label">
                      {labels.tipo_credito_debito || 'Tipo de Lançamento'} *
                    </label>
                    <select
                      className="form-select"
                      id="tipo_credito_debito"
                      name="tipo_credito_debito"
                      value={formData.tipo_credito_debito}
                      onChange={handleChange}
                      required
                    >
                      <option value="">Selecione...</option>
                      <option value="CREDITO">Crédito</option>
                      <option value="DEBITO">Débito</option>
                    </select>
                    <div className="form-text">Indique se o lançamento é uma entrada (crédito) ou saída (débito)</div>
                  </div>
                )}

                {/* Observação */}
                <div className="mb-3">
                  <label htmlFor="observacao" className="form-label">Observação</label>
                  <textarea
                    className="form-control"
                    id="observacao"
                    name="observacao"
                    rows="2"
                    value={formData.observacao}
                    onChange={handleChange}
                    placeholder="DO QUE SE TRATA?"
                  ></textarea>
                  {observacaoHint && (
                    <div className="form-text">{observacaoHint}</div>
                  )}
                </div>

                {/* E-mail do Cliente */}
                <div className="mb-3">
                  <label htmlFor="email_cliente" className="form-label">E-mail do Cliente (opcional)</label>
                  <input
                    type="email"
                    className="form-control"
                    id="email_cliente"
                    name="email_cliente"
                    value={formData.email_cliente}
                    onChange={handleChange}
                  />
                </div>

                {/* Upload de Nota Fiscal */}
                {mostrarUpload && (
                  <div className="mb-3">
                    <label htmlFor="nota_fiscal_arquivo" className="form-label">
                      Anexar Nota Fiscal (PDF, JPG, PNG)
                    </label>
                    <input
                      type="file"
                      className="form-control"
                      id="nota_fiscal_arquivo"
                      name="nota_fiscal_arquivo"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={handleFileChange}
                    />
                  </div>
                )}

                {criarMutation.isError && (
                  <div className="alert alert-danger">
                    {criarMutation.error?.response?.data?.error || 'Erro ao criar pendência'}
                  </div>
                )}

                <div className="d-grid gap-2">
                  <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={criarMutation.isLoading}
                  >
                    {criarMutation.isLoading ? (
                      <>
                        <span className="spinner-border spinner-border-sm me-2"></span>
                        Salvando...
                      </>
                    ) : (
                      <>
                        <i className="bi bi-save me-2"></i>
                        Salvar Pendência
                      </>
                    )}
                  </button>
                  <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => navigate('/dashboard')}
                  >
                    <i className="bi bi-x-circle me-2"></i>
                    Cancelar
                  </button>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default NovaPendencia
