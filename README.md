# The Move - Servidor Local

Este é o código fonte do **The Move**. Siga as instruções abaixo para rodar o site completo no seu computador.

## Pré-requisitos
1. Ter o [Python](https://www.python.org/downloads/) instalado no computador (marcar a caixinha "Add python.exe to PATH" durante a instalação).
2. Ter o [Git](https://git-scm.com/downloads) instalado para baixar o código.

## Passo a Passo para Rodar

### 1. Baixar o Código
Abra o terminal (Prompt de Comando ou PowerShell) e rode:
```bash
git clone https://github.com/joaopedrokruger77/TheMove_Site.git
cd TheMove_Site
```

### 2. Instalar as Bibliotecas Necessárias
Ainda no terminal, rode o comando abaixo para instalar tudo que o site precisa (Flask, Supabase, Google Gemini, etc):
```bash
pip install -r requirements.txt
```

### 3. Configurar as Chaves de Acesso
O projeto precisa se conectar ao Banco de Dados (Supabase) e à Inteligência Artificial (Gemini).
1. Na pasta do projeto, crie um arquivo chamado **`.env`** (exatamente assim, com o ponto no começo e sem extensão).
2. Abra esse arquivo no Bloco de Notas ou VS Code e cole o seguinte conteúdo, pedindo as chaves secretas para o João Pedro:

```env
SUPABASE_URL=URL_DO_SUPABASE_AQUI
SUPABASE_ANON_KEY=CHAVE_DO_SUPABASE_AQUI
GEMINI_API_KEY=CHAVE_DO_GEMINI_AQUI
```
*(Substitua os valores pelas chaves reais que o João vai te passar!)*

### 4. Rodar o Site
No terminal, basta rodar o servidor:
```bash
python app.py
```

### 5. Acessar
Abra o seu navegador de internet e digite:
👉 **http://127.0.0.1:5000**

Pronto! O site completo do The Move vai estar rodando no seu computador!
Lembre-se que a tela preta do terminal precisa ficar aberta para o site continuar no ar. Se quiser desligar, clique no terminal e aperte `CTRL + C`.
