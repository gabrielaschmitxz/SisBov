# 🏥 Health Check - Configuração para UptimeRobot

## ✅ Endpoint de Health Check Criado

Foi criado um endpoint de health check que verifica se a aplicação e o banco de dados estão funcionando corretamente.

### URLs Disponíveis

Você pode usar qualquer uma dessas URLs no UptimeRobot:

- `https://seu-app.onrender.com/health`
- `https://seu-app.onrender.com/healthz`
- `https://seu-app.onrender.com/ping`

**Recomendado**: Use `/health` (mais comum)

### Resposta do Endpoint

#### ✅ Quando está saudável (Status 200):
```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

#### ❌ Quando está com problemas (Status 503):
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "Mensagem de erro",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

## 🔧 Como Configurar no UptimeRobot

### Passo 1: Criar Conta no UptimeRobot

1. Acesse [UptimeRobot](https://uptimerobot.com)
2. Crie uma conta gratuita (até 50 monitores)
3. Faça login

### Passo 2: Adicionar Novo Monitor

1. No dashboard, clique em **"+ Add New Monitor"**
2. Configure o monitor:

#### Tipo de Monitor:
- Selecione **"HTTP(s)"**

#### Configurações Básicas:
- **Friendly Name**: `SisBov - Aplicação Web`
- **URL (or IP)**: `https://seu-app.onrender.com/health`
  - Substitua `seu-app` pelo nome do seu serviço no Render

#### Configurações Avançadas:
- **Monitoring Interval**: `5 minutes` (padrão gratuito)
- **Alert Contacts**: Selecione seu email ou configure notificações

#### Keyword Monitoring (Opcional):
- **Keyword**: `"status":"healthy"`
- **Alert If**: `Does not exist`
- Isso garante que a resposta JSON está correta

### Passo 3: Salvar e Testar

1. Clique em **"Create Monitor"**
2. Aguarde alguns minutos
3. O status deve aparecer como **"Up"** (verde) se tudo estiver funcionando

## 📊 O que o Health Check Verifica

O endpoint `/health` verifica:

1. ✅ **Aplicação Flask está rodando**
   - Se o servidor responde à requisição

2. ✅ **Conexão com o banco de dados**
   - Tenta conectar ao PostgreSQL (Neon)
   - Executa uma query simples (`SELECT 1`)
   - Se falhar, retorna status 503

3. ✅ **Timestamp da verificação**
   - Inclui quando a verificação foi feita

## 🎯 Configurações Recomendadas

### Intervalo de Monitoramento

- **Plano Gratuito**: 5 minutos (máximo)
- **Plano Pago**: 1 minuto (recomendado para produção)

### Alertas

Configure alertas para:
- ✅ Quando o serviço volta a funcionar (Up)
- ❌ Quando o serviço para de funcionar (Down)
- ⚠️ Quando há timeout ou erro de conexão

### Contatos de Alerta

Adicione:
- 📧 Email pessoal
- 📱 SMS (se disponível no plano)
- 🔔 Notificações push (app móvel)
- 💬 Slack/Discord (planos pagos)

## 🐛 Troubleshooting

### Problema: Monitor sempre mostra "Down"

**Possíveis causas:**
1. URL incorreta
   - Verifique se a URL está correta
   - Teste manualmente no navegador: `https://seu-app.onrender.com/health`

2. Aplicação não está rodando
   - Verifique os logs no Render
   - Verifique se o deploy foi bem-sucedido

3. Timeout muito curto
   - No plano free do Render, a primeira requisição após "dormir" pode levar 30-60 segundos
   - Configure timeout de 90 segundos no UptimeRobot

### Problema: Monitor mostra "Up" mas aplicação não funciona

**Solução:**
- O health check verifica apenas a conexão básica
- Se houver problemas específicos, eles aparecerão nos logs
- Considere adicionar verificações mais específicas se necessário

### Problema: Muitos falsos positivos

**Solução:**
- Aumente o intervalo de monitoramento
- Configure alertas apenas para múltiplas falhas consecutivas
- Verifique se o Render não está "dormindo" (plano free)

## 📈 Monitoramento Avançado

### Adicionar Verificações Customizadas

Se quiser verificar mais coisas, você pode modificar o endpoint `/health` em `app_web.py`:

```python
@app.route('/health')
def health_check():
    checks = {
        'app': True,
        'database': False,
        'cache': False  # exemplo
    }
    
    # Verificar banco
    try:
        conn = get_connection()
        # ... teste de conexão
        checks['database'] = True
    except:
        pass
    
    # Se todos os checks passarem
    if all(checks.values()):
        return jsonify({'status': 'healthy', **checks}), 200
    else:
        return jsonify({'status': 'unhealthy', **checks}), 503
```

## 🔒 Segurança

### Endpoint Público

O endpoint `/health` é **público** e não requer autenticação. Isso é intencional para permitir monitoramento externo.

**Informações expostas:**
- Status da aplicação
- Status da conexão com banco
- Timestamp

**Informações NÃO expostas:**
- Dados sensíveis
- Credenciais
- Informações de usuários

Se quiser proteger o endpoint, você pode:
1. Adicionar autenticação básica
2. Usar um token de autenticação
3. Restringir por IP (não recomendado para UptimeRobot)

## 📝 Exemplo de Resposta Real

### Resposta de Sucesso:
```bash
curl https://seu-app.onrender.com/health
```

```json
{
  "status": "healthy",
  "database": "connected",
  "timestamp": "2024-01-15T14:23:45.678901"
}
```

### Resposta de Erro:
```json
{
  "status": "unhealthy",
  "database": "disconnected",
  "error": "connection to server at \"ep-broad-sun-ahovkkf5-pooler.c-3.us-east-1.aws.neon.tech\" (54.xxx.xxx.xxx), port 5432 failed: Connection timed out",
  "timestamp": "2024-01-15T14:23:45.678901"
}
```

## ✅ Checklist de Configuração

- [ ] Endpoint `/health` está funcionando
- [ ] Monitor criado no UptimeRobot
- [ ] URL configurada corretamente
- [ ] Alertas configurados
- [ ] Teste manual realizado
- [ ] Monitor mostra status "Up"
- [ ] Notificações de teste recebidas

## 🎉 Pronto!

Agora você tem monitoramento 24/7 da sua aplicação SisBov!

O UptimeRobot irá:
- ✅ Verificar a aplicação a cada 5 minutos
- ✅ Enviar alertas quando houver problemas
- ✅ Manter histórico de uptime
- ✅ Fornecer estatísticas de disponibilidade

---

**Última atualização**: 2024
**Endpoint**: `/health`, `/healthz`, `/ping`
