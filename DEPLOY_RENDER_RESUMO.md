# 🚀 Deploy no Render - Resumo Rápido

## Passos Essenciais

### 1️⃣ Preparar Repositório
```bash
git add .
git commit -m "Preparar para deploy"
git push origin main
```

### 2️⃣ Criar Banco de Dados no Render
- Dashboard → New + → PostgreSQL
- Name: `sisbov-db`
- Plan: Free
- **Copiar Internal Database URL**

### 3️⃣ Criar Web Service
- Dashboard → New + → Web Service
- Conectar repositório
- Configurar:
  - **Build Command**: `pip install -r requirements.txt`
  - **Start Command**: `gunicorn app_web:app`

### 4️⃣ Variáveis de Ambiente
Adicionar no painel do serviço:

| Variável | Valor |
|----------|-------|
| `SECRET_KEY` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `DATABASE_URL` | `[Internal Database URL do passo 2]` |
| `PORT` | `10000` |
| `FLASK_DEBUG` | `false` |

### 5️⃣ Deploy
- Clicar em "Create Web Service"
- Aguardar build (2-5 min)
- Acessar URL fornecida

## ✅ Pronto!

Acesse: `https://seu-servico.onrender.com`

**Login padrão:**
- Usuário: `admin`
- Senha: `admin123`

---
📖 Para instruções detalhadas, veja `DEPLOY_RENDER.md`
