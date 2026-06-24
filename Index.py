# ══════════════════════════════════════════════════════════════════════════════
#  BOT TELEGRAM – GERENCIADOR DE LINKS COM INTERFACE GRÁFICA
#  Autor: PrensaHidrualica GitHub: https://github.com/gabrieldalacqua
#  Feito com Python 3.10+ , python-telegram-bot v20+ (API Telegram atualizada) e utilizando o claude ai para organizar e otimizar o código.
#
#  DEPENDÊNCIAS (instalar uma vez):
#      pip install python-telegram-bot pytz
#
#  ARQUIVOS GERADOS AUTOMATICAMENTE ao rodar:
#      config.json  → Token, chat_id, horários e intervalo de envio
#      links.json   → Lista de produtos (link + texto + preço) salvos
#
#  FORMATO DO CSV/TXT PARA IMPORTAÇÃO (3 colunas separadas por |||):
#      https://link.com|||Nome do produto|||R$99,90
#      (cabeçalho "link|||texto|||preco" é ignorado automaticamente)
# ══════════════════════════════════════════════════════════════════════════════

import csv
import json
import random
import asyncio
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, time
import pytz
from telegram.ext import ApplicationBuilder, ContextTypes
 
# ─── Fuso horário ─────────────────────────────────────────────────────────────
FUSO = pytz.timezone("America/Sao_Paulo")
 
# ─── Arquivo que guarda todos os bots cadastrados ─────────────────────────────
BOTS_FILE = "bots.json"
 
# ─── Estado global: dicionário de instâncias ativas { bot_id: {...} } ─────────
# Cada entrada contém: thread, loop, app_telegram, links_ordem, link_atual, rodando
instancias_ativas: dict = {}
 
# ─── Referência global ao widget de log (criado na interface) ─────────────────
log_widget = None
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  BLOCO 1 – PERSISTÊNCIA DE BOTS E LINKS
# ══════════════════════════════════════════════════════════════════════════════
 
