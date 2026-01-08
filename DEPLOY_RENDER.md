# 🚀 Guia de Deploy no Render - SisBov

Este guia fornece um passo a passo completo para fazer o deploy da aplicação SisBov no Render.

## 📋 Pré-requisitos

1. Conta no [Render](https://render.com) (gratuita)
2. Código da aplicação no GitHub, GitLab ou Bitbucket
3. Banco de dados Neon PostgreSQL já configurado (você já tem!)

---

## 🔧 Passo 1: Preparar o Repositório

### 1.1. Verificar arquivos necessários

Certifique-se de que os seguintes arquivos estão no seu repositório:

- ✅ `app_web.py` - Aplicação Flask principal
- ✅ `requirements.txt` - Dependências Python
- ✅ `Procfile` - Comando para iniciar a aplicação
- ✅ `render.yaml` (opcional) - Configuração automática

### 1.2. Fazer commit e push

```bash
git add .
git commit -m "Preparar para deploy no Render"
git push origin main
```

---

## 🗄️ Passo 2: Obter URL do Banco Neon

Como você já usa o banco Neon, você precisa da URL de conexão:

1. Acesse o [Dashboard do Neon](https://console.neon.tech)
2. Selecione seu projeto
3. Vá em **"Connection Details"** ou **"Connection String"**
4. **Copie a Connection String** (URL completa)
   - Formato: `postgresql://usuario:senha@host/database?sslmode=require`
   - Você precisará dessa URL no próximo passo

**💡 Dica**: 
- Se você não tem a URL salva, ela está no arquivo `src/services/database.py` como valor padrão
- **Recomendado**: Use a URL atualizada do dashboard do Neon (pode ter mudado)
- O Neon permite conexões de qualquer IP, então não precisa configurar whitelist

---

## 🌐 Passo 3: Criar Web Service no Render

### 3.1. Criar novo serviço

1. No Dashboard do Render, clique em **"New +"** → **"Web Service"**
2. Conecte seu repositório:
   - Se ainda não conectou, clique em **"Connect account"** e autorize o Render a acessar seu repositório
   - Selecione o repositório do SisBov

### 3.2. Configurar o serviço

Preencha os seguintes campos:

#### Informações Básicas:
- **Name**: `sisbov-app` (ou o nome que preferir)
- **Region**: Escolha qualquer região (o banco Neon está na AWS)
- **Branch**: `main` (ou a branch que você usa)
- **Root Directory**: Deixe em branco (ou `.` se necessário)

#### Build & Deploy:
- **Environment**: `Python 3`
- **Build Command**: 
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**: 
  ```bash
  gunicorn app_web:app
  ```

#### Environment Variables (Variáveis de Ambiente):

Clique em **"Add Environment Variable"** e adicione:

| Chave | Valor | Descrição |
|-------|-------|-----------|
| `SECRET_KEY` | `[Gere uma chave aleatória]` | Chave secreta para sessões Flask |
| `DATABASE_URL` | `[URL do Neon copiada no Passo 2]` | URL completa do Neon PostgreSQL |
| `PORT` | `10000` | Porta (Render define automaticamente, mas pode usar 10000) |
| `FLASK_DEBUG` | `false` | Desabilita debug em produção |
| `PYTHON_VERSION` | `3.11.0` | Versão do Python (opcional) |

**Como gerar SECRET_KEY:**
```python
import secrets
print(secrets.token_hex(32))
```

Ou use este comando no terminal:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

**DATABASE_URL:**
- Cole a URL completa do Neon que você copiou no Passo 2
- Formato: `postgresql://usuario:senha@host/database?sslmode=require&channel_binding=require`
- **IMPORTANTE**: Use a URL do dashboard do Neon (não a do código, pois pode estar desatualizada)

### 3.3. Plano e Deploy

- **Instance Type**: `Free` (para começar)
- Clique em **"Create Web Service"**

---

## ⚙️ Passo 4: Configurações Adicionais (Opcional)

### 4.1. Health Check

No painel do serviço, vá em **"Settings"** → **"Health Check Path"**:
- Deixe em branco ou use `/` (a aplicação já tem rotas protegidas)

### 4.2. Auto-Deploy

Por padrão, o Render faz deploy automático quando você faz push para a branch principal. Isso já está habilitado.

### 4.3. Custom Domain (Domínio Personalizado)

Se quiser usar um domínio próprio:
1. Vá em **"Settings"** → **"Custom Domains"**
2. Adicione seu domínio
3. Configure o DNS conforme as instruções do Render

---

## 🔍 Passo 5: Verificar o Deploy

### 5.1. Acompanhar o build

1. Após criar o serviço, o Render começará automaticamente o build
2. Acompanhe os logs em tempo real na aba **"Logs"**
3. Aguarde o build completar (pode levar 2-5 minutos)

### 5.2. Verificar erros comuns

Se o deploy falhar, verifique:

- ✅ **Build Command**: Está correto? `pip install -r requirements.txt`
- ✅ **Start Command**: Está correto? `gunicorn app_web:app`
- ✅ **DATABASE_URL**: Está configurada corretamente?
- ✅ **SECRET_KEY**: Foi definida?
- ✅ **requirements.txt**: Todas as dependências estão listadas?

### 5.3. Testar a aplicação

1. Após o build completar, acesse a URL fornecida pelo Render (ex: `https://sisbov-app.onrender.com`)
2. Você deve ver a tela de login
3. Faça login com as credenciais padrão:
   - **Usuário**: `admin`
   - **Senha**: `admin123`

---

## 🐛 Passo 6: Resolução de Problemas

### Problema: "Application failed to respond"

**Solução:**
- Verifique se o `Start Command` está correto: `gunicorn app_web:app`
- Verifique os logs para erros específicos
- Certifique-se de que a porta está sendo lida da variável de ambiente `PORT`

### Problema: "Database connection error"

**Solução:**
- Verifique se a `DATABASE_URL` está correta e completa
- O Neon permite conexões de qualquer IP por padrão, então não precisa configurar whitelist
- Certifique-se de que a URL inclui `?sslmode=require` no final
- Verifique se a senha na URL está correta (copie do dashboard do Neon)

### Problema: "Module not found"

**Solução:**
- Verifique se todas as dependências estão no `requirements.txt`
- Certifique-se de que o `Build Command` está instalando as dependências

### Problema: "Secret key not set"

**Solução:**
- Adicione a variável de ambiente `SECRET_KEY` no painel do Render

---

## 📝 Passo 7: Atualizar o Banco de Dados

O banco de dados será inicializado automaticamente na primeira execução, mas você pode verificar:

1. Acesse os logs do serviço
2. Procure por mensagens de inicialização do banco
3. Se houver erros, verifique a conexão com o banco

---

## 🔄 Passo 8: Deploy Contínuo

A partir de agora, sempre que você fizer push para a branch principal:

1. O Render detectará automaticamente as mudanças
2. Fará um novo build
3. Deployará a nova versão

Você pode acompanhar tudo na aba **"Events"** do painel do serviço.

---

## 📊 Monitoramento

### Ver logs em tempo real:
- Acesse o painel do serviço
- Clique na aba **"Logs"**
- Veja logs em tempo real da aplicação

### Métricas:
- Na aba **"Metrics"**, veja uso de CPU, memória, etc.

---

## 💰 Planos e Limitações do Plano Free

O plano gratuito do Render tem algumas limitações:

- ⏱️ **Sleep após inatividade**: O serviço "dorme" após 15 minutos de inatividade
- 🚀 **Primeira requisição lenta**: Após dormir, a primeira requisição pode levar 30-60 segundos
- 💾 **Recursos limitados**: CPU e memória limitados
- 📊 **Logs**: Retidos por 7 dias

**Para produção**, considere fazer upgrade para um plano pago.

---

## ✅ Checklist Final

Antes de considerar o deploy completo, verifique:

- [ ] Build completou com sucesso
- [ ] Aplicação está acessível pela URL do Render
- [ ] Login funciona corretamente
- [ ] Banco de dados está conectado
- [ ] Variáveis de ambiente estão configuradas
- [ ] Logs não mostram erros críticos

---

## 🎉 Pronto!

Sua aplicação SisBov está no ar! 🚀

**URL da aplicação**: `https://seu-servico.onrender.com`

---

## 📞 Suporte

Se encontrar problemas:
1. Verifique os logs no Render
2. Verifique a documentação do Render: https://render.com/docs
3. Verifique se todas as configurações estão corretas

---

**Última atualização**: 2024
