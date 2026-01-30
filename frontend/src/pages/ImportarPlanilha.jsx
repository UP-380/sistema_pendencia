import React, { useState } from 'react'
import { useAuth } from '../contexts/AuthContext'
import api from '../services/api'

function ImportarPlanilha() {
  const { user } = useAuth()
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  const handleFileChange = (e) => {
    setFile(e.target.files[0])
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) {
      setMessage('Por favor, selecione um arquivo')
      return
    }

    setLoading(true)
    setMessage('')

    const formData = new FormData()
    formData.append('arquivo', file)

    try {
      const response = await api.post('/api/importar-planilha', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      if (response.data.success) {
        setMessage('Planilha importada com sucesso!')
        setFile(null)
      } else {
        setMessage(response.data.message || 'Erro ao importar planilha')
        if (response.status === 501) {
          setMessage('Importação via API ainda não está totalmente implementada. Use a interface web em /importar')
        }
      }
    } catch (error) {
      setMessage(error.response?.data?.message || 'Erro ao importar planilha')
    } finally {
      setLoading(false)
    }
  }

  if (!['adm', 'operador'].includes(user?.tipo)) {
    return (
      <div className="alert alert-danger">
        Você não tem permissão para acessar esta página.
      </div>
    )
  }

  return (
    <div className="container">
      <h2 className="mb-4">Importar Planilha</h2>
      
      <div className="card">
        <div className="card-body">
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label htmlFor="arquivo" className="form-label">
                Selecione o arquivo Excel (.xlsx, .xls)
              </label>
              <input
                type="file"
                className="form-control"
                id="arquivo"
                accept=".xlsx,.xls"
                onChange={handleFileChange}
                required
              />
            </div>
            
            {message && (
              <div className={`alert ${message.includes('sucesso') ? 'alert-success' : 'alert-danger'}`}>
                {message}
              </div>
            )}
            
            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading || !file}
            >
              {loading ? (
                <>
                  <span className="spinner-border spinner-border-sm me-2"></span>
                  Importando...
                </>
              ) : (
                <>
                  <i className="bi bi-upload me-2"></i>Importar
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default ImportarPlanilha

