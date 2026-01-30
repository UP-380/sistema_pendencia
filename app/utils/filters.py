def datetime_local_filter(dt):
    """Formata datetime para exibição local"""
    if dt is None:
        return ""
    return dt.strftime('%d/%m/%Y %H:%M')

def nome_tipo_usuario_filter(tipo):
    """Retorna o nome amigável do tipo de usuário"""
    nomes = {
        'adm': 'Administrador',
        'supervisor': 'Supervisor',
        'operador': 'Operador',
        'cliente': 'Cliente',
        'cliente_supervisor': 'Cliente Supervisor'
    }
    return nomes.get(tipo, tipo.capitalize())
