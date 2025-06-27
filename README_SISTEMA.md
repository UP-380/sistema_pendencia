# Sistema de Gestão de Pendências UP380

## Visão Geral

Este sistema é uma aplicação web desenvolvida em Flask para gerenciar pendências financeiras de empresas. Ele permite o registro, acompanhamento, resposta e resolução de pendências, com funcionalidades de importação de planilhas, envio de e-mails, logs de auditoria e integração com Microsoft Teams.

---

## Funcionalidades Principais

- **Login e autenticação** com dois tipos de usuário: admin e cliente.
- **Dashboard** com filtros por empresa e tipo de pendência.
- **Cadastro, edição e resolução de pendências**.
- **Importação de pendências via planilha Excel**.
- **Envio automático de e-mails para clientes**.
- **Notificações via Microsoft Teams**.
- **Logs de alterações e exportação de logs em CSV**.
- **Interface responsiva com Bootstrap**.

---

## Estrutura do Projeto

```
PLANILHA DE PENDENCIAS/
├── app.py                # Código principal Flask
├── requirements.txt      # Dependências do projeto
├── README.md             # Instruções de uso
├── modelo_importacao_up380.xlsx # Modelo de planilha para importação
├── Procfile              # Para deploy (ex: Heroku)
├── instance/
│   └── pendencias.db     # Banco de dados SQLite
├── static/
│   ├── up380.css         # Estilos customizados
│   └── logoUP.png        # Logo do sistema
├── templates/
│   ├── base.html         # Template base
│   ├── dashboard.html    # Painel principal
│   ├── pre_dashboard.html# Painel de empresas
│   ├── importar_planilha.html
│   ├── logs_recentes.html
│   ├── logs_pendencia.html
│   ├── historico_importacoes.html
│   ├── resolvidas.html
│   ├── editar_pendencia.html
│   ├── nova_pendencia.html
│   ├── login.html
│   ├── editar_observacao.html
│   └── ver_pendencia.html
```

---

## Modelos de Dados (SQLAlchemy)

### Pendencia
- id, empresa, tipo_pendencia, banco, data, fornecedor_cliente, valor, observacao, resposta_cliente, email_cliente, status, token_acesso, data_resposta, modificado_por

### Usuario
- id, email, senha_hash, tipo (admin/cliente)

### LogAlteracao
- id, pendencia_id, usuario, tipo_usuario, data_hora, acao, campo_alterado, valor_anterior, valor_novo

### Importacao
- id, nome_arquivo, usuario, data_hora, status, mensagem_erro

---

## Fluxo de Uso

1. **Login:**
   - Usuário acessa `/login` e entra como admin ou cliente.
2. **Dashboard:**
   - Visualiza pendências filtrando por empresa/tipo.
3. **Nova Pendência:**
   - Admin pode cadastrar nova pendência e enviar e-mail ao cliente.
4. **Importação:**
   - Admin pode importar várias pendências via planilha Excel.
5. **Resposta do Cliente:**
   - Cliente recebe e-mail com link único, responde a pendência.
6. **Resolução:**
   - Admin pode marcar pendência como resolvida.
7. **Logs:**
   - Todas as alterações são registradas e podem ser exportadas em CSV.
8. **Notificações Teams:**
   - Alterações relevantes notificam canal Teams via webhook.

---

## Rotas Principais

- `/login`, `/logout` — Autenticação
- `/dashboard` — Painel principal
- `/nova` — Nova pendência (admin)
- `/pendencia/<token>` — Visualização e resposta de pendência
- `/resolver/<id>` — Marcar como resolvida (admin)
- `/baixar_modelo` — Download do modelo Excel
- `/importar` — Importação de planilha
- `/historico_importacoes` — Histórico de importações
- `/editar/<id>` — Editar pendência (admin)
- `/editar_observacao/<id>` — Editar observação (cliente)
- `/empresas` — Painel de empresas
- `/resolvidas` — Pendências resolvidas
- `/logs/<pendencia_id>` — Logs de uma pendência
- `/exportar_logs/<pendencia_id>` — Exportar logs de uma pendência
- `/logs_recentes` — Logs recentes
- `/exportar_logs_csv` — Exportar logs recentes
- `/` — Redireciona para dashboard

---

## Templates

- **base.html:** Estrutura base, navbar, mensagens flash, responsividade.
- **dashboard.html:** Listagem e filtros de pendências.
- **pre_dashboard.html:** Resumo por empresa.
- **importar_planilha.html:** Upload e preview de planilha.
- **logs_recentes.html, logs_pendencia.html:** Visualização de logs.
- **historico_importacoes.html:** Histórico de uploads.
- **resolvidas.html:** Pendências resolvidas e seus logs.
- **editar_pendencia.html, nova_pendencia.html:** Formulários de edição/criação.
- **login.html:** Tela de login.
- **editar_observacao.html:** Edição de observação pelo cliente.
- **ver_pendencia.html:** Visualização e resposta de pendência via token.

---

## Integrações

- **E-mail:** Flask-Mail, SMTP configurável via `.env`.
- **Teams:** Webhook para canal Microsoft Teams.
- **Importação Excel:** pandas + openpyxl.
- **Exportação CSV:** csv + streaming.

---

## Segurança

- Sessão protegida por `SECRET_KEY`.
- Login obrigatório para todas as rotas (exceto resposta via token).
- Tokens de acesso únicos para cada pendência.
- Senhas armazenadas com hash seguro.

---

## Como Executar

1. Instale dependências: `pip install -r requirements.txt`
2. Configure `.env` com variáveis de e-mail e chave secreta.
3. Rode: `python app.py`
4. Acesse: `http://localhost:8000`

---

## Observações

- O sistema é facilmente adaptável para outros bancos de dados.
- Pode ser hospedado em qualquer serviço que rode Python (Heroku, VPS, etc).
- O código é modular e pronto para expansão.

---

**Desenvolvido por UP380.** 