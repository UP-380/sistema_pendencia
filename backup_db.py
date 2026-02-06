import os
import shutil
from datetime import datetime

def backup_database():
    # Caminhos baseados na estrutura do projeto
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'pendencias.db')
    backup_dir = os.path.join(basedir, 'backups')
    
    # Criar diretório de backups se não existir
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
        print(f"📁 Diretório de backups criado: {backup_dir}")

    if not os.path.exists(db_path):
        # Tentar no root caso não esteja em instance
        db_path = os.path.join(basedir, 'pendencias.db')
        if not os.path.exists(db_path):
            print("❌ Erro: Arquivo pendencias.db não encontrado.")
            return

    # Nome do arquivo de backup com timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"pendencias_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_file)

    try:
        shutil.copy2(db_path, backup_path)
        print(f"✅ Backup concluído com sucesso!")
        print(f"📄 Arquivo: {backup_file}")
        print(f"📍 Local: {backup_path}")
    except Exception as e:
        print(f"❌ Erro ao realizar backup: {str(e)}")

if __name__ == "__main__":
    backup_database()
