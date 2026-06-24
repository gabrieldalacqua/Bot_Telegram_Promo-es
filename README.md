# 🤖 Bot Telegram – Gerenciador Multi-Bot

Ferramenta desktop para gerenciar e automatizar o envio de links de afiliados (Shopee, Mercado Livre, Amazon, AliExpress) para canais do Telegram, com suporte a múltiplos bots simultâneos, envio aleatório e horários configuráveis.

---

## ✨ Funcionalidades

- **Multi-bot**: cadastre quantos bots quiser, cada um com canal e lista de links próprios
- **Painel de controle**: selecione quais bots rodar com um simples checkmark
- **Envio aleatório**: os links são embaralhados a cada início, evitando padrão de envio
- **Sem repetição**: cada link é enviado apenas uma vez por sessão
- **Horário configurável**: define janela de envio (ex: 9h–23h) por bot
- **Intervalo ajustável**: de 1 a N minutos entre cada postagem
- **Notificação automática**: ao esgotar os links, avisa o canal e o sistema
- **Importação em massa**: suporte a `.txt` e `.csv` com separador `|||` ou vírgula
- **Interface gráfica**: 100% visual, sem linha de comando

---

## 📦 Instalação

### Pré-requisitos
- Python 3.10 ou superior
- pip atualizado

### 1. Clone ou baixe o projeto
```bash
git clone https://github.com/seu-usuario/bot-telegram-afiliados.git
cd bot-telegram-afiliados
```

### 2. Instale as dependências
```bash
pip install python-telegram-bot pytz
```

### 3. Execute
```bash
python bot_telegram.py
```

---

## 🚀 Como usar

### Passo 1 – Criar seu bot no Telegram
1. Abra o Telegram e pesquise por **@BotFather**
2. Envie `/newbot` e siga as instruções
3. Copie o **token** gerado (ex: `123456:ABC-DEF1234...`)
4. Adicione o bot como **administrador** do seu canal

### Passo 2 – Cadastrar um bot no sistema
1. Vá para a aba **⚙️ Bots**
2. Preencha: Nome, Token, Chat ID do canal (ex: `@meucanal`), horários e intervalo
3. Clique em **💾 Salvar bot**

### Passo 3 – Adicionar links
1. Vá para a aba **🔗 Links**
2. Selecione o bot no combo superior
3. Adicione manualmente **ou** importe um arquivo `.txt`/`.csv`

### Passo 4 – Iniciar
1. Vá para a aba **🏠 Painel**
2. Marque os bots que deseja ativar
3. Clique em **✅ Confirmar seleção**

---

## 📄 Formato de importação

### TXT com separador `|||` (recomendado)
```
link|||texto|||preco
https://s.shopee.com.br/abc123|||Tênis masculino confortável|||R$89,99
https://www.mercadolivre.com.br/xyz|||Jaqueta impermeável|||R$129,90
```

### CSV (compatível com Excel e Google Sheets)
```
link,texto,preco
https://s.shopee.com.br/abc123,Tênis masculino confortável,R$89,99
https://www.mercadolivre.com.br/xyz,Jaqueta impermeável,R$129,90
```

> ⚠️ **Atenção com CSV**: se o texto ou preço contiver vírgula, coloque entre aspas: `"R$1,99"`

---

## 💬 Formato da mensagem enviada

```
🔗 https://s.shopee.com.br/abc123

🔥 Oferta Imperdível! Tênis masculino confortável

Por Apenas: R$89,99
```

---

## 🗂️ Estrutura de arquivos

```
📁 bot-telegram-afiliados/
├── bot_telegram.py        ← Código principal
├── bots.json              ← Configurações de todos os bots (gerado automaticamente)
├── links_bot_001.json     ← Links do Bot 1 (gerado automaticamente)
├── links_bot_002.json     ← Links do Bot 2 (gerado automaticamente)
└── README.md
```

---

## 🛠️ Tecnologias utilizadas

| Tecnologia | Uso |
|---|---|
| Python 3.10+ | Linguagem principal |
| python-telegram-bot | Integração com a API do Telegram |
| Tkinter | Interface gráfica desktop |
| asyncio + threading | Múltiplos bots em paralelo |
| pytz | Controle de fuso horário (America/Sao_Paulo) |
| json / csv | Persistência e importação de dados |

---

## ⚙️ Configurações por bot

| Campo | Descrição | Exemplo |
|---|---|---|
| Nome | Identificação interna do bot | `Bot Shopee` |
| Token | Chave da API do Telegram | `123456:ABC...` |
| Chat ID | Canal ou grupo de destino | `@meucanal` |
| Hora início | Horário de início dos envios | `9` |
| Hora fim | Horário de encerramento | `23` |
| Intervalo | Minutos entre cada envio | `10` |

---

## 📌 Observações

- O sistema **não repete links** durante a sessão — cada link é enviado uma única vez
- Os links são **embaralhados aleatoriamente** a cada nova sessão (ideal para misturar Shopee, ML, Amazon etc.)
- Quando os links acabam, o canal recebe: *"✅ Por hoje terminamos! Amanhã voltaremos a partir das 9:00 🌅"*
- O arquivo `bots.json` e os arquivos `links_*.json` são gerados automaticamente na mesma pasta do script

---

## 📝 Licença

PolyForm Noncommercial License 1.0.0

---

*Desenvolvido com Python + Tkinter + python-telegram-bot*
