from app import create_app
from app.extensions import db
from app.models import Usuario, Empresa, Segmento, PermissaoUsuarioTipo
from app.routes.main import configurar_permissoes_padrao
from werkzeug.security import generate_password_hash
import sys
import os

app = create_app()

def criar_usuarios_iniciais():
    """Cria os usuários iniciais do sistema se não existirem"""
    # Usuário Admin
    admin_email = 'adm.pendencia@up380.com.br'
    admin = Usuario.query.filter_by(email=admin_email).first()
    if not admin:
        admin = Usuario(
            email=admin_email,
            senha_hash=generate_password_hash('Finance.@2'),
            tipo='adm',
            ativo=True
        )
        db.session.add(admin)
        print(f"  ✅ Usuário Admin ({admin_email}) criado.")
    else:
        print(f"  ⏭️  Usuário Admin ({admin_email}) já existe.")

    # Usuário Cliente Teste
    cliente_email = 'cliente.teste@example.com'
    cliente = Usuario.query.filter_by(email=cliente_email).first()
    if not cliente:
        cliente = Usuario(
            email=cliente_email,
            senha_hash=generate_password_hash('Cliente.@123'),
            tipo='cliente',
            ativo=True
        )
        db.session.add(cliente)
        print(f"  ✅ Usuário Cliente ({cliente_email}) criado.")
    
    db.session.commit()

def migrar_empresas_existentes():
    """Garante que pelo menos uma empresa de exemplo exista no banco"""
    if Empresa.query.count() == 0:
        empresa = Empresa(nome='ALIANZE')
        db.session.add(empresa)
        db.session.commit()
        print("  ✅ Empresa ALIANZE criada como exemplo.")
    else:
        print("  ⏭️  Empresas já existem no banco.")

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
            # Criar pasta instance se não existir (para o SQLite)
            if not os.path.exists(app.instance_path):
                os.makedirs(app.instance_path)
                print(f"✅ Pasta {app.instance_path} criada!")

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
    
    # Verificar se o banco de dados existe fisicamente (SQLite)
    db_path = os.path.join(app.instance_path, 'pendencias.db')
    db_exists = os.path.exists(db_path)
    
    # Verificar estado atual (tabelas)
    banco_ok = verificar_banco() if db_exists else False
    
    if banco_ok:
        print("\n✅ Banco de dados já está inicializado!")
        # Se estiver rodando em um ambiente que permite input, pergunta. 
        # Caso contrário, poderíamos usar argumentos de linha de comando.
        try:
            resposta = input("\nDeseja reconfigurar/atualizar as estruturas? (sim/não): ").strip().lower()
            if resposta not in ['sim', 's', 'yes', 'y']:
                print("\n💡 Nenhuma alteração realizada.")
                return
        except EOFError:
            print("\n💡 Ambiente não interativo detectado. Pulando atualização.")
            return
    
    # Inicializar/reconfigurar
    print("\n⚠️  Iniciando processo de inicialização/reconfiguração...")
    print("    Isso criará todas as tabelas e configurações necessárias.")
    
    # Executar inicialização
    if not inicializar_banco():
        print("\n❌ Falha na inicialização do banco de dados!")
        sys.exit(1)
    
    # Criar segmentos default sem perguntar se for a primeira vez
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

if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()


