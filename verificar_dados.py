#!/usr/bin/env python3
"""
Script para verificar os dados de pendências no banco.
"""

from app import app, db, Pendencia
from collections import Counter

with app.app_context():
    print("=" * 80)
    print("📊 VERIFICAÇÃO DE DADOS DE PENDÊNCIAS")
    print("=" * 80)
    
    # Total de pendências
    total = Pendencia.query.count()
    print(f"\n✅ Total de pendências no banco: {total}")
    
    if total == 0:
        print("\n⚠️  ATENÇÃO: Não há pendências cadastradas!")
        print("   Execute: python criar_pendencias_teste.py")
        exit()
    
    # Buscar todas as pendências
    pendencias = Pendencia.query.all()
    
    # Contar por tipo
    print("\n📊 Pendências por Tipo:")
    tipos = Counter([p.tipo_pendencia for p in pendencias])
    for tipo, count in tipos.most_common():
        print(f"   • {tipo}: {count}")
    
    # Contar por status
    print("\n📊 Pendências por Status:")
    status = Counter([p.status for p in pendencias])
    for st, count in status.most_common():
        print(f"   • {st}: {count}")
    
    # Contar por empresa
    print("\n📊 Pendências por Empresa (Top 10):")
    empresas = Counter([p.empresa for p in pendencias])
    for empresa, count in empresas.most_common(10):
        print(f"   • {empresa}: {count}")
    
    # Verificar pendências abertas vs resolvidas
    abertas = [p for p in pendencias if p.status != 'RESOLVIDA']
    resolvidas = [p for p in pendencias if p.status == 'RESOLVIDA']
    
    print(f"\n📈 Resumo Geral:")
    print(f"   • Total: {total}")
    print(f"   • Abertas: {len(abertas)}")
    print(f"   • Resolvidas: {len(resolvidas)}")
    
    print("\n" + "=" * 80)
    print("✅ Verificação concluída!")
    print("=" * 80)
    
    if len(abertas) > 0:
        print(f"\n🎯 Os gráficos devem mostrar {len(abertas)} pendências abertas.")
    else:
        print("\n⚠️  Todas as pendências estão resolvidas. Os gráficos mostrarão apenas resolvidas.")


