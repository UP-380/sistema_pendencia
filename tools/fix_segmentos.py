from app import create_app, db
from app.models import Segmento, Empresa, Pendencia

app = create_app()

with app.app_context():
    print("🔍 DIAGNÓSTICO DE DADOS:")
    
    # 1. Contar Pendências (A prova real)
    total_pendencias = Pendencia.query.count()
    print(f"📊 Total de Pendências no Banco: {total_pendencias}")
    
    if total_pendencias > 0:
        print("✅ SEUS DADOS ESTÃO AQUI! (Não infarte!)")
    else:
        print("⚠️  Banco parece vazio. Verifique se o arquivo pendencias.db foi montado corretmente.")
        
    # 2. Corrigir Segmentos (O motivo da tela branca)
    print("\n🛠️  CORRIGINDO VISUALIZAÇÃO...")
    
    # Criar segmento Padrão se não existir
    segmento_geral = Segmento.query.filter_by(nome="Geral").first()
    if not segmento_geral:
        segmento_geral = Segmento(nome="Geral")
        db.session.add(segmento_geral)
        db.session.commit()
        print(f"✅ Segmento 'Geral' criado.")
    else:
        print(f"ℹ️  Segmento 'Geral' já existe.")
        
    # Vincular TODAS as empresas sem segmento ao "Geral"
    empresas = Empresa.query.filter(Empresa.segmento_id == None).all()
    count_updates = 0
    for empresa in empresas:
        empresa.segmento_id = segmento_geral.id
        count_updates += 1
    
    if count_updates > 0:
        db.session.commit()
        print(f"✅ {count_updates} empresas vinculadas ao segmento 'Geral'.")
    else:
        print("ℹ️  Todas as empresas já têm segmento.")
        
    print("\n🚀 TUDO PRONTO! Atualize a página e seus dados vão aparecer.")
