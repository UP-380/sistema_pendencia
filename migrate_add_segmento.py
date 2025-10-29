#!/usr/bin/env python3
"""
Script para criar a estrutura de segmentos e migrar empresas existentes.
Execute uma única vez após adicionar o código.

Este script:
1. Cria a tabela segmento (se não existir)
2. Adiciona coluna segmento_id em empresa (se não existir)
3. Cria os 3 segmentos (FUNERÁRIA, PROTEÇÃO VEICULAR, FARMÁCIA)
4. Vincula todas as 37 empresas aos seus respectivos segmentos
5. Exibe resumo completo da migração

Uso:
    python migrate_add_segmento.py
"""

from app import app, db, Segmento, Empresa
from sqlalchemy import text
import sys

def migrate():
    with app.app_context():
        print("=" * 80)
        print("🚀 INICIANDO MIGRAÇÃO DE SEGMENTOS")
        print("=" * 80)
        
        # 1. Criar tabela segmento
        print("\n📊 Passo 1: Criando tabela segmento...")
        try:
            db.session.execute(text(
                """
                CREATE TABLE IF NOT EXISTS segmento (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome VARCHAR(100) UNIQUE NOT NULL
                )
                """
            ))
            db.session.commit()
            print("✅ Tabela segmento criada/verificada com sucesso!")
        except Exception as e:
            print(f"⚠️  Erro ao criar tabela segmento: {e}")
            db.session.rollback()
        
        # 2. Adicionar coluna segmento_id em empresa
        print("\n📊 Passo 2: Adicionando coluna segmento_id em empresa...")
        try:
            info = db.session.execute(text("PRAGMA table_info(empresa)")).fetchall()
            has_segmento_id = any(row[1] == 'segmento_id' for row in info)
            
            if not has_segmento_id:
                db.session.execute(text("ALTER TABLE empresa ADD COLUMN segmento_id INTEGER"))
                db.session.commit()
                print("✅ Coluna segmento_id adicionada com sucesso!")
            else:
                print("ℹ️  Coluna segmento_id já existe!")
        except Exception as e:
            print(f"⚠️  Erro ao adicionar coluna: {e}")
            db.session.rollback()
        
        # 3. Criar segmentos e vincular empresas
        print("\n📊 Passo 3: Criando segmentos e vinculando empresas...")
        
        ESTRUTURA_SEGMENTOS = {
            'FUNERÁRIA': [
                'PLANO PAI', 'ECO MEMORIAL', 'PAXDOMINI', 'GRUPO COLINA', 
                'OFEBAS', 'FENIX FUNERÁRIA', 'PREDIGNA', 'ASFAP'
            ],
            'PROTEÇÃO VEICULAR': [
                'MASTER', 'ALIANZE', 'BRTRUCK', 'CANAÃ', 'COOPERATRUCK', 'ELEVAMAIS',
                'SPEED', 'RAIO', 'EXODO', 'GTA', 'MOVIDAS', 'PROTEGE ASSOCIAÇÕES',
                'TECH PROTEGE', 'UNIK', 'ARX', 'VALLE', 'CEL', 'ADMAS', 'INNOVARE',
                'AUTOBRAS', 'ANCORE', '7 MARES ASSOCIAÇÃO', 'AUTOALLIANCE',
                'ROYALE ASSOCIAÇÕES', 'ARX TRAINNING', 'ARX TECH', 'ARX ASSIST', 'YAP'
            ],
            'FARMÁCIA': ['LONGEVITÁ']
        }
        
        segmentos_map = {}
        empresas_criadas = 0
        empresas_vinculadas = 0
        
        for segmento_nome in ESTRUTURA_SEGMENTOS.keys():
            print(f"\n🔹 Processando segmento: {segmento_nome}")
            
            # Criar ou obter segmento
            segmento = Segmento.query.filter_by(nome=segmento_nome).first()
            if not segmento:
                segmento = Segmento(nome=segmento_nome)
                db.session.add(segmento)
                db.session.flush()
                print(f"   ✅ Segmento '{segmento_nome}' criado!")
            else:
                print(f"   ℹ️  Segmento '{segmento_nome}' já existe!")
            
            segmentos_map[segmento_nome] = segmento.id
            
            # Vincular empresas ao segmento
            empresas_lista = ESTRUTURA_SEGMENTOS[segmento_nome]
            for nome_empresa in empresas_lista:
                empresa = Empresa.query.filter_by(nome=nome_empresa).first()
                
                if not empresa:
                    empresa = Empresa(nome=nome_empresa, segmento_id=segmento.id)
                    db.session.add(empresa)
                    empresas_criadas += 1
                    print(f"   ✅ Empresa '{nome_empresa}' criada e vinculada")
                elif empresa.segmento_id is None:
                    empresa.segmento_id = segmento.id
                    empresas_vinculadas += 1
                    print(f"   ✅ Empresa '{nome_empresa}' vinculada")
                else:
                    print(f"   ℹ️  Empresa '{nome_empresa}' já vinculada")
        
        try:
            db.session.commit()
            print("\n✅ Todas as alterações foram salvas no banco de dados!")
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Erro ao salvar alterações: {e}")
            sys.exit(1)
        
        # 4. Resumo final
        print("\n" + "=" * 80)
        print("📊 RESUMO DA MIGRAÇÃO")
        print("=" * 80)
        
        total_segmentos = Segmento.query.count()
        total_empresas = Empresa.query.count()
        empresas_sem_segmento = Empresa.query.filter_by(segmento_id=None).count()
        
        print(f"\n📈 Estatísticas Gerais:")
        print(f"   • Total de segmentos: {total_segmentos}")
        print(f"   • Total de empresas: {total_empresas}")
        print(f"   • Empresas criadas nesta migração: {empresas_criadas}")
        print(f"   • Empresas vinculadas nesta migração: {empresas_vinculadas}")
        print(f"   • Empresas sem segmento: {empresas_sem_segmento}")
        
        print(f"\n📋 Detalhamento por Segmento:")
        for segmento in Segmento.query.order_by(Segmento.nome).all():
            total_empresas_seg = Empresa.query.filter_by(segmento_id=segmento.id).count()
            
            # Ícone por segmento
            icone = "🏥"  # FUNERÁRIA
            if segmento.nome == "PROTEÇÃO VEICULAR":
                icone = "🛡️"
            elif segmento.nome == "FARMÁCIA":
                icone = "💊"
            
            print(f"   {icone} {segmento.nome}: {total_empresas_seg} empresas")
            
            # Listar empresas do segmento
            empresas_seg = Empresa.query.filter_by(segmento_id=segmento.id).order_by(Empresa.nome).all()
            for emp in empresas_seg:
                print(f"      • {emp.nome}")
        
        if empresas_sem_segmento > 0:
            print(f"\n⚠️  Atenção: Há {empresas_sem_segmento} empresa(s) sem segmento vinculado:")
            empresas_orfas = Empresa.query.filter_by(segmento_id=None).all()
            for emp in empresas_orfas:
                print(f"      • {emp.nome}")
            print("\n   Você pode vinculá-las manualmente através do painel administrativo.")
        
        print("\n" + "=" * 80)
        print("🎉 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
        print("=" * 80)
        
        print("\n📋 Próximos passos:")
        print("   1. Reinicie o servidor da aplicação")
        print("   2. Acesse a aplicação e faça login")
        print("   3. Você será redirecionado para a tela de segmentos")
        print("   4. Navegue: Segmentos → Empresas → Pendências")
        print("\n   Rotas disponíveis:")
        print("   • /segmentos - Tela principal de segmentos")
        print("   • /segmento/<id> - Empresas de um segmento")
        print("   • /gerenciar_segmentos - Gerenciar segmentos (admin/supervisor)")
        
        print("\n✨ O sistema de navegação hierárquica está pronto para uso!")
        print("=" * 80)

if __name__ == '__main__':
    print("\n⚠️  ATENÇÃO: Este script irá modificar o banco de dados.")
    print("   Certifique-se de ter um backup antes de continuar.\n")
    
    resposta = input("Deseja continuar? (sim/não): ").strip().lower()
    
    if resposta in ['sim', 's', 'yes', 'y']:
        migrate()
    else:
        print("\n❌ Migração cancelada pelo usuário.")
        sys.exit(0)


