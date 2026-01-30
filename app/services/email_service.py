from flask import url_for
from flask_mail import Message
from app.extensions import mail

def enviar_email_cliente(pendencia):
    if not pendencia.email_cliente:
        return
    link = url_for('main.ver_pendencia', token=pendencia.token_acesso, _external=True)
    msg = Message(
        'Pendência Financeira Identificada',
        recipients=[pendencia.email_cliente]
    )
    msg.body = f"""
    Olá,

    Identificamos uma pendência no valor de R$ {pendencia.valor:.2f}.

    Por favor, acesse o link abaixo para nos informar do que se trata:
    {link}

    Obrigado,
    Equipe UP380
    """
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")

def enviar_email_resposta_recusada(pendencia, motivo_recusa):
    """Envia e-mail ao cliente informando que sua resposta foi recusada"""
    if not pendencia.email_cliente:
        return
    
    link = url_for('main.ver_pendencia', token=pendencia.token_acesso, _external=True)
    msg = Message(
        'Resposta Recusada - Pendência Financeira',
        recipients=[pendencia.email_cliente]
    )
    msg.body = f"""
    Olá,

    Sua resposta para a pendência no valor de R$ {pendencia.valor:.2f} foi recusada.

    Motivo da recusa: {motivo_recusa}

    Por favor, acesse o link abaixo para ver sua resposta anterior e o motivo da recusa:
    {link}

    Ao reabrir o link, você verá sua resposta anterior e o motivo da recusa.

    Obrigado,
    Equipe UP380
    """
    try:
        mail.send(msg)
    except Exception as e:
        print(f"Erro ao enviar email: {e}")
