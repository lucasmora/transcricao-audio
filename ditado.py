"""
Ditado por voz - suporta vários provedores de transcrição (Groq, Mistral).
"""
import io
import os
import wave
import threading
import queue
import sounddevice as sd
import keyboard
import tkinter as tk
import tkinter.ttk as ttk
from groq import Groq
# ----------------------------------------------------------------
HOTKEY = "ctrl+\\"
SAMPLE_RATE = 16000
DEFAULT_MODEL = "whisper-large-v3-turbo"

# Idiomas suportados: nome exibido no dropdown -> código usado na API
LANGUAGES = {
    "Português": "pt",
    "Inglês": "en",
}

# Provedores: nome -> configuração
PROVIDERS = {
    "Groq": {
        "env_key": "GROQ_API_KEY",
        "kind": "groq",
        # Filtro opcional: só modelos de transcrição de áudio (nome contém "whisper")
        "model_filter": "whisper",
    },
    "Mistral": {
        "env_key": "MISTRAL_API_KEY",
        "kind": "mistral",
        # Filtro opcional: só modelos de transcrição de áudio (nome contém "voxtral")
        "model_filter": "voxtral",
    },
    "Local (faster-whisper)": {
        "env_key": None,
        "kind": "local",
        "model_filter": None,
    },
}

# Modelos a OCULTAR do dropdown - edite manualmente quando quiser esconder um modelo
EXCLUDED_MODELS = {
    "distil-whisper-large-v3-en"
}

# Modelos locais (faster-whisper) - apenas CPU
LOCAL_MODELS = ["tiny", "base", "small", "medium"]

# Lista de fallback (usada se a chamada à API falhar)
FALLBACK_MODELS = {
    "Groq": ["whisper-large-v3-turbo", "whisper-large-v3"],
    "Mistral": ["voxtral-mini-latest", "voxtral-mini-2507"],
}
# ----------------------------------------------------------------
client = None  # recriado quando o provedor muda
ui_queue = queue.Queue()
recording = []
is_recording = False
selected_provider = "Groq"
selected_model = DEFAULT_MODEL
selected_language = "pt"
# Configurações de Cores
BG = "#1f1f1f"
FG = "#f2f2f2"
ACCENT = "#3a7afe"
ACCENT_REC = "#e04141"


def create_client(provider_name):
    global client
    cfg = PROVIDERS[provider_name]
    if cfg["kind"] == "local":
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            raise RuntimeError(
                "Pacote 'faster-whisper' não instalado. Execute: pip install faster-whisper"
            )
        client = None
        return client
    api_key = os.getenv(cfg["env_key"], "")
    if not api_key:
        raise RuntimeError(f"Variável de ambiente {cfg['env_key']} não configurada")
    if cfg["kind"] == "groq":
        client = Groq(api_key=api_key)
    elif cfg["kind"] == "mistral":
        try:
            from mistralai.client import Mistral
        except ImportError:
            raise RuntimeError(
                "Pacote 'mistralai' não instalado. Execute: pip install mistralai"
            )
        client = Mistral(api_key=api_key)
    return client


def list_models(provider_name):
    cfg = PROVIDERS[provider_name]
    if provider_name == "Local (faster-whisper)":
        return LOCAL_MODELS
    if not os.getenv(cfg["env_key"], ""):
        raise RuntimeError(f"Variável de ambiente {cfg['env_key']} não configurada")
    try:
        c = create_client(provider_name)
        modelos = [m.id for m in c.models.list()]
    except Exception:
        modelos = FALLBACK_MODELS.get(provider_name, [])
    filtro = cfg.get("model_filter")
    if filtro:
        modelos = [m for m in modelos if filtro in m]
    return [m for m in modelos if m not in EXCLUDED_MODELS]


def carregar_modelos(provider):
    """Busca modelos em thread e entrega via ui_queue (não trava a GUI)."""
    try:
        modelos = list_models(provider)
    except Exception as e:
        ui_queue.put(("status", f"Erro ao carregar modelos: {e}"))
        ui_queue.put(("models_loaded", provider, []))
        return
    ui_queue.put(("models_loaded", provider, modelos))


def audio_callback(indata, frames, time_info, status):
    if is_recording:
        recording.append(bytes(indata))
        

