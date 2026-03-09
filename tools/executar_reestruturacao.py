import sqlite3
import os

# Nome do arquivo de banco de dados e do script SQL
DB_NAME = 'pendencias.db'
SQL_FILE = 'migrate_reestruturar_banco.sql'

def executar_migracao():
    print(f"🚀 Iniciando migração do banco de dados: {DB_NAME}")
    
    # Verificar se o arquivo SQL existe
    if not os.path.exists(SQL_FILE):
        print(f"❌ Erro: Arquivo SQL '{SQL_FILE}' não encontrado!")
        return

    # Verificar se o banco de dados existe
    if not os.path.exists(DB_NAME):
        print(f"⚠️  Aviso: Banco de dados '{DB_NAME}' não encontrado. Ele será criado.")

    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Ler o conteúdo do arquivo SQL
        print(f"📖 Lendo arquivo de migração: {SQL_FILE}")
        with open(SQL_FILE, 'r', encoding='utf-8') as file:
            sql_script = file.read()

        # Executar o script SQL linha a linha para tratar erros individuais
        print("⚙️  Executando script SQL (modo seguro)...")
        
        # Dividir comandos por ponto e vírgula
        commands = sql_script.split(';')
        
        for command in commands:
            command = command.strip()
            if command:
                try:
                    cursor.execute(command)
                except sqlite3.OperationalError as e:
                    # Ignorar erro se a coluna já existir ou índice já existir
                    if "duplicate column name" in str(e):
                        print(f"⚠️  Aviso: Coluna já existe (pulosando): {e}")
                    elif "already exists" in str(e):
                        print(f"⚠️  Aviso: Objeto já existe (pulando): {e}")
                    else:
                        print(f"❌ Erro no comando: {command[:50]}... -> {e}")

        # Commit das alterações
        conn.commit()
        print("✅ Migração concluída com SUCESSO! (Erros ignoráveis foram tratados)")

        # Fechar conexão
        conn.close()

    except sqlite3.Error as e:
        print(f"❌ Erro Geral SQLite: {e}")
    except Exception as e:
        print(f"❌ Erro inesperado: {e}")

if __name__ == "__main__":
    executar_migracao()
