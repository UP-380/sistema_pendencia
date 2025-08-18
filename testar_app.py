#!/usr/bin/env python3
"""
Script para testar se a aplicação está funcionando
"""

import os
import sys
from datetime import datetime

# Adicionar o diretório atual ao path para importar o app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Pendencia, Empresa

def testar_aplicacao():
    """Testa se a aplicação está funcionando"""
    
    with app.app_context():
        try:
            print("🧪 Testando aplicação...")
            
            # 1. Testar conexão com banco
            print("📊 Testando conexão com banco...")
            empresas = Empresa.query.all()
            print(f"✅ {len(empresas)} empresas encontradas")
            
            # 2. Testar tabela pendencia
            print("📋 Testando tabela pendencia...")
            pendencias = Pendencia.query.all()
            print(f"✅ {len(pendencias)} pendências encontradas")
            
            # 3. Testar criação de pendência
            print("➕ Testando criação de pendência...")
            nova_pendencia = Pendencia(
                empresa="TESTE",
                tipo_pendencia="Pagamento Não Identificado",
                banco="Banco Teste",
                data=datetime.now().date(),
                data_abertura=datetime.now(),
                fornecedor_cliente="Fornecedor Teste",
                valor=100.0,
                observacao="Teste de criação",
                status="PENDENTE CLIENTE"
            )
            
            db.session.add(nova_pendencia)
            db.session.commit()
            print("✅ Pendência criada com sucesso!")
            
            # 4. Remover pendência de teste
            db.session.delete(nova_pendencia)
            db.session.commit()
            print("✅ Pendência de teste removida!")
            
            print("🎉 Aplicação funcionando corretamente!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            raise
        finally:
            db.session.close()

if __name__ == "__main__":
    testar_aplicacao()
