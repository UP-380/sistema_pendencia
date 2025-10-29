#!/usr/bin/env python3
"""
Script de migração automática: Consolida tipos "Nota Fiscal Não Anexada" e "Nota Fiscal Não Identificada"
para o novo tipo "Documento Não Anexado".

ATENÇÃO: Este script NÃO solicita confirmação. Use com cuidado!
Execute em staging primeiro e verifique os resultados antes de rodar em produção.
"""

from app import app, db, Pendencia
from datetime import datetime
import sys

def migrar_notas_fiscais_auto():
    """Migra tipos antigos de Nota Fiscal para Documento Não Anexado (sem confirmação)"""
    
    with app.app_context():
        # Tipos antigos a serem migrados
        tipos_antigos = ['Nota Fiscal Não Anexada', 'Nota Fiscal Não Identificada']
        novo_tipo = 'Documento Não Anexado'
        
        # Buscar pendências com tipos antigos
        pendencias = Pendencia.query.filter(
            Pendencia.tipo_pendencia.in_(tipos_antigos)
        ).all()
        
        if not pendencias:
            print("[OK] Nenhuma pendencia encontrada com os tipos antigos de Nota Fiscal.")
            return True
        
        print(f"[INFO] Migrando {len(pendencias)} pendencias automaticamente...")
        contador = 0
        
        for pendencia in pendencias:
            pendencia.tipo_pendencia = novo_tipo
            contador += 1
        
        # Commit das alterações
        try:
            db.session.commit()
            print(f"[OK] {contador} registro(s) migrado(s) com sucesso em {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"[ERRO] Erro ao salvar migracao: {e}")
            return False

if __name__ == '__main__':
    success = migrar_notas_fiscais_auto()
    sys.exit(0 if success else 1)


