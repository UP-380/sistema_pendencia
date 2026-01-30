import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:5000/api', // DEV URL
  withCredentials: true, // Importante para manter sessão/cookies
  headers: {
    'Content-Type': 'application/json',
  },
})

// Interceptor para adicionar tratamento de erros
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Não redirecionar automaticamente, deixar o componente tratar
      console.log('Não autenticado')
    }
    return Promise.reject(error)
  }
)

export default api

