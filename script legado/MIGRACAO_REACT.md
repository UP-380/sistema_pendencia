# Guia de Migração para React - Sistema UP380

## 📋 Visão Geral

Este documento descreve a migração do frontend do sistema UP380 de templates Flask/Jinja2 para React, mantendo o backend Flask intacto.

## 🏗️ Estrutura Criada

### Frontend React
```
frontend/
├── package.json          # Dependências do React
├── vite.config.js        # Configuração do Vite
├── index.html           # HTML base
└── src/
    ├── main.jsx         # Entry point
    ├── App.jsx          # Rotas principais
    ├── index.css        # Estilos globais
    ├── contexts/
    │   └── AuthContext.jsx    # Contexto de autenticação
    ├── services/
    │   └── api.js       # Cliente Axios configurado
    ├── components/
    │   └── Layout/
    │       ├── Layout.jsx
    │       ├── Layout.css
    │       ├── Sidebar.jsx
    │       └── Sidebar.css
    └── pages/
        ├── Login.jsx
        └── Login.css
```

### Backend API
```
api_routes.py            # Rotas de API REST (/api/*)
```

## 🚀 Como Usar

### 1. Instalar Dependências do Frontend

```bash
cd frontend
npm install
```

### 2. Desenvolvimento

**Terminal 1 - Flask Backend:**
```bash
python app.py
# ou
flask run
```

**Terminal 2 - React Frontend:**
```bash
cd frontend
npm run dev
```

O React estará rodando em `http://localhost:3000` e fazendo proxy para o Flask em `http://localhost:5000`

### 3. Produção

**Build do React:**
```bash
cd frontend
npm run build
```

Isso gerará os arquivos estáticos em `static/react-build/`

**Configurar Flask para servir React:**

Adicionar ao `app.py`:
```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if path != "" and os.path.exists(os.path.join(app.static_folder, 'react-build', path)):
        return send_from_directory(os.path.join(app.static_folder, 'react-build'), path)
    else:
        return send_from_directory(os.path.join(app.static_folder, 'react-build'), 'index.html')
```

## 📝 Próximos Passos

### Fase 1: API REST (Em Progresso)
- [x] Criar estrutura base do React
- [x] Criar rotas de autenticação (/api/auth/*)
- [ ] Criar rotas de empresas (/api/empresas)
- [ ] Criar rotas de pendências (/api/pendencias)
- [ ] Criar rotas de segmentos (/api/segmentos)
- [ ] Criar rotas administrativas (/api/admin/*)

### Fase 2: Componentes React
- [x] Layout e Sidebar
- [x] Login
- [ ] Página de Empresas
- [ ] Página de Dashboard
- [ ] Página de Segmentos
- [ ] Páginas Administrativas

### Fase 3: Funcionalidades
- [ ] Importar Planilha
- [ ] Relatórios
- [ ] Operador/Supervisor
- [ ] Modais e Formulários

### Fase 4: Integração e Testes
- [ ] Testar todas as rotas
- [ ] Ajustar CORS se necessário
- [ ] Configurar build de produção
- [ ] Deploy

## 🔧 Configurações Importantes

### CORS (se necessário)
Se o React estiver em domínio diferente, adicionar ao Flask:
```python
from flask_cors import CORS
CORS(app, supports_credentials=True)
```

### Sessões
O sistema usa sessões do Flask. O Axios está configurado com `withCredentials: true` para manter cookies.

### Autenticação
- Login: `POST /api/auth/login`
- Logout: `POST /api/auth/logout`
- Verificar: `GET /api/auth/check`

## 📚 Recursos

- React Router: Navegação
- React Query: Gerenciamento de estado e cache
- Axios: Requisições HTTP
- Bootstrap 5: UI Framework
- Chart.js: Gráficos

## ⚠️ Notas Importantes

1. **Backend não alterado**: Todas as rotas Flask existentes continuam funcionando
2. **Compatibilidade**: O sistema pode rodar com templates antigos e React simultaneamente durante a migração
3. **Sessões**: As sessões Flask são mantidas através de cookies
4. **Build**: O build do React gera arquivos estáticos que o Flask serve

## 🐛 Troubleshooting

### Erro de CORS
Adicionar `flask-cors` e configurar no `app.py`

### Sessão não persiste
Verificar se `withCredentials: true` está no Axios

### Rotas não funcionam
Verificar se o proxy do Vite está configurado corretamente