def transcrever(provider_name, client, audio_bytes, model):
    """Transcreve o áudio usando o cliente do provedor selecionado.

    Retorna o texto transcrito. Cada provedor tem seu jeito de chamar a API,
    mas todos devolvem um objeto com o campo `.text`.
    """
    cfg = PROVIDERS[provider_name]
    if cfg["kind"] == "groq":
        response = client.audio.transcriptions.create(
            file=("audio.wav", audio_bytes),
            model=model,
            language=selected_language,
        )
    elif cfg["kind"] == "mistral":
        response = client.audio.transcriptions.complete(
            model=model,
            file={"content": audio_bytes, "file_name": "audio.wav"},
            language=selected_language,
        )
    elif cfg["kind"] == "local":
        from faster_whisper import WhisperModel
        whisper_model = WhisperModel(model, device="cpu", compute_type="int8")
        buf = io.BytesIO(audio_bytes)
        segments, _ = whisper_model.transcribe(buf, language=selected_language)
        return " ".join([seg.text for seg in segments])
    else:
        raise RuntimeError(f"Provedor não suportado: {provider_name}")
    return response.text


def stop_and_transcribe():
    global is_recording, stream
    if not is_recording: return
    
    is_recording = False
    if stream:
        stream.stop()
        stream.close()
        stream = None
        
    ui_queue.put(("status", "Transcrevendo..."))
    ui_queue.put(("record_state", False))
    
    if not recording:
        ui_queue.put(("status", "Pronto"))
        return
    audio_bytes = b"".join(recording)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio_bytes)
    
    try:
        cfg = PROVIDERS[selected_provider]
        if cfg["kind"] != "local" and client is None:
            create_client(selected_provider)
        response = transcrever(selected_provider, client, buf.getvalue(), selected_model)
        ui_queue.put(("text", response))
    except Exception as e:
        ui_queue.put(("text", f"\n[Erro]: {str(e)}"))
    
    ui_queue.put(("status", "Pronto"))
def toggle_recording():
    global is_recording, stream
    if is_recording:
        threading.Thread(target=stop_and_transcribe, daemon=True).start()
    else:
        recording.clear()
        is_recording = True
        stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", callback=audio_callback)
        stream.start()
        ui_queue.put(("status", "Gravando..."))
        ui_queue.put(("record_state", True))
# Interface
root = tk.Tk()
root.title("Ditado")
root.configure(bg=BG)

# Posiciona a janela no canto inferior direito da tela
LARGURA, ALTURA = 400, 300
largura_tela = root.winfo_screenwidth()
altura_tela = root.winfo_screenheight()
pos_x = largura_tela - LARGURA - 20
pos_y = altura_tela - ALTURA - 100  # Deixa margem de 100 para a altura da tela (barra de tarefas)
root.geometry(f"{LARGURA}x{ALTURA}+{pos_x}+{pos_y}")
# Estilo escuro para os comboboxes (ttk não herda bg/fg do Tk)
style = ttk.Style()
style.theme_use("clam")
style.configure("TCombobox", fieldbackground="#ffffff", background="#333333",
                foreground="#000000", arrowcolor=FG,
                selectbackground=ACCENT, selectforeground="#ffffff")
# Elementos
lbl_status = tk.Label(root, text="Pronto", bg=BG, fg=FG)
lbl_status.pack(pady=5)

# Frame com os seletores de provedor e modelo
frame_seletores = tk.Frame(root, bg=BG)
frame_seletores.pack(pady=5)

tk.Label(frame_seletores, text="Provedor:", bg=BG, fg=FG).pack(side="left", padx=(10, 2))
cmb_provider = ttk.Combobox(frame_seletores, values=list(PROVIDERS.keys()), state="readonly", width=14)
cmb_provider.pack(side="left", padx=(0, 10))

tk.Label(frame_seletores, text="Modelo:", bg=BG, fg=FG).pack(side="left", padx=(10, 2))
cmb_model = ttk.Combobox(frame_seletores, state="readonly", width=24)
cmb_model.pack(side="left", padx=(0, 10))

# Seletor de idioma em linha própria, abaixo dos demais
frame_idioma = tk.Frame(root, bg=BG)
frame_idioma.pack(pady=(0, 5))
tk.Label(frame_idioma, text="Idioma:", bg=BG, fg=FG).pack(side="left", padx=(10, 2))
cmb_lang = ttk.Combobox(frame_idioma, values=list(LANGUAGES.keys()), state="readonly", width=10)
cmb_lang.set("Português")
cmb_lang.pack(side="left", padx=(0, 10))


