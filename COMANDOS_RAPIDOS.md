# ⚡ Comandos Rápidos - Sistema UP380

Referência rápida dos comandos mais utilizados para manutenção e administração do sistema.

---

## 📦 Instalação e Setup

```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar banco de dados (sistema novo)
python init_db.py

# Executar aplicação
python app.py
```

---

## 🗄️ Migrações de Banco de Dados

```bash
# Adicionar estrutura de segmentos
python migrate_adicionar_segmentos.py

# Migrar tipos de pendência (com confirmação)
python migrate_nota_fiscal_para_documento.py

# Migrar tipos automaticamente (sem confirmação)
python migrar_nota_fiscal_automatico.py

# Configurar permissões cliente_supervisor
python migrate_cliente_supervisor.py

# Backup do banco
python backup_database.py
```

---

## 🔍 Verificações Rápidas

### Verificar Dependências

```bash
# Windows
python -m pip list | findstr Flask

# Linux/Mac
python -m pip list | grep Flask
```

### Verificar Estrutura do Banco

```python
from app import app, db, Segmento, Empresa, Pendencia
from sqlalchemy import inspect

with app.app_context():
    inspector = inspect(db.engine)
    
    # Listar tabelas
    print("Tabelas:", inspector.get_table_names())
    
    # Listar colunas de empresa
    print("\nColunas da tabela empresa:")
    for col in inspector.get_columns('empresa'):
        print(f"  - {col['name']}: {col['type']}")
```

### Verificar Migração de Tipos

```python
from app import app, db, Pendencia

with app.app_context():
    # Tipos antigos (deve ser 0)
    antigos = Pendencia.query.filter(
        Pendencia.tipo_pendencia.in_([
            'Nota Fiscal Não Anexada',
            'Nota Fiscal Não Identificada'
        ])
    ).count()
    print(f"Tipos antigos: {antigos}")
    
    # Novos tipos
    documento = Pendencia.query.filter_by(
        tipo_pendencia='Documento Não Anexado'
    ).count()
    print(f"Documento Não Anexado: {documento}")
    
    extrato = Pendencia.query.filter_by(
        tipo_pendencia='Lançamento Não Encontrado em Extrato'
    ).count()
    print(f"Lançamento Não Encontrado em Extrato: {extrato}")
```

---

## 👥 Gerenciamento de Usuários

### Criar Usuário via Python

```python
from app import app, db, Usuario, Empresa
from werkzeug.security import generate_password_hash

with app.app_context():
    # Criar usuário cliente_supervisor
    usuario = Usuario(
        email='supervisor@empresa.com',
        senha_hash=generate_password_hash('SenhaSegura123!'),
        tipo='cliente_supervisor'
    )
    
    # Associar empresas
    empresas = Empresa.query.filter(
        Empresa.nome.in_(['EMPRESA1', 'EMPRESA2'])
    ).all()
    usuario.empresas = empresas
    
    db.session.add(usuario)
    db.session.commit()
    print(f"Usuário criado: {usuario.email}")
```

### Alterar Senha de Usuário

```python
from app import app, db, Usuario
from werkzeug.security import generate_password_hash

with app.app_context():
    usuario = Usuario.query.filter_by(
        email='usuario@exemplo.com'
    ).first()
    
    if usuario:
        usuario.senha_hash = generate_password_hash('NovaSenha123!')
        db.session.commit()
        print("Senha alterada com sucesso!")
```

### Listar Todos os Usuários

```python
from app import app, db, Usuario

with app.app_context():
    usuarios = Usuario.query.all()
    for u in usuarios:
        empresas = [e.nome for e in u.empresas]
        print(f"{u.email} ({u.tipo}) - Empresas: {', '.join(empresas)}")
```

---

## 🏢 Gerenciamento de Segmentos e Empresas

### Criar Segmento

```python
from app import app, db, Segmento

with app.app_context():
    segmento = Segmento(nome='Novo Segmento')
    db.session.add(segmento)
    db.session.commit()
    print(f"Segmento criado: ID {segmento.id}")
```

### Associar Empresa a Segmento

```python
from app import app, db, Empresa, Segmento

with app.app_context():
    empresa = Empresa.query.filter_by(nome='ALIANZE').first()
    segmento = Segmento.query.filter_by(nome='Financeiro').first()
    
    if empresa and segmento:
        empresa.segmento_id = segmento.id
        db.session.commit()
        print(f"{empresa.nome} → {segmento.nome}")
```

### Listar Segmentos com Empresas

```python
from app import app, db, Segmento

with app.app_context():
    segmentos = Segmento.query.all()
    for seg in segmentos:
        print(f"\n{seg.nome}:")
        for emp in seg.empresas:
            print(f"  - {emp.nome}")
```

---

## 📊 Consultas e Relatórios

### Contar Pendências por Tipo

```python
from app import app, db, Pendencia
from sqlalchemy import func

with app.app_context():
    resultado = db.session.query(
        Pendencia.tipo_pendencia,
        func.count(Pendencia.id).label('total')
    ).group_by(Pendencia.tipo_pendencia).all()
    
    for tipo, total in resultado:
        print(f"{tipo}: {total}")
```

