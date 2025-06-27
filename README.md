# Sistema de Gestão de Pendências

Um sistema web simples para gerenciar pendências financeiras, permitindo que operadores registrem pendências e clientes respondam através de links seguros enviados por e-mail.

## Funcionalidades

- Painel principal para visualização de todas as pendências
- Formulário para registro de novas pendências
- Envio automático de e-mails para clientes
- Página segura para clientes responderem pendências
- Sistema de status para acompanhamento (Pendente, Respondida, Resolvida)

## Requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

## Instalação

1. Clone este repositório ou baixe os arquivos

2. Crie um ambiente virtual (recomendado):
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:
```
SECRET_KEY=sua_chave_secreta_aqui
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_de_app
MAIL_DEFAULT_SENDER=seu_email@gmail.com
```

Para usar o Gmail como servidor de e-mail, você precisará:
1. Ativar a verificação em duas etapas na sua conta Google
2. Gerar uma "Senha de App" específica para este aplicativo
3. Usar essa senha no MAIL_PASSWORD

## Executando o Sistema

1. Inicie o servidor:
```bash
python app.py
```

2. Acesse o sistema no navegador:
```
http://localhost:5000
```

## Uso

1. **Registrando uma Pendência**:
   - Acesse o painel principal
   - Clique em "Nova Pendência"
   - Preencha o formulário com os dados da pendência
   - O sistema enviará automaticamente um e-mail para o cliente

2. **Respondendo uma Pendência**:
   - O cliente recebe um e-mail com um link único
   - Ao clicar no link, ele acessa a página da pendência
   - Pode responder diretamente pelo formulário
   - O operador será notificado da resposta

3. **Gerenciando Pendências**:
   - No painel principal, visualize todas as pendências
   - Marque pendências como resolvidas quando necessário
   - Acompanhe o status de cada pendência

## Segurança

- Links únicos e seguros para cada pendência
- Sem necessidade de login para clientes
- Proteção contra acesso não autorizado
- Dados armazenados em banco SQLite local

## Suporte

Para suporte ou dúvidas, entre em contato com a equipe de desenvolvimento.

## Deploy no EasyPanel (VPS)

### 1. Requisitos
- Python 3.9+
- Banco de dados SQLite (ou PostgreSQL/MySQL se desejar)
- EasyPanel configurado

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente
Crie um arquivo `.env` na raiz do projeto com:
```
SECRET_KEY=sua_chave_secreta
MAIL_SERVER=smtp.seuservidor.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu@email.com
MAIL_PASSWORD=sua_senha
MAIL_DEFAULT_SENDER=seu@email.com
```

### 4. Inicialize o banco de dados (primeira vez)
```bash
python
>>> from app import db; db.create_all()
```

### 5. Execute com Gunicorn (produção)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
No EasyPanel, configure o comando acima como start do app.

### 6. Segurança
- Certifique-se de rodar atrás de HTTPS (Nginx/Proxy do EasyPanel)
- Nunca exponha o .env
- Desative debug no Flask

### 7. Acesso
Acesse pelo domínio configurado no EasyPanel.

---

## Suporte
Dúvidas? Fale com o desenvolvedor UP380. 