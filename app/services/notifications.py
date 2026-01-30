import requests
from flask import current_app

def notificar_teams(pendencia):
    webhook_url = current_app.config.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        return
        
    mensagem = {
        "title": "Pendência Atualizada pelo Cliente",
        "text": (
            f"O cliente <b>USUARIO</b> informou sobre a pendência <b>ID {pendencia.id}</b>:<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Observação:</b> {pendencia.observacao}<br><br>"
            f"<b>@Luiz Marcelo</b> (luiz.marcelo@up380.com.br) verifique esta atualização!"
        )
    }
    _enviar_teams(webhook_url, mensagem, "0076D7")

def notificar_teams_pendente_operador(pendencia):
    """Notifica quando pendência fica PENDENTE OPERADOR UP"""
    webhook_url = current_app.config.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        return
        
    mensagem = {
        "title": "🔄 Pendência PENDENTE OPERADOR UP",
        "text": (
            f"<b>Nova pendência aguardando operador!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Resposta do Cliente:</b> {pendencia.resposta_cliente}<br><br>"
            f"<b>@Operadores UP380</b> - Pendência aguardando Natureza de Operação!"
        )
    }
    _enviar_teams(webhook_url, mensagem, "FFA500")

def notificar_teams_pendente_supervisor(pendencia):
    """Notifica quando pendência fica PENDENTE SUPERVISOR UP"""
    webhook_url = current_app.config.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        return
        
    mensagem = {
        "title": "👨‍💼 Pendência PENDENTE SUPERVISOR UP",
        "text": (
            f"<b>Pendência aguardando aprovação do supervisor!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Natureza de Operação:</b> {pendencia.natureza_operacao}<br><br>"
            f"<b>@Supervisores UP380</b> - Pendência aguardando resolução!"
        )
    }
    _enviar_teams(webhook_url, mensagem, "FF0000")

def notificar_teams_recusa_cliente(pendencia):
    """Notifica quando operador recusa resposta do cliente"""
    webhook_url = current_app.config.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        return
        
    mensagem = {
        "title": "❌ Resposta Recusada - Complemento Necessário",
        "text": (
            f"<b>Operador recusou a resposta do cliente!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Motivo da Recusa:</b> {pendencia.motivo_recusa}<br><br>"
            f"<b>@Cliente</b> - Pendência aguardando complemento de informações!"
        )
    }
    _enviar_teams(webhook_url, mensagem, "FF6B35")

def notificar_teams_recusa_supervisor(pendencia):
    """Notifica quando pendência é recusada pelo supervisor e devolvida ao operador"""
    webhook_url = current_app.config.get('TEAMS_WEBHOOK_URL')
    if not webhook_url:
        return
        
    mensagem = {
        "title": "🔄 Pendência Devolvida pelo Supervisor",
        "text": (
            f"<b>Pendência recusada e devolvida ao operador!</b><br><br>"
            f"<b>ID:</b> {pendencia.id}<br>"
            f"<b>Empresa:</b> {pendencia.empresa}<br>"
            f"<b>Fornecedor/Cliente:</b> {pendencia.fornecedor_cliente}<br>"
            f"<b>Valor:</b> R$ {pendencia.valor:.2f}<br>"
            f"<b>Natureza de Operação:</b> {pendencia.natureza_operacao}<br>"
            f"<b>Motivo da Recusa:</b> {pendencia.motivo_recusa_supervisor}<br><br>"
            f"<b>@Operadores UP380</b> - Pendência devolvida para correção!"
        )
    }
    _enviar_teams(webhook_url, mensagem, "FFA500")

def _enviar_teams(webhook_url, mensagem, color):
    try:
        requests.post(webhook_url, json={
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "summary": mensagem["title"],
            "themeColor": color,
            "title": mensagem["title"],
            "text": mensagem["text"]
        }, timeout=5)
    except Exception as e:
        print(f"Erro ao notificar Teams: {e}")
