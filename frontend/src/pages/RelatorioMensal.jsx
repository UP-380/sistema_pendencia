import React from 'react'
import { useAuth } from '../contexts/AuthContext'

function RelatorioMensal() {
  const { user } = useAuth()

  if (!['adm', 'supervisor', 'operador', 'cliente_supervisor'].includes(user?.tipo)) {
    return (
      <div className="alert alert-danger">
        Você não tem permissão para acessar esta página.
      </div>
    )
  }

  return (
    <div className="container">
      <h2 className="mb-4">Relatório Mensal</h2>
      <div className="alert alert-info">
        Esta funcionalidade será implementada em breve.
      </div>
    </div>
  )
}

export default RelatorioMensal

