# 🤖 Telegram Bot – Multi-Bot Manager

A desktop application designed to manage and automate the posting of affiliate links (Shopee, Mercado Livre, Amazon, AliExpress) to Telegram channels, with support for multiple bots running simultaneously, randomized posting, and customizable schedules.

---

## ✨ Features

* **Multi-bot support**: register as many bots as you want, each with its own channel and link database
* **Control panel**: choose which bots should run with a simple checkbox
* **Randomized posting**: links are shuffled at the beginning of each session to avoid posting patterns
* **No duplicates**: each link is sent only once per session
* **Custom schedules**: define posting windows (e.g., 9 AM–11 PM) for each bot
* **Adjustable intervals**: configure posting frequency from 1 to N minutes
* **Automatic notifications**: alerts both the channel and system when all links have been sent
* **Bulk import**: supports `.txt` and `.csv` files using `|||` or comma separators
* **Graphical interface**: fully visual, no command-line usage required

---

## 📦 Installation

### Requirements

* Python 3.10 or later
* Updated pip version

### 1. Clone or download the project

```bash
git clone https://github.com/your-username/telegram-affiliate-bot.git
cd telegram-affiliate-bot
```

### 2. Install dependencies

```bash
pip install python-telegram-bot pytz
```

### 3. Run the application

```bash
python bot_telegram.py
```

---

## 🚀 How to Use

### Step 1 – Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot` and follow the instructions
3. Copy the generated **token** (e.g., `123456:ABC-DEF1234...`)
4. Add the bot as an **administrator** to your channel

### Step 2 – Register a Bot in the System

1. Open the **⚙️ Bots** tab
2. Fill in: Name, Token, Channel Chat ID (e.g., `@mychannel`), schedule, and posting interval
3. Click **💾 Save Bot**

### Step 3 – Add Links

1. Open the **🔗 Links** tab
2. Select the desired bot from the dropdown menu
3. Add links manually **or** import a `.txt` / `.csv` file

### Step 4 – Start the Bots

1. Open the **🏠 Dashboard** tab
2. Select the bots you want to activate
3. Click **✅ Confirm Selection**

---

## 📄 Import File Format

### TXT using `|||` separator (recommended)

```txt
link|||text|||price
https://s.shopee.com.br/abc123|||Comfortable men's sneakers|||R$89.99
https://www.mercadolivre.com.br/xyz|||Waterproof jacket|||R$129.90
```

### CSV (Excel and Google Sheets compatible)

```csv
link,text,price
https://s.shopee.com.br/abc123,Comfortable men's sneakers,R$89.99
https://www.mercadolivre.com.br/xyz,Waterproof jacket,R$129.90
```

> ⚠️ **CSV Warning:** If the text or price contains commas, wrap the value in quotation marks, such as `"R$1,999.99"`.

---

## 💬 Message Format

```txt
🔗 https://s.shopee.com.br/abc123

🔥 Unmissable Deal! Comfortable men's sneakers

Only: R$89.99
```

---

## 🗂️ Project Structure

```txt
📁 telegram-affiliate-bot/
├── bot_telegram.py        ← Main application file
├── bots.json              ← All bot configurations (auto-generated)
├── links_bot_001.json     ← Bot 1 links (auto-generated)
├── links_bot_002.json     ← Bot 2 links (auto-generated)
└── README.md
```

---

## 🛠️ Technologies Used

| Technology          | Purpose                                 |
| ------------------- | --------------------------------------- |
| Python 3.10+        | Main programming language               |
| python-telegram-bot | Telegram API integration                |
| Tkinter             | Desktop graphical interface             |
| asyncio + threading | Parallel execution of multiple bots     |
| pytz                | Timezone management (America/Sao_Paulo) |
| json / csv          | Data persistence and import/export      |

---

## ⚙️ Per-Bot Configuration

| Field      | Description                  | Example         |
| ---------- | ---------------------------- | --------------- |
| Name       | Internal bot identifier      | `Shopee Bot`    |
| Token      | Telegram API key             | `123456:ABC...` |
| Chat ID    | Destination channel or group | `@mychannel`    |
| Start Time | Posting start hour           | `9`             |
| End Time   | Posting end hour             | `23`            |
| Interval   | Minutes between posts        | `10`            |

---

## 📌 Notes

* The system **does not repeat links** during a session — each link is posted only once.
* Links are **randomly shuffled** every time a new session starts (ideal for mixing Shopee, Mercado Livre, Amazon, etc.).
* When all links have been sent, the channel receives the following message:

> ✅ That's all for today! We'll be back tomorrow starting at 9:00 AM 🌅

* The `bots.json` file and all `links_*.json` files are generated automatically in the same directory as the application.

---

## 📝 License

PolyForm Noncommercial License 1.0.0

---

*Developed with Python + Tkinter + python-telegram-bot*