def on_provider_change(event=None):
    global selected_provider, client
    provider = cmb_provider.get()
    if not provider:
        return
    selected_provider = provider
    client = None  # força recriação com a chave correta
    cmb_model.set("")
    cmb_model["values"] = []
    lbl_status.config(text="Carregando modelos...")
    threading.Thread(target=carregar_modelos, args=(provider,), daemon=True).start()


def on_model_change(event=None):
    global selected_model
    selected_model = cmb_model.get()


def on_language_change(event=None):
    global selected_language
    selected_language = LANGUAGES[cmb_lang.get()]


cmb_provider.bind("<<ComboboxSelected>>", on_provider_change)
cmb_model.bind("<<ComboboxSelected>>", on_model_change)
cmb_lang.bind("<<ComboboxSelected>>", on_language_change)

# Checkbox "Sempre no topo"
sempre_no_topo = tk.BooleanVar(value=False)
# Forçar a aplicação do atributo para que a janela já inicie no topo
root.attributes("-topmost", False)
def alternar_topo():
    root.attributes("-topmost", sempre_no_topo.get())
chk_topo = tk.Checkbutton(
    root, text="Sempre no topo", variable=sempre_no_topo, command=alternar_topo,
    bg=BG, fg=FG, selectcolor="#333333", activebackground=BG, activeforeground=FG
)
chk_topo.pack(pady=2)

# Checkbox "Colar automaticamente"
colar_auto = tk.BooleanVar(value=False)
chk_colar = tk.Checkbutton(
    root, text="Colar automaticamente", variable=colar_auto,
    bg=BG, fg=FG, selectcolor="#333333", activebackground=BG, activeforeground=FG
)
chk_colar.pack(pady=2)

btn_mic = tk.Button(root, text="🎤 Gravar", command=toggle_recording, bg=ACCENT, fg="white")
btn_mic.pack(pady=5)
def excluir_texto():
    txt_area.delete("1.0", "end")

def copiar_texto():
    conteudo = txt_area.get("1.0", "end-1c")
    root.clipboard_clear()
    root.clipboard_append(conteudo)
    root.update()  # garante que o clipboard fique disponível mesmo após o app fechar
    lbl_status.config(text="Copiado!")

frame_botoes = tk.Frame(root, bg=BG)
frame_botoes.pack(pady=5)
btn_excluir = tk.Button(frame_botoes, text="Excluir", command=excluir_texto, bg="#333333", fg=FG)
btn_excluir.pack(side="left", padx=5)
btn_copiar = tk.Button(frame_botoes, text="Copiar", command=copiar_texto, bg="#333333", fg=FG)
btn_copiar.pack(side="left", padx=5)

txt_area = tk.Text(root, bg="#141414", fg=FG, insertbackground=FG)
txt_area.pack(fill="both", expand=True, padx=10, pady=10)

def process_queue():
    global selected_model
    try:
        while True:
            kind, *msg = ui_queue.get_nowait()
            if kind == "status": lbl_status.config(text=msg[0])
            elif kind == "record_state":
                if msg[0]:
                    btn_mic.config(text="🔴 Gravando...", bg=ACCENT_REC)
                else:
                    btn_mic.config(text="🎤 Gravar", bg=ACCENT)
            elif kind == "models_loaded":
                provider, modelos = msg
                if provider != selected_provider:
                    return  # usuário trocou de provedor no meio
                cmb_model["values"] = modelos
                if modelos:
                    cmb_model.current(0)  # pré-seleciona o primeiro
                    selected_model = modelos[0]
                lbl_status.config(text="Pronto" if modelos else "Nenhum modelo disponível")
            elif kind == "text":
                trecho = msg[0].strip()
                if trecho:
                    conteudo_atual = txt_area.get("1.0", "end-1c")
                    if conteudo_atual and not conteudo_atual.endswith(" "):
                        txt_area.insert("end", " ")
                    txt_area.insert("end", trecho)
                    txt_area.mark_set("insert", "end")
                    txt_area.see("end")
                    
                    # Lógica de colagem automática
                    if colar_auto.get():
                        root.clipboard_clear()
                        root.clipboard_append(trecho)
                        root.update()
                        root.after(100, lambda: keyboard.press_and_release("ctrl+v"))
    except queue.Empty: pass
    root.after(100, process_queue)
keyboard.add_hotkey(HOTKEY, toggle_recording)
# Pré-seleciona o primeiro provedor e carrega os modelos dele
cmb_provider.set(selected_provider)
on_provider_change()
process_queue()
root.focus_force()
root.mainloop()