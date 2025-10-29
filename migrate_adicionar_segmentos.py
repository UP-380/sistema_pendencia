#!/usr/bin/env python3
"""
Script de migração: Cria tabela de segmentos e adiciona campo segmento_id à tabela empresa.

Este script:
1. Cria a tabela 'segmento' (se não existir)
2. Adiciona a coluna 'segmento_id' à tabela 'empresa' (se não existir)
3. Cria segmentos de exemplo (opcional)
4. Associa empresas aos segmentos (opcional)

ATENÇÃO: Teste em staging antes de executar em produção!
"""

from app import app, db, Segmento, Empresa
from sqlalchemy import inspect, text
import sys

def verificar_estrutura():
    """Verifica se as tabelas e colunas necessárias existem"""
    with app.app_context():
        inspector = inspect(db.engine)
        
        # Verificar tabela segmento
        tem_tabela_segmento = 'segmento' in inspector.get_table_names()
        
        # Verificar coluna segmento_id em empresa
        colunas_empresa = [col['name'] for col in inspector.get_columns('empresa')]
        tem_coluna_segmento = 'segmento_id' in colunas_empresa
        
        return tem_tabela_segmento, tem_coluna_segmento

def criar_estrutura():
    """Cria as estruturas necessárias no banco de dados"""
    with app.app_context():
        print("🔄 Criando estruturas de banco de dados...")
        
        try:
            # Criar todas as tabelas definidas nos models (incluindo segmento)
            db.create_all()
            print("✅ Tabelas criadas/verificadas com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao criar estruturas: {e}")
            return False

def criar_segmentos_exemplo():
    """Cria segmentos de exemplo"""
    with app.app_context():
        segmentos_exemplo = [
            'Financeiro',
            'Operacional',
            'Comercial',
            'Administrativo',
            'Tecnologia'
        ]
        
        print("\n🔄 Criando segmentos de exemplo...")
        criados = 0
        
        for nome_segmento in segmentos_exemplo:
            # Verificar se já existe
            segmento_existe = Segmento.query.filter_by(nome=nome_segmento).first()
            
            if not segmento_existe:
                novo_segmento = Segmento(nome=nome_segmento)
                db.session.add(novo_segmento)
                criados += 1
                print(f"  ✅ Criado: {nome_segmento}")
            else:
                print(f"  ⏭️  Já existe: {nome_segmento}")
        
        if criados > 0:
            try:
                db.session.commit()
                print(f"\n✅ {criados} segmento(s) criado(s) com sucesso!")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Erro ao salvar segmentos: {e}")
                return False
        
        return True

def associar_empresas_segmentos():
    """Permite associar empresas existentes aos segmentos"""
    with app.app_context():
        # Verificar se há segmentos
        segmentos = Segmento.query.all()
        if not segmentos:
            print("\n⚠️  Nenhum segmento cadastrado. Execute create_segmentos_exemplo primeiro.")
            return
        
        # Verificar se há empresas
        empresas = Empresa.query.all()
        if not empresas:
            print("\n⚠️  Nenhuma empresa cadastrada.")
            return
        
        print("\n📋 Empresas disponíveis:")
        for empresa in empresas:
            segmento_atual = empresa.segmento.nome if empresa.segmento else "Sem segmento"
            print(f"  {empresa.id}. {empresa.nome} (Segmento atual: {segmento_atual})")
        
        print("\n📋 Segmentos disponíveis:")
        for segmento in segmentos:
            print(f"  {segmento.id}. {segmento.nome}")
        
        print("\n⚠️  Para associar empresas, edite este script ou use a interface web.")

def main():
    """Função principal de migração"""
    print("=" * 80)
    print("SCRIPT DE MIGRAÇÃO: Estrutura de Segmentos")
    print("=" * 80)
    
    # Verificar estrutura atual
    tem_tabela, tem_coluna = verificar_estrutura()
    
    print("\n📊 Status atual:")
    print(f"  • Tabela 'segmento': {'✅ Existe' if tem_tabela else '❌ Não existe'}")
    print(f"  • Coluna 'segmento_id' em 'empresa': {'✅ Existe' if tem_coluna else '❌ Não existe'}")
    
    if tem_tabela and tem_coluna:
        print("\n✅ Estrutura já está atualizada!")
        
        resposta = input("\nDeseja criar segmentos de exemplo? (sim/não): ").strip().lower()
        if resposta in ['sim', 's', 'yes', 'y']:
            criar_segmentos_exemplo()
        
        return
    
    # Solicitar confirmação
    print("\n⚠️  Serão criadas/atualizadas as seguintes estruturas:")
    if not tem_tabela:
        print("  • Tabela 'segmento'")
    if not tem_coluna:
        print("  • Coluna 'segmento_id' na tabela 'empresa'")
    
    resposta = input("\nDeseja continuar? (sim/não): ").strip().lower()
    if resposta not in ['sim', 's', 'yes', 'y']:
        print("❌ Migração cancelada pelo usuário.")
        return
    
    # Criar estruturas
    if not criar_estrutura():
        print("\n❌ Falha ao criar estruturas.")
        sys.exit(1)
    
    # Perguntar se deseja criar segmentos de exemplo
    resposta = input("\nDeseja criar segmentos de exemplo? (sim/não): ").strip().lower()
    if resposta in ['sim', 's', 'yes', 'y']:
        criar_segmentos_exemplo()
    
    print("\n✅ Migração concluída com sucesso!")
    print("\n💡 Dica: Para associar empresas aos segmentos, use a interface administrativa.")

if __name__ == '__main__':
    main()