### Pendências por Status

```python
from app import app, db, Pendencia
from sqlalchemy import func

with app.app_context():
    resultado = db.session.query(
        Pendencia.status,
        func.count(Pendencia.id).label('total')
    ).group_by(Pendencia.status).all()
    
    for status, total in resultado:
        print(f"{status}: {total}")
```

### Pendências por Empresa

```python
from app import app, db, Pendencia
from sqlalchemy import func

with app.app_context():
    resultado = db.session.query(
        Pendencia.empresa,
        func.count(Pendencia.id).label('total')
    ).group_by(Pendencia.empresa).order_by(
        func.count(Pendencia.id).desc()
    ).all()
    
    for empresa, total in resultado:
        print(f"{empresa}: {total}")
```

---

## 🔧 Manutenção

### Limpar Sessões Antigas (não aplicável para SQLite)

```python
# Para produção com Redis/PostgreSQL
# Limpar sessões com mais de 24h
```

### Verificar Integridade do Banco

```bash
# SQLite
sqlite3 pendencias.db "PRAGMA integrity_check;"

# Deve retornar: ok
```

### Compactar Banco SQLite

```bash
sqlite3 pendencias.db "VACUUM;"
```

### Exportar Banco para SQL

```bash
sqlite3 pendencias.db .dump > backup_$(date +%Y%m%d).sql
```

---

## 🐛 Debug e Troubleshooting

### Modo Debug Flask

```bash
# app.py - adicionar antes de app.run()
app.config['DEBUG'] = True
app.run(debug=True)
```

### Ver Queries SQL

```python
from app import app, db

# Ativar echo
app.config['SQLALCHEMY_ECHO'] = True

# Ou durante runtime
with app.app_context():
    # Suas queries aqui
    pass
```

### Verificar Logs Recentes

```python
from app import app, db, LogAlteracao
from datetime import datetime, timedelta

with app.app_context():
    uma_hora_atras = datetime.now() - timedelta(hours=1)
    logs = LogAlteracao.query.filter(
        LogAlteracao.data_hora >= uma_hora_atras
    ).order_by(LogAlteracao.data_hora.desc()).all()
    
    for log in logs:
        print(f"{log.data_hora} - {log.usuario}: {log.acao}")
```

---

## 🧪 Testes

### Testar CSRF

```bash
# Deve retornar 400 (CSRF token missing)
curl -X POST http://localhost:5000/nova -d "empresa=TESTE"
```

### Testar Rate Limiting

```bash
# Fazer 60 requisições
for i in {1..60}; do 
    curl -s http://localhost:5000/ > /dev/null
    echo "Requisição $i"
done
```

### Testar Formatação de Moeda

```python
from app import parse_currency_to_float

# Testes
print(parse_currency_to_float("R$ 1.234,56"))    # 1234.56
print(parse_currency_to_float("R$1234,56"))      # 1234.56
print(parse_currency_to_float("1.234,56"))       # 1234.56
print(parse_currency_to_float("1234.56"))        # 1234.56
```

---

## 🚀 Deploy

### Deploy Local/Desenvolvimento

```bash
python app.py
```

### Deploy Produção (Gunicorn)

```bash
# Instalar gunicorn
pip install gunicorn

# Executar
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Deploy com Docker

```bash
# Build
docker build -t up380-pendencias .

# Run
docker run -d -p 5000:5000 --name up380 up380-pendencias
```

---

## 📝 Backup e Restore

### Backup Manual

```bash
# Copiar banco
cp pendencias.db pendencias_backup_$(date +%Y%m%d_%H%M%S).db

# Ou usar script
python backup_database.py
```

### Restore

```bash
# Restaurar backup
cp pendencias_backup_20250101_120000.db pendencias.db
```

### Backup Automático (Cron)

```bash
# Adicionar ao crontab (executar diariamente às 2h)
0 2 * * * cd /caminho/para/app && python backup_database.py
```

---

## 🔐 Segurança

### Gerar Nova SECRET_KEY

```python
import secrets
print(secrets.token_hex(32))
```

### Verificar Headers de Segurança

```bash
curl -I http://localhost:5000/ | grep -E "Security|Policy|Transport"
```

### Ativar HTTPS (Produção)

```python
# app.py
talisman = Talisman(
    app,
    force_https=True,  # ← Mudar para True
    ...
)
```

---

## 📞 Informações Úteis

### Usuários Padrão

- **Admin**: adm.pendencia@up380.com.br / Finance.@2
- **Cliente**: usuario.pendencia@up380.com.br / Finance.@2

### Portas Padrão

- **Flask Development**: 5000
- **Gunicorn (sugerido)**: 8000
- **Nginx (proxy)**: 80/443

### Arquivos Importantes

- `pendencias.db` - Banco de dados SQLite
- `app.py` - Aplicação principal
- `requirements.txt` - Dependências
- `.env` - Configurações (NÃO versionar!)

---

**Última Atualização**: Outubro 2025  
**Versão**: 3.0


