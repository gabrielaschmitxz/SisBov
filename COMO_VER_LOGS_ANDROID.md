# 📱 Como Ver Logs do Android para Diagnosticar Erros

Quando o app fecha sozinho, os logs mostram o erro. Aqui estão várias formas de ver:

## 🔧 Método 1: Usando ADB (Android Debug Bridge)

### No PC (Windows):

1. **Instalar ADB:**
   - Baixe o Platform Tools: https://developer.android.com/studio/releases/platform-tools
   - Extraia para `C:\adb\`
   - Adicione ao PATH do Windows

2. **Habilitar Depuração USB no celular:**
   - Configurações > Sobre o telefone
   - Toque 7 vezes em "Número da versão" (ativa Modo Desenvolvedor)
   - Volte para Configurações > Opções do desenvolvedor
   - Ative "Depuração USB"

3. **Conectar celular e ver logs:**
   ```cmd
   adb logcat | findstr "python"
   ```
   
   Ou ver TODOS os logs:
   ```cmd
   adb logcat > logs.txt
   ```

### No WSL:

```bash
# Instalar ADB
sudo apt install android-tools-adb

# Ver logs do Python/SISBOV
adb logcat | grep -i "python\|sisbov\|kivy"

# Ou salvar em arquivo
adb logcat > ~/android_logs.txt
```

---

## 📱 Método 2: App Log Viewer (Mais Fácil!)

Instale um app de visualização de logs no seu celular:

1. **aLogcat** (Play Store) - GRÁTIS
2. **Log Viewer** (Play Store) - GRÁTIS
3. **Logcat Reader** (Play Store) - GRÁTIS

Depois de instalar:
1. Abra o app
2. Dê permissão de administrador (se pedir)
3. Filtre por "python" ou "sisbov"
4. Tente abrir seu app
5. Veja os erros no Log Viewer

---

## 🔍 Método 3: Via USB + PowerShell (Windows)

```powershell
# Instalar adb se não tiver
# Baixe de: https://developer.android.com/studio/releases/platform-tools

# Conectar celular via USB
# Ativar Depuração USB no celular

# Ver logs
adb logcat | Select-String -Pattern "python|sisbov|error|exception"
```

---

## 🐛 O Que Procurar nos Logs:

Procure por estas palavras-chave:
- `PythonException`
- `Traceback`
- `ImportError`
- `ModuleNotFoundError`
- `ConnectionError`
- `psycopg2`
- `database`
- `FATAL`

---

## 💡 Solução Rápida - Testar Sem Banco de Dados

O erro mais comum é conexão com banco de dados. Para testar, modifique temporariamente o `main_kivy.py`:

```python
def build(self):
    try:
        # COMENTAR temporariamente para testar
        # init_database()
        print("Banco de dados desabilitado para teste")
    except Exception as e:
        print(f"Erro (ignorado): {e}")
    
    # ... resto do código
```

Depois recompile:
```bash
cd ~/sisbov-app
source ~/.buildozer-env/bin/activate
buildozer android debug
```

---

## 📋 Checklist de Problemas Comuns:

- [ ] App fecha imediatamente → Ver logs (erro no import/startup)
- [ ] App abre mas fecha ao usar → Ver logs (erro na execução)
- [ ] Sem internet → Erro de conexão com banco
- [ ] Arquivo .env não incluído → Erro de DATABASE_URL
- [ ] Permissão de Internet negada → Erro de conexão

---

Use o **Método 2 (App Log Viewer)** - é o mais fácil! 📱

