Ditado – Vídeo para Texto
================================================

**Descrição**
-------------
*Ditado.py* é um aplicativo de gravação e transcrição de áudio em tempo real com suporte a múltiplos provedores:
- **Groq** – modelo Whisper‑Large‑V3‑Turbo (padrão).
- **Mistral** – modelo Voxtral Mini Transcribe (`voxtral-mini-latest`).
- Grava áudio do microfone (16 kHz).
- Transcreve em Português.
- Interface Tkinter simples com botão de gravação + hot‑key *Ctrl+\\*.
- Ajuda, status e clipboard embutidos.

**Requisitos**
-------------
- Python ≥ 3.7 com Tkinter (padrão).
- Bibliotecas Python: `numpy`, `sounddevice`, `keyboard`, `groq`.
  ```bash
  pip install numpy sounddevice keyboard groq
  ```
- Para usar o provedor **Mistral**, instale também o SDK oficial:
  ```bash
  pip install mistralai
  ```
- Variável de ambiente `GROQ_API_KEY` (provedor Groq) ou `MISTRAL_API_KEY` (provedor Mistral) com sua chave.
- Microfone funcional; em Windows verifique drivers e permissões de áudio.

**Instalação (para Windows)**
---------------------------
```cmd
cd ~\Ditado
python -m pip install --upgrade pip
pip install numpy sounddevice keyboard groq
set GROQ_API_KEY=***
set MISTRAL_API_KEY=***
python ditado.py
```

**Provedores e Modelos**
------------------------
Na barra superior da janela há dois seletores:
1. **Provedor** – lista os provedores configurados em `PROVIDERS` (Groq, Mistral).
2. **Modelo** – é preenchido automaticamente com os modelos de transcrição do provedor escolhido.

- O dropdown de modelo exibe apenas os modelos relevantes para transcrição de áudio
  (contêm "whisper" no Groq e "voxtral" na Mistral).
- Para esconder um modelo da lista, adicione o nome dele em `EXCLUDED_MODELS` no código.
- Se a chamada à API de listagem falhar (ex.: sem internet), o programa usa os
  modelos de fallback definidos em `FALLBACK_MODELS`.
- Para adicionar um novo provedor, basta incluir uma entrada em `PROVIDERS`
  (com `env_key`, `kind` e `model_filter` opcional) e implementar o ramo
  correspondente nas funções `create_client` e `transcrever`.

**Uso**
------
1. **Abrir** → o script inicia uma janela na borda inferior direita.
2. **Clique** no botão *🎤 Gravar* ou pressione *Ctrl+\\*. 
3. Fale. 
4. Com o botão de gravação novamente você interrompe; o texto aparece na caixa e, se a opção “Colar automaticamente” estiver marcada, o trecho é copiado para a área de transferência e simulado `Ctrl+V`.
5. **Copiar** → Copia todo o texto. 
6. **Excluir** → Limpa a caixa. 
7. **Sempre no topo** → Mantém a janela sempre na frente.
8. O status (*Pronto*, *Gravando…*, *Transcrevendo…*) aparece na label na parte superior.

**Hot‑key**
----------
- `Ctrl+\` (Ctrl + tecla barra invertida) aciona disparo/gravação.
- Se a tecla não funcionar, verifique a localização da tecla “\” no seu teclado ou edite o valor `HOTKEY` em `ditado.py`.

**Personalizações**
-------------------
- `DEFAULT_MODEL`: troque para outro modelo Whisper suportado.
- `COLAR_AUTO`: predefina no código para auto‑colar por padrão.
- Cores de interface: editável via variáveis `BG`, `FG`, `ACCENT`, `ACCENT_REC`.
- `SAMPLE_RATE`: 16000 Hz; altere se desejar taxa de amostragem diferente (ex.: 48000).

**Notas Técnicas**
-----------------
- O áudio é salvo em memória (`BytesIO`) e enviado como arquivo *audio.wav* para a API.
- Concatenação de blocos de áudio usa `np.concatenate`.
- `keyboard` ouve a hot‑key em thread isolada; assim a GUI não bloqueia.
- O `tkinter` usa `after(100, process_queue)` para consumir eventos da fila de UI de forma não‑bloqueante.
- Carregamento de TTS ou plugins não incluídos; este script apenas grava e transcreve.

**Dicas de Depuração**
----------------------
- Se a transcrição falhar, verifique a saída no console (`[Erro]: …`).
- Certifique‑se de que a variável de ambiente está configurada (`echo %GROQ_API_KEY%`).
- Em Linux/macOS, use `sudo apt install portaudio19-dev libportaudio2` antes de instalar `sounddevice`.

**Licença**
--------
MIT. Sinta‑se livre para usar, modificar e distribuir, contanto que essa licença seja mantida.

**Versões/Alterações**
---------------------
- **1.0.0** – Versão inicial.
- **1.1.0** – Hot‑key `Ctrl+\\`, colagem automática e integração `keyboard`.

### Threading e Responsividade
O script usa *threads* para manter a interface responsiva:
- `threading.Thread` roda a função de paragem/transcrição em background, mantendo a GUI sem bloquear.
- A biblioteca `keyboard` cria internamente uma thread para escutar o hot‑key `Ctrl+\\` sem interferir no loop principal do Tkinter.
