#!/usr/bin/env python3
"""
Script de migração: Adiciona permissões padrão para o novo tipo de usuário "cliente_supervisor".

Este script configura as permissões padrão do perfil Cliente Supervisor:
- Visualização avançada (dashboards, relatórios, logs, pendências resolvidas)
- Edição de observações
- Exportação de dados
- Download de anexos
- SEM permissões de criação, edição ou exclusão de pendências
- SEM permissões administrativas
"""

from app import app, db, PermissaoUsuarioTipo, configurar_permissoes_padrao

def migrar_permissoes_cliente_supervisor():
    """Adiciona/atualiza permissões do cliente_supervisor"""
    
    with app.app_context():
        print("=" * 80)
        print("SCRIPT DE MIGRACAO: Permissoes Cliente Supervisor")
        print("=" * 80)
        
        # Verificar se já existem permissões para cliente_supervisor
        permissoes_existentes = PermissaoUsuarioTipo.query.filter_by(
            tipo_usuario='cliente_supervisor'
        ).count()
        
        if permissoes_existentes > 0:
            print(f"\n[INFO] Ja existem {permissoes_existentes} permissoes configuradas para 'cliente_supervisor'.")
            print("[INFO] Reconfigurando automaticamente...")
            
            # Remover permissões antigas
            print("[INFO] Removendo permissoes antigas...")
            PermissaoUsuarioTipo.query.filter_by(tipo_usuario='cliente_supervisor').delete()
            db.session.commit()
        
        print("\n[INFO] Configurando permissoes padrao para 'cliente_supervisor'...")
        
        # Configurar permissões usando a função do app.py
        try:
            configurar_permissoes_padrao()
            db.session.commit()
            
            # Verificar resultado
            total_permissoes = PermissaoUsuarioTipo.query.filter_by(
                tipo_usuario='cliente_supervisor'
            ).count()
            
            print(f"\n[OK] Permissoes configuradas com sucesso!")
            print(f"   Total de permissoes criadas: {total_permissoes}")
            
            # Exibir permissões configuradas
            print("\n[INFO] Permissoes do Cliente Supervisor:")
            print("-" * 80)
            permissoes = PermissaoUsuarioTipo.query.filter_by(
                tipo_usuario='cliente_supervisor'
            ).order_by(PermissaoUsuarioTipo.funcionalidade).all()
            
            permitidas = [p for p in permissoes if p.permitido]
            negadas = [p for p in permissoes if not p.permitido]
            
            print("\n[OK] PERMITIDAS:")
            for p in permitidas:
                print(f"  - {p.funcionalidade}")
            
            print("\n[NEGADO] NEGADAS:")
            for p in negadas:
                print(f"  - {p.funcionalidade}")
            
            print("-" * 80)
            
        except Exception as e:
            db.session.rollback()
            print(f"\n[ERRO] Erro ao configurar permissoes: {e}")
            return False
        
        return True

if __name__ == '__main__':
    migrar_permissoes_cliente_supervisor()


