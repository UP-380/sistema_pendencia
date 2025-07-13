# Instruções para Atualizar a VPS

## Passos para atualizar o código na VPS:

1. **Conecte-se à VPS via SSH:**
   ```bash
   ssh root@SEU_IP_DA_VPS
   ```

2. **Navegue até o diretório do projeto:**
   ```bash
   cd /root/sistema_pendencia
   ```

3. **Pare os containers Docker:**
   ```bash
   docker-compose down
   ```

4. **Atualize o código do GitHub:**
   ```bash
   git pull origin main
   ```

5. **Reconstrua e inicie os containers:**
   ```bash
   docker-compose up --build -d
   ```

6. **Verifique se os containers estão rodando:**
   ```bash
   docker-compose ps
   ```

7. **Verifique os logs se necessário:**
   ```bash
   docker-compose logs -f
   ```

## Comandos em sequência (copie e cole):
```bash
cd /root/sistema_pendencia
docker-compose down
git pull origin main
docker-compose up --build -d
docker-compose ps
```

Após executar esses comandos, seu sistema estará atualizado com a "ATUALIZAÇÃO ESTRATÉGICA" na VPS! 