import os
import re

def fix_url_endpoints():
    templates_dir = 'templates'
    
    # Mapeamento de endpoints para seus blueprints
    # auth
    auth_endpoints = ['login', 'logout']
    
    # main (lista parcial, o script vai assumir 'main' para tudo que nÃ£o for 'auth' ou 'static')
    # mas vamos listar os comuns para garantir
    
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                path = os.path.join(root, file)
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                
                # Regex para capturar url_for('endpoint', ...)
                # Grupos: 1=quote, 2=endpoint, 3=quote
                # Exemplo: url_for('login') -> url_for('auth.login')
                
                def replace_endpoint(match):
                    full_match = match.group(0)
                    endpoint = match.group(2)
                    
                    # Ignorar se jÃ¡ tiver ponto (ex: main.dashboard) ou for static
                    if '.' in endpoint or endpoint == 'static':
                        return full_match
                    
                    if endpoint in auth_endpoints:
                        new_endpoint = f"auth.{endpoint}"
                    else:
                        new_endpoint = f"main.{endpoint}"
                        
                    print(f"[{file}] Fixing {endpoint} -> {new_endpoint}")
                    return f"url_for({match.group(1)}{new_endpoint}{match.group(3)}"

                # Padrão: url_for( ('|") endpoint ('|")
                new_content = re.sub(r"url_for\(\s*(['\"])([\w_]+)(['\"])", replace_endpoint, new_content)
                
                if new_content != content:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

if __name__ == '__main__':
    fix_url_endpoints()
