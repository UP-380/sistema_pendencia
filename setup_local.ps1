# ========================================
# SCRIPT DE SETUP LOCAL - Windows
# ========================================

Write-Host "🚀 Configurando ambiente de desenvolvimento local..." -ForegroundColor Green

# 1. Instalar dependências
Write-Host "`n📦 Instalando dependências..." -ForegroundColor Cyan
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Erro ao instalar dependências!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Dependências instaladas!" -ForegroundColor Green

# 2. Criar arquivo .env se não existir
if (-not (Test-Path ".env")) {
    Write-Host "`n📝 Criando arquivo .env..." -ForegroundColor Cyan
    
    @"
SECRET_KEY=desenvolvimento-local-key-123456789
FLASK_ENV=development
FLASK_APP=app.py
SESSION_COOKIE_SECURE=False
"@ | Out-File -FilePath ".env" -Encoding UTF8
    
    Write-Host "✅ Arquivo .env criado!" -ForegroundColor Green
} else {
    Write-Host "`n✅ Arquivo .env já existe!" -ForegroundColor Green
}

# 3. Criar diretório instance
if (-not (Test-Path "instance")) {
    Write-Host "`n📂 Criando diretório instance..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path "instance" | Out-Null
    Write-Host "✅ Diretório instance criado!" -ForegroundColor Green
}

# 4. Criar banco de dados (se não existir)
if (-not (Test-Path "instance\pendencias.db")) {
    Write-Host "`n🗄️ Criando banco de dados local..." -ForegroundColor Cyan
    
    python -c @"
from app import db, app
with app.app_context():
    db.create_all()
    print('✅ Banco de dados criado!')
"@
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✅ Banco de dados criado em: instance\pendencias.db" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Erro ao criar banco. Execute manualmente:" -ForegroundColor Yellow
        Write-Host "python -c `"from app import db, app; app.app_context().push(); db.create_all()`"" -ForegroundColor Yellow
    }
} else {
    Write-Host "`n✅ Banco de dados já existe!" -ForegroundColor Green
}

Write-Host "`n" -NoNewline
Write-Host "═══════════════════════════════════════" -ForegroundColor Green
Write-Host "✅ SETUP CONCLUÍDO!" -ForegroundColor Green
Write-Host "═══════════════════════════════════════" -ForegroundColor Green

Write-Host "`n📋 Próximos passos:" -ForegroundColor Cyan
Write-Host "1. Execute: python app.py" -ForegroundColor White
Write-Host "2. Acesse: http://localhost:5000" -ForegroundColor White
Write-Host "3. Login padrão (será criado no primeiro acesso)" -ForegroundColor White
Write-Host ""
Write-Host "💡 Para parar o servidor: Ctrl+C" -ForegroundColor Yellow
Write-Host ""

