#!/usr/bin/env python3
"""
Script de migração: Consolida tipos "Nota Fiscal Não Anexada" e "Nota Fiscal Não Identificada"
para o novo tipo "Documento Não Anexado".

ATENÇÃO: Este script solicita confirmação antes de executar.
Execute em staging primeiro e verifique os resultados antes de rodar em produção.
"""

from app import app, db, Pendencia
from datetime import datetime
import sys

def migrar_notas_fiscais():
    """Migra tipos antigos de Nota Fiscal para Documento Não Anexado"""
    
    with app.app_context():
        # Tipos antigos a serem migrados
        tipos_antigos = ['Nota Fiscal Não Anexada', 'Nota Fiscal Não Identificada']
        novo_tipo = 'Documento Não Anexado'
        
        # Buscar pendências com tipos antigos
        pendencias = Pendencia.query.filter(
            Pendencia.tipo_pendencia.in_(tipos_antigos)
        ).all()
        
        if not pendencias:
            print("✅ Nenhuma pendência encontrada com os tipos antigos de Nota Fiscal.")
            return
        
        print(f"\n📊 Encontradas {len(pendencias)} pendências para migrar:")
        print("-" * 80)
        
        # Exibir estatísticas
        stats = {}
        for p in pendencias:
            stats[p.tipo_pendencia] = stats.get(p.tipo_pendencia, 0) + 1
        
        for tipo, count in stats.items():
            print(f"  • {tipo}: {count} registro(s)")
        
        print("-" * 80)
        print(f"\nEstas pendências serão migradas para: '{novo_tipo}'")
        print("\n⚠️  ATENÇÃO: Esta operação não pode ser desfeita facilmente!")
        
        # Solicitar confirmação
        resposta = input("\nDeseja continuar com a migração? (sim/não): ").strip().lower()
        
        if resposta not in ['sim', 's', 'yes', 'y']:
            print("❌ Migração cancelada pelo usuário.")
            return
        
        # Executar migração
        print("\n🔄 Iniciando migração...")
        contador = 0
        
        for pendencia in pendencias:
            tipo_anterior = pendencia.tipo_pendencia
            pendencia.tipo_pendencia = novo_tipo
            contador += 1
            
            if contador % 10 == 0:
                print(f"  Processadas {contador}/{len(pendencias)} pendências...")
        
        # Commit das alterações
        try:
            db.session.commit()
            print(f"\n✅ Migração concluída com sucesso!")
            print(f"   Total de registros migrados: {contador}")
            print(f"   Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao salvar migração: {e}")
            sys.exit(1)
        
        # Verificar resultado
        print("\n🔍 Verificando resultado...")
        remanescentes = Pendencia.query.filter(
            Pendencia.tipo_pendencia.in_(tipos_antigos)
        ).count()
        
        if remanescentes > 0:
            print(f"⚠️  AVISO: Ainda existem {remanescentes} pendências com tipos antigos!")
        else:
            print("✅ Verificação OK: Nenhuma pendência remanescente com tipos antigos.")
        
        # Exibir amostra de registros migrados
        print("\n📋 Amostra de registros migrados (primeiros 5):")
        print("-" * 80)
        amostra = Pendencia.query.filter_by(tipo_pendencia=novo_tipo).limit(5).all()
        for p in amostra:
            print(f"  ID: {p.id} | Empresa: {p.empresa} | Valor: R$ {p.valor:,.2f}")
        print("-" * 80)

if __name__ == '__main__':
    print("=" * 80)
    print("SCRIPT DE MIGRAÇÃO: Nota Fiscal → Documento Não Anexado")
    print("=" * 80)
    migrar_notas_fiscais()


