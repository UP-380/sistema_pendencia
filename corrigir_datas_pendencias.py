#!/usr/bin/env python3
"""
Script para corrigir pendências sem data.
Preenche o campo 'data' com a 'data_abertura' quando estiver vazio.
"""

from app import app, db, Pendencia
from datetime import datetime

with app.app_context():
    print("=" * 80)
    print("CORRIGINDO DATAS DAS PENDENCIAS")
    print("=" * 80)
    
    # Buscar pendências sem data
    pendencias_sem_data = Pendencia.query.filter(Pendencia.data == None).all()
    
    total_sem_data = len(pendencias_sem_data)
    
    if total_sem_data == 0:
        print("\nTodas as pendencias ja tem data!")
        print("=" * 80)
        exit()
    
    print(f"\nEncontradas {total_sem_data} pendencias sem data")
    print("\nCorrigindo...")
    
    corrigidas = 0
    
    for pendencia in pendencias_sem_data:
        # Usar data_abertura como data da pendência
        if pendencia.data_abertura:
            pendencia.data = pendencia.data_abertura.date()
            corrigidas += 1
            print(f"   ID {pendencia.id}: data definida como {pendencia.data}")
        else:
            # Se nem data_abertura tiver, usar data atual
            pendencia.data = datetime.now().date()
            corrigidas += 1
            print(f"   ID {pendencia.id}: data definida como hoje ({pendencia.data})")
    
    # Salvar alterações
    db.session.commit()
    
    print(f"\n{corrigidas} pendencias corrigidas com sucesso!")
    
    # Verificar se ainda existem pendências sem data
    ainda_sem_data = Pendencia.query.filter(Pendencia.data == None).count()
    
    if ainda_sem_data > 0:
        print(f"\nAinda existem {ainda_sem_data} pendencias sem data.")
    else:
        print("\nTodas as pendencias agora tem data!")
    
    print("=" * 80)
    print("\nProximos passos:")
    print("   1. Atualize a pagina no navegador (F5)")
    print("   2. As datas devem aparecer agora")
    print("\nPara evitar este problema no futuro:")
    print("   - Sempre preencha o campo 'Data' ao criar pendencias")
    print("   - O sistema agora usa data_abertura como fallback")

