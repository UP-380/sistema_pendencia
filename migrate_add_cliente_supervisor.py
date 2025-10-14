"""
Script de migração para adicionar o tipo de usuário 'cliente_supervisor'
e configurar suas permissões padrão no sistema.

Execução: python migrate_add_cliente_supervisor.py
"""

import sqlite3
from datetime import datetime

def migrate():
    """Adiciona permissões para o tipo de usuário cliente_supervisor"""
    
    print("=" * 60)
    print("MIGRAÇÃO: Adicionar Cliente Supervisor")
    print("=" * 60)
    
    conn = sqlite3.connect('instance/pendencias.db')
    cursor = conn.cursor()
    
    try:
        # Verificar se a tabela existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='permissao_usuario_tipo'
        """)
        
        if not cursor.fetchone():
            print("❌ Tabela permissao_usuario_tipo não encontrada!")
            print("   Execute primeiro a criação das tabelas do sistema.")
            return
        
        # Lista de permissões para cliente_supervisor
        permissoes_cliente_supervisor = [
            ('cliente_supervisor', 'cadastrar_pendencia', False),
            ('cliente_supervisor', 'editar_pendencia', False),
            ('cliente_supervisor', 'importar_planilha', False),
            ('cliente_supervisor', 'baixar_anexo', True),
            ('cliente_supervisor', 'aprovar_pendencia', False),
            ('cliente_supervisor', 'recusar_pendencia', False),
            ('cliente_supervisor', 'exportar_logs', True),
            ('cliente_supervisor', 'gerenciar_usuarios', False),
            ('cliente_supervisor', 'gerenciar_empresas', False),
            ('cliente_supervisor', 'visualizar_relatorios', True),
        ]
        
        print("\n📋 Configurando permissões para cliente_supervisor...")
        
        for tipo_usuario, funcionalidade, permitido in permissoes_cliente_supervisor:
            # Verificar se já existe
            cursor.execute("""
                SELECT id FROM permissao_usuario_tipo 
                WHERE tipo_usuario = ? AND funcionalidade = ?
            """, (tipo_usuario, funcionalidade))
            
            existing = cursor.fetchone()
            
            if existing:
                # Atualizar
                cursor.execute("""
                    UPDATE permissao_usuario_tipo 
                    SET permitido = ? 
                    WHERE tipo_usuario = ? AND funcionalidade = ?
                """, (permitido, tipo_usuario, funcionalidade))
                print(f"   ✅ Atualizado: {funcionalidade} = {permitido}")
            else:
                # Inserir
                cursor.execute("""
                    INSERT INTO permissao_usuario_tipo (tipo_usuario, funcionalidade, permitido)
                    VALUES (?, ?, ?)
                """, (tipo_usuario, funcionalidade, permitido))
                print(f"   ➕ Criado: {funcionalidade} = {permitido}")
        
        # Commit das alterações
        conn.commit()
        
        # Verificar resultado
        cursor.execute("""
            SELECT funcionalidade, permitido 
            FROM permissao_usuario_tipo 
            WHERE tipo_usuario = 'cliente_supervisor'
            ORDER BY funcionalidade
        """)
        
        permissoes = cursor.fetchall()
        
        print("\n" + "=" * 60)
        print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 60)
        print(f"\n📊 Total de permissões configuradas: {len(permissoes)}")
        print("\n🔐 Permissões do Cliente Supervisor:")
        print("-" * 60)
        
        for funcionalidade, permitido in permissoes:
            status = "✅ Permitido" if permitido else "❌ Negado"
            print(f"   {funcionalidade:30} → {status}")
        
        print("\n" + "=" * 60)
        print("📝 RESUMO DAS FUNCIONALIDADES DO CLIENTE SUPERVISOR:")
        print("=" * 60)
        print("""
✅ Pode:
   • Responder pendências normalmente
   • Visualizar pendências resolvidas
   • Acessar dashboards e relatórios
   • Exportar logs e relatórios
   • Baixar anexos
   • Ver relatório mensal
   • Ver relatório de operadores

❌ Não pode:
   • Criar ou editar pendências manualmente
   • Importar planilhas
   • Aprovar ou recusar pendências como operador/supervisor
   • Gerenciar usuários
   • Gerenciar empresas
        """)
        
        print("\n" + "=" * 60)
        print("🎯 PRÓXIMOS PASSOS:")
        print("=" * 60)
        print("""
1. Reinicie a aplicação para carregar as novas permissões
2. Crie usuários do tipo 'cliente_supervisor' no painel admin
3. Associe empresas aos clientes supervisores
4. Teste o acesso com um usuário cliente_supervisor
        """)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ERRO durante a migração: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        conn.close()
    
    return True

if __name__ == '__main__':
    print("\n🚀 Iniciando migração para Cliente Supervisor...")
    print(f"📅 Data/Hora: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
    print()
    
    sucesso = migrate()
    
    if sucesso:
        print("\n✅ Migração executada com sucesso!")
        print("   O tipo 'cliente_supervisor' está pronto para uso.")
    else:
        print("\n❌ Migração falhou!")
        print("   Verifique os erros acima e tente novamente.")
    
    print("\n" + "=" * 60)