def carregar_bots() -> list:
    """
    Lê bots.json e retorna a lista de bots cadastrados.
    Cada bot é um dict com: id, nome, token, chat_id, hora_inicio, hora_fim, intervalo.
    Retorna lista vazia se o arquivo não existir.
    """
    try:
        with open(BOTS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
 
def salvar_bots(lista: list):
    """Grava a lista de bots no bots.json."""
    with open(BOTS_FILE, "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)
 
def arquivo_links(bot_id: str) -> str:
    """Retorna o caminho do arquivo de links de um bot específico."""
    return f"links_{bot_id}.json"
 
def carregar_links(bot_id: str) -> list:
    """
    Lê os links do bot indicado por bot_id.
    Cada item é um dict: {"link": "...", "texto": "...", "preco": "..."}
    """
    try:
        with open(arquivo_links(bot_id), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []
 
def salvar_links(bot_id: str, lista: list):
    """Grava a lista de links do bot no arquivo links_<bot_id>.json."""
    with open(arquivo_links(bot_id), "w", encoding="utf-8") as f:
        json.dump(lista, f, indent=2, ensure_ascii=False)
 
def novo_id(bots: list) -> str:
    """Gera um ID único sequencial para um novo bot (ex: 'bot_004')."""
    if not bots:
        return "bot_001"
    ids_numericos = []
    for b in bots:
        try:
            ids_numericos.append(int(b["id"].split("_")[1]))
        except Exception:
            pass
    proximo = max(ids_numericos, default=0) + 1
    return f"bot_{proximo:03d}"
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  BLOCO 2 – LÓGICA DO BOT TELEGRAM (envio de mensagens)
# ══════════════════════════════════════════════════════════════════════════════
 
def log(msg: str):
    """Escreve uma linha com timestamp no painel de Log da interface."""
    if log_widget:
        log_widget.configure(state="normal")
        log_widget.insert("end", f"[{datetime.now(FUSO).strftime('%H:%M:%S')}] {msg}\n")
        log_widget.see("end")
        log_widget.configure(state="disabled")
 
def fazer_callback_envio(bot_id: str, cfg_bot: dict):
    """
    Retorna uma função assíncrona de envio específica para um bot.
    Usamos closure para capturar bot_id e cfg_bot sem variável global por bot.
    """
    async def enviar_produto(context: ContextTypes.DEFAULT_TYPE):
        inst = instancias_ativas.get(bot_id)
        if not inst:
            return
 
        # ── Verifica horário ─────────────────────────────────────────────────
        agora = datetime.now(FUSO).time()
        h_ini = time(int(cfg_bot["hora_inicio"]), 0)
        h_fim = time(int(cfg_bot["hora_fim"]),    0)
 
        if not (h_ini <= agora <= h_fim):
            log(f"[{cfg_bot['nome']}] ⏸ Fora do horário — aguardando...")
            return
 
        links_ordem = inst["links_ordem"]
 
        if not links_ordem:
            log(f"[{cfg_bot['nome']}] ⚠️ Nenhum link cadastrado!")
            return
 
        link_atual = inst["link_atual"]
 
        # ── Todos os links do dia foram enviados ──────────────────────────────
        if link_atual >= len(links_ordem):
            aviso = "✅ Por hoje terminamos! Amanhã voltaremos a partir das 9:00 🌅"
            await context.bot.send_message(chat_id=cfg_bot["chat_id"], text=aviso)
            log(f"[{cfg_bot['nome']}] 🔔 Todos os links enviados hoje!")
            messagebox.showinfo(
                f"Bot {cfg_bot['nome']} – Esgotado",
                f"Todos os links do bot '{cfg_bot['nome']}' foram enviados hoje!"
            )
            context.job.schedule_removal()
            inst["rodando"] = False
            return
 
        # ── Monta e envia a mensagem ──────────────────────────────────────────
        item  = links_ordem[link_atual]
        link  = item.get("link",  "").strip()
        texto = item.get("texto", "").strip().strip('"').strip("'")
        preco = item.get("preco", "").strip().strip('"').strip("'")
 
        mensagem = (
            f"🔗 {link}\n\n"
            f"🔥 Oferta Imperdível! {texto}\n\n"
            f"<b>Por Apenas: {preco}</b>"
        )
 
        await context.bot.send_message(
            chat_id=cfg_bot["chat_id"],
            text=mensagem,
            parse_mode="HTML"
        )
        log(f"[{cfg_bot['nome']}] ✅ {link_atual + 1}/{len(links_ordem)}: {link[:50]}...")
        inst["link_atual"] += 1
 
    return enviar_produto
 
def iniciar_bot_em_thread(bot_id: str, cfg_bot: dict, links_embaralhados: list):
    """
    Cria um event loop próprio para o bot e o mantém rodando até inst['rodando'] = False.
    Cada bot roda em sua própria thread para não bloquear a interface nem os outros bots.
    """
    async def _run():
        app = ApplicationBuilder().token(cfg_bot["token"]).build()
        instancias_ativas[bot_id]["app"] = app
 
        intervalo = int(cfg_bot["intervalo"]) * 60  # minutos → segundos
        callback  = fazer_callback_envio(bot_id, cfg_bot)
        app.job_queue.run_repeating(callback, interval=intervalo, first=5)
 
        log(f"[{cfg_bot['nome']}] 🤖 Iniciado! Canal: {cfg_bot['chat_id']} | "
            f"Intervalo: {cfg_bot['intervalo']}min | Links: {len(links_embaralhados)}")
 
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
 
        # Mantém o bot vivo enquanto inst['rodando'] for True
        while instancias_ativas.get(bot_id, {}).get("rodando", False):
            await asyncio.sleep(1)
 
        await app.updater.stop()
        await app.stop()
        await app.shutdown()
        log(f"[{cfg_bot['nome']}] 🛑 Encerrado.")
 
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(_run())
 
 
# ══════════════════════════════════════════════════════════════════════════════
#  BLOCO 3 – INTERFACE GRÁFICA
# ══════════════════════════════════════════════════════════════════════════════
 
def criar_interface():
    global log_widget
 
    # ── Paleta e estilos ──────────────────────────────────────────────────────
    AZUL     = "#0f3460"
    ROXO     = "#533483"
    VERDE    = "#00b894"
    BRANCO   = "#e0e0e0"
    CINZA    = "#2d2d44"
    VERMELHO = "#e74c3c"
    AMARELO  = "#f39c12"
    FUNDO    = "#1a1a2e"
    FONTE    = ("Segoe UI", 10)
    FONTE_B  = ("Segoe UI", 10, "bold")
    FONTE_G  = ("Segoe UI", 12, "bold")
 
    # ── Janela principal ──────────────────────────────────────────────────────
    janela = tk.Tk()
    janela.title("🤖 Bot Telegram – Gerenciador Multi-Bot")
    janela.geometry("960x700")
    janela.configure(bg=FUNDO)
    janela.resizable(True, True)
 
    # ── Helpers ───────────────────────────────────────────────────────────────
    def lbl(parent, texto, bg=CINZA, fg=BRANCO, fonte=FONTE, **kw):
        return tk.Label(parent, text=texto, bg=bg, fg=fg, font=fonte, **kw)
 
    def btn(parent, texto, cor, cmd, largura=None):
        kw = {"text": texto, "bg": cor, "fg": "white", "font": FONTE_B,
              "relief": "flat", "padx": 12, "pady": 6, "cursor": "hand2", "command": cmd}
        if largura:
            kw["width"] = largura
        return tk.Button(parent, **kw)
 
    def entry(parent, width=40):
        return tk.Entry(parent, width=width, bg="#0d0d1a", fg=BRANCO,
                        insertbackground=BRANCO, font=FONTE, relief="flat", bd=4)
 
    # ── Notebook de abas ──────────────────────────────────────────────────────
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TNotebook",     background=FUNDO, borderwidth=0)
    style.configure("TNotebook.Tab", background=AZUL, foreground=BRANCO,
                    padding=[14, 6], font=FONTE_B)
    style.map("TNotebook.Tab",       background=[("selected", ROXO)])
 
    nb = ttk.Notebook(janela)
    nb.pack(fill="both", expand=True, padx=10, pady=10)
 
    def aba(titulo):
        f = tk.Frame(nb, bg=CINZA)
        nb.add(f, text=titulo)
        return f
 
 
    # ╔══════════════════════════════════════════════════════╗
    # ║  ABA 1 – PAINEL DE BOTS (selecionar e iniciar)      ║
    # ╚══════════════════════════════════════════════════════╝
    aba_painel = aba("🏠  Painel")
 
    lbl(aba_painel, "Selecione os bots para rodar:", fonte=FONTE_G,
        bg=CINZA).pack(anchor="w", padx=16, pady=(14, 6))
 
    # Frame com scroll para a lista de bots
    fr_scroll = tk.Frame(aba_painel, bg=CINZA)
    fr_scroll.pack(fill="both", expand=True, padx=16, pady=4)
 
    canvas_bots = tk.Canvas(fr_scroll, bg=CINZA, highlightthickness=0)
    sb_bots     = tk.Scrollbar(fr_scroll, orient="vertical", command=canvas_bots.yview)
    fr_bots_inner = tk.Frame(canvas_bots, bg=CINZA)
 
    fr_bots_inner.bind(
        "<Configure>",
        lambda e: canvas_bots.configure(scrollregion=canvas_bots.bbox("all"))
    )
    canvas_bots.create_window((0, 0), window=fr_bots_inner, anchor="nw")
    canvas_bots.configure(yscrollcommand=sb_bots.set)
 
    canvas_bots.pack(side="left",  fill="both", expand=True)
    sb_bots.pack(side="right", fill="y")
 
    # Dicionário: bot_id → BooleanVar (checkmark de seleção)
    checks_bots: dict = {}
 
    def renderizar_painel():
        """
        Reconstrói a lista de cards de bots no painel.
        Chamado sempre que a lista de bots muda (adicionar, remover, editar).
        """
        for widget in fr_bots_inner.winfo_children():
            widget.destroy()
        checks_bots.clear()
 
        bots = carregar_bots()
        if not bots:
            lbl(fr_bots_inner, "Nenhum bot cadastrado. Clique em '➕ Adicionar Bot'.",
                fg="#888").pack(pady=30)
            return
 
        for bot in bots:
            bid  = bot["id"]
            nome = bot["nome"]
            ativo = instancias_ativas.get(bid, {}).get("rodando", False)
 
            # Card do bot
            fr_card = tk.Frame(fr_bots_inner, bg="#1e1e35", pady=10, padx=14,
                               highlightbackground=VERDE if ativo else AZUL,
                               highlightthickness=2)
            fr_card.pack(fill="x", pady=5, padx=4)
 
            # Coluna esquerda: checkbox + nome + info
            fr_info = tk.Frame(fr_card, bg="#1e1e35")
            fr_info.pack(side="left", fill="x", expand=True)
 
            var = tk.BooleanVar(value=ativo)
            checks_bots[bid] = var
 
            tk.Checkbutton(
                fr_info, variable=var,
                bg="#1e1e35", fg=BRANCO, selectcolor="#0d0d1a",
                activebackground="#1e1e35", font=FONTE_B,
                text=f"  {nome}",
                cursor="hand2"
            ).pack(side="left")
 
            status_txt = "● Rodando" if ativo else "○ Parado"
            status_cor = VERDE      if ativo else "#888"
            lbl(fr_info, status_txt, bg="#1e1e35", fg=status_cor).pack(side="left", padx=10)
 
            n_links = len(carregar_links(bid))
            lbl(fr_info, f"📦 {n_links} links  |  ⏱ {bot.get('intervalo','10')}min  |  "
                         f"🕐 {bot.get('hora_inicio','9')}h–{bot.get('hora_fim','23')}h",
                bg="#1e1e35", fg="#aaa").pack(side="left", padx=6)
 
            # Coluna direita: botões editar e remover
            fr_acoes_card = tk.Frame(fr_card, bg="#1e1e35")
            fr_acoes_card.pack(side="right")
 
            btn(fr_acoes_card, "✏️", AZUL,
                lambda b=bid: abrir_edicao(b), largura=3).pack(side="left", padx=3)
            btn(fr_acoes_card, "🗑️", VERMELHO,
                lambda b=bid: remover_bot(b), largura=3).pack(side="left", padx=3)
 
    def remover_bot(bot_id: str):
        """Remove o bot da lista após confirmação. Para o bot se estiver rodando."""
        bots = carregar_bots()
        bot  = next((b for b in bots if b["id"] == bot_id), None)
        if not bot:
            return
        if not messagebox.askyesno("Remover bot",
                                   f"Deseja remover o bot '{bot['nome']}'?\n"
                                   "Os links salvos deste bot também serão perdidos."):
            return
        # Para o bot se estiver ativo
        if bot_id in instancias_ativas:
            instancias_ativas[bot_id]["rodando"] = False
        bots = [b for b in bots if b["id"] != bot_id]
        salvar_bots(bots)
        renderizar_painel()
        log(f"🗑️ Bot '{bot['nome']}' removido.")
 
    # Botões do painel
    fr_painel_btns = tk.Frame(aba_painel, bg=CINZA)
    fr_painel_btns.pack(fill="x", padx=16, pady=10)
 
    def confirmar_selecao():
        """
        Inicia os bots marcados e para os desmarcados.
        Cada bot roda em sua própria thread com seu próprio event loop.
        """
        bots = carregar_bots()
        for bot in bots:
            bid   = bot["id"]
            rodar = checks_bots.get(bid, tk.BooleanVar(value=False)).get()
            ativo = instancias_ativas.get(bid, {}).get("rodando", False)
 
            if rodar and not ativo:
                # ── Iniciar este bot ─────────────────────────────────────────
                if not bot.get("token"):
                    messagebox.showerror("Erro", f"Bot '{bot['nome']}' sem token configurado!")
                    continue
                links = carregar_links(bid)
                if not links:
                    messagebox.showwarning("Atenção",
                                           f"Bot '{bot['nome']}' não tem links cadastrados!")
                    continue
                embaralhados = list(links)
                random.shuffle(embaralhados)
 
                instancias_ativas[bid] = {
                    "rodando":     True,
                    "links_ordem": embaralhados,
                    "link_atual":  0,
                    "app":         None,
                }
                t = threading.Thread(
                    target=iniciar_bot_em_thread,
                    args=(bid, bot, embaralhados),
                    daemon=True
                )
                t.start()
                log(f"▶ Bot '{bot['nome']}' iniciado com {len(embaralhados)} links embaralhados.")
 
            elif not rodar and ativo:
                # ── Parar este bot ───────────────────────────────────────────
                instancias_ativas[bid]["rodando"] = False
                log(f"⏹ Bot '{bot['nome']}' sendo encerrado...")
 
        renderizar_painel()
 
    btn(fr_painel_btns, "✅ Confirmar seleção", VERDE, confirmar_selecao).pack(side="left", padx=4)
    btn(fr_painel_btns, "🔄 Atualizar painel",  AZUL,  renderizar_painel).pack(side="left", padx=4)
    btn(fr_painel_btns, "⏹ Parar todos",       VERMELHO,
        lambda: [instancias_ativas.update(
                     {bid: {**inst, "rodando": False}}
                 ) for bid, inst in instancias_ativas.items()] or renderizar_painel()
        ).pack(side="left", padx=4)
 
 
    # ╔══════════════════════════════════════════════════════╗
    # ║  ABA 2 – CADASTRO E EDIÇÃO DE BOTS                  ║
    # ╚══════════════════════════════════════════════════════╝
    aba_cfg = aba("⚙️  Bots")
 
    lbl(aba_cfg, "Bots cadastrados:", fonte=FONTE_G, bg=CINZA).pack(
        anchor="w", padx=16, pady=(14, 4))
 
    # Lista de bots cadastrados (simplificada, com botão editar)
    fr_lista_bots = tk.Frame(aba_cfg, bg=CINZA)
    fr_lista_bots.pack(fill="x", padx=16)
 
    lbox_bots = tk.Listbox(fr_lista_bots, bg="#0d0d1a", fg=BRANCO,
                           font=("Consolas", 10), selectbackground=ROXO,
                           relief="flat", bd=0, height=6, activestyle="none")
    lbox_bots.pack(fill="x")
 
    def atualizar_lbox_bots():
        lbox_bots.delete(0, "end")
        for b in carregar_bots():
            n = len(carregar_links(b["id"]))
            lbox_bots.insert("end",
                f"  {b['id']}  |  {b['nome']:<20}  |  Canal: {b.get('chat_id',''):<20}"
                f"  |  {n} links  |  {b.get('hora_inicio','9')}h–{b.get('hora_fim','23')}h"
                f"  cada {b.get('intervalo','10')}min")
 
    atualizar_lbox_bots()
 
    # ── Formulário de adição / edição ─────────────────────────────────────────
    fr_form = tk.LabelFrame(aba_cfg, text="  ➕ Adicionar / Editar Bot  ",
                            bg=CINZA, fg=BRANCO, font=FONTE_B,
                            relief="flat", highlightbackground=ROXO, highlightthickness=1)
    fr_form.pack(fill="x", padx=16, pady=10)
 
    campos = [
        ("Nome do bot (ex: Bot Shopee):", "nome"),
        ("Token (@BotFather):",           "token"),
        ("Chat ID do canal (ex: @canal):","chat_id"),
        ("Hora início (ex: 9):",          "hora_inicio"),
        ("Hora fim (ex: 23):",            "hora_fim"),
        ("Intervalo em minutos:",         "intervalo"),
    ]
    entries_form: dict = {}
    for i, (rotulo, chave) in enumerate(campos):
        tk.Label(fr_form, text=rotulo, bg=CINZA, fg=BRANCO, font=FONTE,
                 anchor="w").grid(row=i, column=0, sticky="w", padx=10, pady=3)
        e = entry(fr_form, width=50)
        e.grid(row=i, column=1, padx=6, pady=3)
        entries_form[chave] = e
 
    # Padrões
    entries_form["hora_inicio"].insert(0, "9")
    entries_form["hora_fim"].insert(0, "23")
    entries_form["intervalo"].insert(0, "10")
 
    # Variável que guarda o id do bot sendo editado (None = novo bot)
    bot_em_edicao = [None]
 
    def limpar_form():
        for e in entries_form.values():
            e.delete(0, "end")
        entries_form["hora_inicio"].insert(0, "9")
        entries_form["hora_fim"].insert(0, "23")
        entries_form["intervalo"].insert(0, "10")
        bot_em_edicao[0] = None
        lbl_form_titulo.config(text="➕ Novo bot")
 
    def abrir_edicao(bot_id: str):
        """Preenche o formulário com os dados do bot para edição."""
        bots = carregar_bots()
        bot  = next((b for b in bots if b["id"] == bot_id), None)
        if not bot:
            return
        limpar_form()
        for chave, entry_widget in entries_form.items():
            entry_widget.insert(0, bot.get(chave, ""))
        bot_em_edicao[0] = bot_id
        lbl_form_titulo.config(text=f"✏️ Editando: {bot['nome']}")
        nb.select(aba_cfg)  # Vai para a aba de bots
 
    lbl_form_titulo = lbl(fr_form, "➕ Novo bot", fg=VERDE)
    lbl_form_titulo.grid(row=len(campos), column=0, columnspan=2,
                         sticky="w", padx=10, pady=(6, 2))
 
    def salvar_bot_form():
        """Salva um bot novo ou atualiza o bot em edição."""
        bots = carregar_bots()
        dados = {chave: e.get().strip() for chave, e in entries_form.items()}
 
        # Validação básica
        if not dados["nome"] or not dados["token"] or not dados["chat_id"]:
            messagebox.showerror("Erro", "Nome, Token e Chat ID são obrigatórios!")
            return
 
        if bot_em_edicao[0]:
            # Atualiza bot existente
            for b in bots:
                if b["id"] == bot_em_edicao[0]:
                    b.update(dados)
                    break
            log(f"✏️ Bot '{dados['nome']}' atualizado.")
        else:
            # Novo bot
            dados["id"] = novo_id(bots)
            bots.append(dados)
            log(f"➕ Bot '{dados['nome']}' cadastrado com ID {dados['id']}.")
 
        salvar_bots(bots)
        atualizar_lbox_bots()
        renderizar_painel()
        limpar_form()
        messagebox.showinfo("Salvo", "Bot salvo com sucesso!")
 
    fr_form_btns = tk.Frame(fr_form, bg=CINZA)
    fr_form_btns.grid(row=len(campos)+1, column=0, columnspan=2,
                      sticky="e", padx=10, pady=8)
    btn(fr_form_btns, "💾 Salvar bot", VERDE,   salvar_bot_form).pack(side="left", padx=4)
    btn(fr_form_btns, "🔄 Limpar",     AZUL,    limpar_form    ).pack(side="left", padx=4)
 
    btn(aba_cfg, "➕ Novo bot", ROXO, limpar_form).pack(anchor="w", padx=16, pady=(0, 10))
 
 
    # ╔══════════════════════════════════════════════════════╗
    # ║  ABA 3 – LINKS POR BOT                              ║
    # ╚══════════════════════════════════════════════════════╝
    aba_links = aba("🔗  Links")
 
    lbl(aba_links, "Bot selecionado:", bg=CINZA).pack(anchor="w", padx=16, pady=(12, 2))
 
    # Selector do bot ativo na aba de links
    bot_links_var = tk.StringVar()
    combo_bots = ttk.Combobox(aba_links, textvariable=bot_links_var,
                               state="readonly", font=FONTE, width=40)
    combo_bots.pack(anchor="w", padx=16, pady=(0, 6))
 
    links_atuais: list = []   # Links do bot selecionado no combo
 
    # Label de contagem – criado antes de atualizar_links_listbox para evitar conflito
    lbl_contagem = tk.Label(aba_links, text="Total: 0 links",
                            bg=CINZA, fg=VERDE, font=FONTE_B)
    lbl_contagem.pack(anchor="w", padx=16)
 
    # Listbox com scroll duplo
    fr_lb = tk.Frame(aba_links, bg=CINZA)
    fr_lb.pack(fill="both", expand=True, padx=16, pady=4)
 
    sb_v = tk.Scrollbar(fr_lb, orient="vertical")
    sb_v.pack(side="right", fill="y")
    sb_h = tk.Scrollbar(fr_lb, orient="horizontal")
    sb_h.pack(side="bottom", fill="x")
 
    listbox_links = tk.Listbox(fr_lb, yscrollcommand=sb_v.set, xscrollcommand=sb_h.set,
                               bg="#0d0d1a", fg=BRANCO, font=("Consolas", 9),
                               selectbackground=ROXO, relief="flat", bd=0, activestyle="none")
    listbox_links.pack(fill="both", expand=True)
    sb_v.config(command=listbox_links.yview)
    sb_h.config(command=listbox_links.xview)
 
    def atualizar_links_listbox():
        """Repopula a listbox com os links do bot selecionado."""
        listbox_links.delete(0, "end")
        for i, item in enumerate(links_atuais):
            txt = item.get("texto", "")[:28].strip('"')
            prc = item.get("preco", "")[:10].strip('"')
            listbox_links.insert(
                "end",
                f"  {i+1:03d}  |  {txt:<28}  |  {prc:<10}  →  {item['link'][:45]}"
            )
        lbl_contagem.config(text=f"Total: {len(links_atuais)} links")
 
    def ao_selecionar_bot(event=None):
        """Carrega os links do bot selecionado no combo."""
        nome_sel = bot_links_var.get()
        bots     = carregar_bots()
        bot      = next((b for b in bots if b["nome"] == nome_sel), None)
        if not bot:
            return
        links_atuais.clear()
        links_atuais.extend(carregar_links(bot["id"]))
        atualizar_links_listbox()
 
    combo_bots.bind("<<ComboboxSelected>>", ao_selecionar_bot)
 
    def atualizar_combo_bots():
        """Atualiza a lista de opções do combo com os bots cadastrados."""
        bots = carregar_bots()
        nomes = [b["nome"] for b in bots]
        combo_bots["values"] = nomes
        if nomes and not bot_links_var.get():
            combo_bots.current(0)
            ao_selecionar_bot()
 
    atualizar_combo_bots()
 
    # ── Formulário adicionar link manualmente ─────────────────────────────────
    fr_add = tk.LabelFrame(aba_links, text="  ➕ Adicionar produto manualmente  ",
                           bg=CINZA, fg=BRANCO, font=FONTE_B,
                           relief="flat", highlightbackground=ROXO, highlightthickness=1)
    fr_add.pack(fill="x", padx=16, pady=6)
 
    tk.Label(fr_add, text="URL:", bg=CINZA, fg=BRANCO, font=FONTE).grid(
        row=0, column=0, sticky="w", padx=8, pady=3)
    e_url = entry(fr_add, width=60)
    e_url.grid(row=0, column=1, padx=4)
 
    tk.Label(fr_add, text="Descrição:", bg=CINZA, fg=BRANCO, font=FONTE).grid(
        row=1, column=0, sticky="nw", padx=8, pady=3)
    e_texto = tk.Text(fr_add, width=60, height=2, bg="#0d0d1a", fg=BRANCO,
                      insertbackground=BRANCO, font=FONTE, relief="flat", bd=4)
    e_texto.grid(row=1, column=1, padx=4, pady=3)
 
    tk.Label(fr_add, text="Preço:", bg=CINZA, fg=BRANCO, font=FONTE).grid(
        row=2, column=0, sticky="w", padx=8, pady=3)
    e_preco = entry(fr_add, width=20)
    e_preco.grid(row=2, column=1, sticky="w", padx=4)
 
    def adicionar_link_manual():
        """Adiciona um produto manualmente ao bot selecionado no combo."""
        nome_sel = bot_links_var.get()
        bots     = carregar_bots()
        bot      = next((b for b in bots if b["nome"] == nome_sel), None)
        if not bot:
            messagebox.showerror("Erro", "Selecione um bot antes de adicionar links!")
            return
        url   = e_url.get().strip()
        texto = e_texto.get("1.0", "end").strip()
        preco = e_preco.get().strip()
        if not url or not texto or not preco:
            messagebox.showwarning("Atenção", "Preencha URL, descrição e preço!")
            return
        links_atuais.append({"link": url, "texto": texto, "preco": preco})
        salvar_links(bot["id"], links_atuais)
        atualizar_links_listbox()
        e_url.delete(0, "end")
        e_texto.delete("1.0", "end")
        e_preco.delete(0, "end")
        renderizar_painel()
        log(f"[{bot['nome']}] 🔗 Link adicionado manualmente.")
 
    btn(fr_add, "➕ Adicionar", VERDE, adicionar_link_manual).grid(
        row=3, column=1, sticky="e", padx=4, pady=6)
 
    # ── Botões de importação e gestão ─────────────────────────────────────────
    fr_acoes = tk.Frame(aba_links, bg=CINZA)
    fr_acoes.pack(fill="x", padx=16, pady=4)
 
    def importar_arquivo():
        """
        Importa links de .txt ou .csv para o bot selecionado.
 
        FORMATOS ACEITOS:
          TXT com |||:  link|||texto|||preco
          CSV com , :   link,texto,preco  (aspas suportadas pelo módulo csv)
        """
        nome_sel = bot_links_var.get()
        bots     = carregar_bots()
        bot      = next((b for b in bots if b["nome"] == nome_sel), None)
        if not bot:
            messagebox.showerror("Erro", "Selecione um bot primeiro!")
            return
 
        caminho = filedialog.askopenfilename(
            title="Selecionar arquivo de links",
            filetypes=[("Texto/CSV", "*.txt *.csv"), ("Todos", "*.*")]
        )
        if not caminho:
            return
 
        novos, erros = 0, 0
 
        with open(caminho, encoding="utf-8-sig") as f:
            primeira = f.readline().strip()
        usa_pipe = "|||" in primeira
 
        with open(caminho, encoding="utf-8-sig") as f:
            if usa_pipe:
                for n, linha in enumerate(f, 1):
                    linha = linha.strip()
                    if not linha:
                        continue
                    if n == 1 and not linha.startswith("http"):
                        continue
                    partes = [p.strip().strip('"').strip("'") for p in linha.split("|||")]
                    if len(partes) >= 3:
                        links_atuais.append({"link": partes[0], "texto": partes[1], "preco": partes[2]})
                        novos += 1
                    elif len(partes) == 2:
                        links_atuais.append({"link": partes[0], "texto": partes[1], "preco": "Consulte o link"})
                        novos += 1
                    else:
                        erros += 1
            else:
                reader = csv.reader(f)
                for n, row in enumerate(reader, 1):
                    if not row:
                        continue
                    row = [c.strip().strip('"').strip("'") for c in row]
                    if n == 1 and not row[0].startswith("http"):
                        continue
                    if len(row) >= 3:
                        links_atuais.append({"link": row[0], "texto": row[1], "preco": row[2]})
                        novos += 1
                    elif len(row) == 2:
                        links_atuais.append({"link": row[0], "texto": row[1], "preco": "Consulte o link"})
                        novos += 1
                    elif len(row) == 1 and row[0].startswith("http"):
                        links_atuais.append({"link": row[0], "texto": "Oferta", "preco": "Consulte o link"})
                        novos += 1
                    else:
                        erros += 1
 
        salvar_links(bot["id"], links_atuais)
        atualizar_links_listbox()
        renderizar_painel()
        msg = f"{novos} links importados!"
        if erros:
            msg += f"\n{erros} linha(s) ignoradas."
        messagebox.showinfo("Importação concluída", msg)
        log(f"[{bot['nome']}] 📥 {novos} links importados, {erros} ignorados.")
 
    def remover_link_selecionado():
        nome_sel = bot_links_var.get()
        bots     = carregar_bots()
        bot      = next((b for b in bots if b["nome"] == nome_sel), None)
        sel = listbox_links.curselection()
        if not sel:
            messagebox.showwarning("Atenção", "Selecione um link para remover.")
            return
        links_atuais.pop(sel[0])
        if bot:
            salvar_links(bot["id"], links_atuais)
        atualizar_links_listbox()
 
    def limpar_links():
        nome_sel = bot_links_var.get()
        bots     = carregar_bots()
        bot      = next((b for b in bots if b["nome"] == nome_sel), None)
        if not messagebox.askyesno("Confirmar", "Apagar TODOS os links deste bot?"):
            return
        links_atuais.clear()
        if bot:
            salvar_links(bot["id"], links_atuais)
        atualizar_links_listbox()
        renderizar_painel()
 
    btn(fr_acoes, "📥 Importar .txt/.csv", AZUL,     importar_arquivo       ).pack(side="left", padx=4)
    btn(fr_acoes, "🗑️ Remover selecionado", ROXO,    remover_link_selecionado).pack(side="left", padx=4)
    btn(fr_acoes, "❌ Limpar todos",         VERMELHO, limpar_links           ).pack(side="left", padx=4)
    btn(fr_acoes, "🔄 Trocar bot",           AZUL,
        lambda: (atualizar_combo_bots(), ao_selecionar_bot())).pack(side="left", padx=4)
 
    tk.Label(aba_links,
             text="💡 Formato: https://link.com|||Descrição do produto|||R$99,90",
             bg=CINZA, fg="#888", font=("Segoe UI", 8)).pack(anchor="w", padx=16, pady=2)
 
 
    # ╔══════════════════════════════════════════════════════╗
    # ║  ABA 4 – LOG DE EVENTOS                             ║
    # ╚══════════════════════════════════════════════════════╝
    aba_log = aba("📋  Log")
 
    log_widget = tk.Text(aba_log, bg="#0d0d1a", fg="#00ff88",
                         font=("Consolas", 9), state="disabled",
                         relief="flat", bd=0)
    log_widget.pack(fill="both", expand=True, padx=10, pady=10)
 
    sb_log = tk.Scrollbar(aba_log, command=log_widget.yview)
    log_widget.configure(yscrollcommand=sb_log.set)
 
    def limpar_log():
        log_widget.configure(state="normal")
        log_widget.delete("1.0", "end")
        log_widget.configure(state="disabled")
 
    btn(aba_log, "🗑️ Limpar log", CINZA, limpar_log).pack(anchor="e", padx=10, pady=4)
 
    # ── Inicialização final ───────────────────────────────────────────────────
    renderizar_painel()
    log(f"🟢 Sistema iniciado. {len(carregar_bots())} bot(s) cadastrado(s).")
 
    janela.mainloop()
 
 
# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    criar_interface()
