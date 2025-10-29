#!/usr/bin/env python3
"""
Script de inicialização do banco de dados.

Este script:
1. Cria todas as tabelas necessárias
2. Cria usuários iniciais (admin e cliente padrão)
3. Migra empresas da lista EMPRESAS para o modelo Empresa
4. Configura permissões padrão para todos os tipos de usuário
5. Cria estrutura de segmentos (opcional)

Execute este script após clonar o repositório ou após atualizações que modifiquem o schema.
"""

from app import app, db, criar_usuarios_iniciais, migrar_empresas_existentes, configurar_permissoes_padrao
from app import Segmento, Empresa, Usuario, PermissaoUsuarioTipo
import sys

def verificar_banco():
    """Verifica o estado atual do banco de dados"""
    with app.app_context():
        try:
            # Tentar contar registros das principais tabelas
            total_empresas = Empresa.query.count()
            total_usuarios = Usuario.query.count()
            total_segmentos = Segmento.query.count()
            total_permissoes = PermissaoUsuarioTipo.query.count()
            
            print("\n📊 Estado atual do banco de dados:")
            print(f"  • Empresas: {total_empresas}")
            print(f"  • Usuários: {total_usuarios}")
            print(f"  • Segmentos: {total_segmentos}")
            print(f"  • Permissões: {total_permissoes}")
            
            return True
        except Exception as e:
            print(f"\n⚠️  Banco de dados não inicializado ou com problemas: {e}")
            return False

def inicializar_banco():
    """Inicializa o banco de dados com todas as estruturas"""
    with app.app_context():
        print("\n🔄 Criando estruturas do banco de dados...")
        
        try:
            # Criar todas as tabelas
            db.create_all()
            print("✅ Tabelas criadas com sucesso!")
            
            # Criar usuários iniciais
            print("\n🔄 Criando usuários iniciais...")
            criar_usuarios_iniciais()
            print("✅ Usuários iniciais criados/verificados!")
            
            # Migrar empresas
            print("\n🔄 Migrando empresas...")
            migrar_empresas_existentes()
            print("✅ Empresas migradas com sucesso!")
            
            # Configurar permissões
            print("\n🔄 Configurando permissões padrão...")
            configurar_permissoes_padrao()
            db.session.commit()
            print("✅ Permissões configuradas com sucesso!")
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro durante inicialização: {e}")
            return False

def criar_segmentos_basicos():
    """Cria segmentos básicos se não existirem"""
    with app.app_context():
        if Segmento.query.count() > 0:
            print("\n⏭️  Segmentos já existem. Pulando criação.")
            return
        
        print("\n🔄 Criando segmentos básicos...")
        segmentos = ['Financeiro', 'Operacional', 'Comercial', 'Administrativo']
        
        for nome in segmentos:
            seg = Segmento(nome=nome)
            db.session.add(seg)
            print(f"  ✅ Criado: {nome}")
        
        try:
            db.session.commit()
            print("✅ Segmentos criados com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao criar segmentos: {e}")

def main():
    """Função principal"""
    print("=" * 80)
    print("SCRIPT DE INICIALIZAÇÃO DO BANCO DE DADOS")
    print("Sistema de Pendências UP380")
    print("=" * 80)
    
    # Verificar estado atual
    banco_ok = verificar_banco()
    
    if banco_ok:
        print("\n✅ Banco de dados já está inicializado!")
        resposta = input("\nDeseja reconfigurar as estruturas? (sim/não): ").strip().lower()
        
        if resposta not in ['sim', 's', 'yes', 'y']:
            print("\n💡 Nenhuma alteração realizada.")
            print("   Para criar segmentos, execute: python migrate_adicionar_segmentos.py")
            print("   Para migrar tipos de pendência, execute: python migrate_nota_fiscal_para_documento.py")
            return
    
    # Inicializar/reconfigurar
    print("\n⚠️  Iniciando processo de inicialização/reconfiguração...")
    print("    Isso criará todas as tabelas e configurações necessárias.")
    
    if banco_ok:
        resposta = input("\nTem certeza? (sim/não): ").strip().lower()
        if resposta not in ['sim', 's', 'yes', 'y']:
            print("❌ Operação cancelada.")
            return
    
    # Executar inicialização
    if not inicializar_banco():
        print("\n❌ Falha na inicialização do banco de dados!")
        sys.exit(1)
    
    # Perguntar sobre segmentos
    resposta = input("\nDeseja criar segmentos básicos? (sim/não): ").strip().lower()
    if resposta in ['sim', 's', 'yes', 'y']:
        criar_segmentos_basicos()
    
    # Verificar resultado final
    verificar_banco()
    
    print("\n" + "=" * 80)
    print("✅ INICIALIZAÇÃO CONCLUÍDA COM SUCESSO!")
    print("=" * 80)
    print("\n📋 Próximos passos:")
    print("  1. Acesse o sistema com o usuário admin:")
    print("     Email: adm.pendencia@up380.com.br")
    print("     Senha: Finance.@2")
    print("  2. Configure segmentos e associe empresas (se aplicável)")
    print("  3. Crie usuários adicionais conforme necessário")
    print("\n💡 Scripts de migração disponíveis:")
    print("  • python migrate_adicionar_segmentos.py")
    print("  • python migrate_nota_fiscal_para_documento.py")
    print("  • python migrate_cliente_supervisor.py")

if __name__ == '__main__':
    main()


