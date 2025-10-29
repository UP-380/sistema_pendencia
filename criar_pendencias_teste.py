#!/usr/bin/env python3
"""
Script para criar pendências de teste no banco de dados.
Útil para testar os dashboards e gráficos.

Uso:
    python criar_pendencias_teste.py
"""

from app import app, db, Pendencia, Empresa
from datetime import datetime, timedelta
import random

def criar_pendencias_teste():
    with app.app_context():
        print("=" * 80)
        print("🚀 CRIANDO PENDÊNCIAS DE TESTE")
        print("=" * 80)
        
        # Buscar empresas existentes
        empresas = Empresa.query.limit(10).all()
        
        if not empresas:
            print("❌ Nenhuma empresa encontrada no banco!")
            print("   Execute primeiro: python migrate_add_segmento.py")
            return
        
        print(f"\n✅ Encontradas {len(empresas)} empresas")
        
        # Tipos de pendência disponíveis
        tipos = [
            'CARTAO_NAO_IDENTIFICADO',
            'PAGAMENTO_NAO_IDENTIFICADO',
            'RECEBIMENTO_NAO_IDENTIFICADO',
            'DOCUMENTO_NAO_ANEXADO',
            'LANCAMENTO_NAO_ENCONTRADO_EXTRATO',
            'LANCAMENTO_NAO_ENCONTRADO_SISTEMA',
            'NATUREZA_ERRADA',
            'COMPETENCIA_ERRADA',
            'DATA_BAIXA_ERRADA'
        ]
        
        # Status disponíveis
        status_list = [
            'PENDENTE CLIENTE',
            'PENDENTE OPERADOR UP',
            'PENDENTE SUPERVISOR UP',
            'PENDENTE COMPLEMENTO CLIENTE',
            'RESOLVIDA'
        ]
        
        # Bancos de exemplo
        bancos = ['Banco do Brasil', 'Itaú', 'Bradesco', 'Santander', 'Caixa']
        
        # Fornecedores/Clientes de exemplo
        fornecedores = [
            'Fornecedor XYZ Ltda',
            'Cliente ABC S/A',
            'Empresa DEF',
            'Prestador GHI',
            'Cliente JKL'
        ]
        
        print("\n📊 Criando 30 pendências de teste...")
        
        total_criadas = 0
        
        for i in range(30):
            empresa = random.choice(empresas)
            tipo = random.choice(tipos)
            status = random.choice(status_list)
            banco = random.choice(bancos)
            fornecedor = random.choice(fornecedores)
            
            # Data aleatória nos últimos 60 dias
            dias_atras = random.randint(0, 60)
            data = (datetime.now() - timedelta(days=dias_atras)).date()
            
            # Valor aleatório entre 100 e 10000
            valor = round(random.uniform(100, 10000), 2)
            
            # Criar pendência
            pendencia = Pendencia(
                empresa=empresa.nome,
                tipo_pendencia=tipo,
                banco=banco,
                data=data,
                fornecedor_cliente=fornecedor,
                valor=valor,
                observacao=f'Pendência de teste número {i+1}. Criada automaticamente para testes.',
                status=status,
                email_cliente=f'teste{i+1}@exemplo.com.br'
            )
            
            # Se for resolvida, adicionar resposta
            if status == 'RESOLVIDA':
                pendencia.resposta_cliente = f'Resolvida em teste - Pendência {i+1}'
                pendencia.data_resposta = datetime.now()
            
            db.session.add(pendencia)
            total_criadas += 1
            
            if (i + 1) % 10 == 0:
                print(f"   ✅ {i + 1} pendências criadas...")
        
        # Commit final
        db.session.commit()
        
        print(f"\n✅ Total de pendências criadas: {total_criadas}")
        
        # Resumo por tipo
        print("\n📊 Resumo por Tipo de Pendência:")
        for tipo in tipos:
            count = Pendencia.query.filter_by(tipo_pendencia=tipo).count()
            if count > 0:
                print(f"   • {tipo}: {count}")
        
        # Resumo por status
        print("\n📊 Resumo por Status:")
        for status in status_list:
            count = Pendencia.query.filter_by(status=status).count()
            if count > 0:
                print(f"   • {status}: {count}")
        
        # Resumo por empresa
        print("\n📊 Resumo por Empresa (Top 5):")
        for empresa in empresas[:5]:
            count = Pendencia.query.filter_by(empresa=empresa.nome).count()
            print(f"   • {empresa.nome}: {count} pendências")
        
        print("\n" + "=" * 80)
        print("🎉 PENDÊNCIAS DE TESTE CRIADAS COM SUCESSO!")
        print("=" * 80)
        
        print("\n📋 Próximos passos:")
        print("   1. Acesse: http://localhost:5000/empresas")
        print("   2. Veja os gráficos com dados")
        print("   3. Navegue pelas empresas e pendências")
        
        print("\n💡 Dica:")
        print("   Para limpar as pendências de teste, use:")
        print("   DELETE FROM pendencia WHERE observacao LIKE '%teste%';")

if __name__ == '__main__':
    print("\n⚠️  Este script irá criar 30 pendências de teste no banco de dados.")
    resposta = input("\nDeseja continuar? (sim/não): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        criar_pendencias_teste()
    else:
        print("\n❌ Operação cancelada.")


