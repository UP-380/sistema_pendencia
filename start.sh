#!/bin/bash

# Script de inicialização com migrações automáticas
echo "🚀 Iniciando sistema de pendências..."

# Executar migrações se os scripts existirem
if [ -f "migrate_natureza_operacao.py" ]; then
    echo "📊 Executando migração: natureza_operacao"
    python3 migrate_natureza_operacao.py
fi

if [ -f "migrate_motivo_recusa_supervisor.py" ]; then
    echo "📊 Executando migração: motivo_recusa_supervisor"
    python3 migrate_motivo_recusa_supervisor.py
fi

if [ -f "migrate_data_abertura.py" ]; then
    echo "📊 Executando migração: data_abertura"
    python3 migrate_data_abertura.py
fi

echo "✅ Migrações concluídas!"
echo "🌐 Iniciando Gunicorn com 1 worker + sticky sessions..."

# Iniciar com 1 worker e múltiplas threads (sessão funcionará)
exec gunicorn --bind 0.0.0.0:5000 \
              --workers 1 \
              --threads 8 \
              --timeout 120 \
              --access-logfile - \
              --error-logfile - \
              --log-level info \
              app:app
