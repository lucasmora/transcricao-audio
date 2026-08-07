Ditado – Áudio para Texto
================================================

<div align="center">

# 🎤 Ditado – Áudio para Texto

![Python](https://img.shields.io/badge/Python-3.7%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Tkinter](https://img.shields.io/badge/Tkinter-GUI-5B5BD6?style=flat-square)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-22c55e?style=flat-square)
![Versão](https://img.shields.io/badge/Vers%C3%A3o-2.0.0-blue?style=flat-square)

</div>

**Descrição**
-------------
*Ditado.py* é um aplicativo de gravação e transcrição de áudio com suporte a provedores de STT, como Groq e Mistral.
- **Groq** – modelo Whisper‑Large‑V3‑Turbo (padrão).
- **Mistral** – modelo Voxtral Mini Transcribe (`voxtral-mini-latest`).
- Grava áudio do microfone com taxa de amostragem de 16 kHz.
- Transcreve em Português e Inglês (configurável na interface).
- Interface Tkinter simples com botão de gravação + hot‑key `Ctrl + \`.
- Status e clipboard embutidos.

**Requisitos**
-------------
- Python ≥ 3.7 com Tkinter (padrão).
- Bibliotecas Python com provedor Groq: `numpy`, `sounddevice`, `keyboard`, `groq`.
  ```bash
  pip install numpy sounddevice keyboard groq
  ```
- Para usar o provedor **Mistral**, instale também o SDK oficial:
  ```bash
  pip install mistralai
  ```
- Variável de ambiente `GROQ_API_KEY` (provedor Groq) ou `MISTRAL_API_KEY` (provedor Mistral) com sua chave.
- Microfone funcional; em Windows verifique as configurações de áudio.

**Instalação (para Windows)**
---------------------------
```cmd
cd ~\Ditado
python -m pip install --upgrade pip
pip install numpy sounddevice keyboard groq mistralai
set GROQ_API_KEY=SUA_CHAVE_AQUI
set MISTRAL_API_KEY=SUA_CHAVE_AQUI
python ditado.py
```

**Provedores e Modelos**
------------------------
Na barra superior da janela há três seletores:
1. **Provedor** – lista os provedores configurados em `PROVIDERS` (Groq, Mistral).
2. **Modelo** – é preenchido automaticamente com os modelos de transcrição do provedor escolhido.
3. **Idioma** – define o idioma da transcrição: **Português** (padrão) ou **Inglês**.

- O dropdown de modelo exibe apenas os modelos relevantes para transcrição de áudio
  (contêm "whisper" no Groq e "voxtral" na Mistral).
- Para esconder um modelo da lista, adicione o nome dele em `EXCLUDED_MODELS` no código.
- Se a chamada à API de listagem falhar (ex.: sem internet), o programa usa os
  modelos de fallback definidos em `FALLBACK_MODELS`.
- Para adicionar um novo idioma, basta incluir uma entrada em `LANGUAGES`
  (nome exibido no dropdown -> código usado na API, ex.: `"Espanhol": "es"`).
- Para adicionar um novo provedor, basta incluir uma entrada em `PROVIDERS`
  (com `env_key`, `kind` e `model_filter` opcional) e implementar o ramo
  correspondente nas funções `create_client` e `transcrever`.

**Uso**
------
1. **Abrir** → o script inicia uma janela na borda inferior direita.
2. **Idioma** → escolha entre *Português* (padrão) ou *Inglês* para a transcrição.
3. O status (*Pronto*, *Gravando…*, *Transcrevendo…*) aparece na label na parte superior.
4. **Clique** no botão *🎤 Gravar* ou pressione `Ctrl + \`. 
5. Fale. 
6. Com o botão de gravação novamente você interrompe; o texto aparece na caixa e, se a opção “Colar automaticamente” estiver marcada, o trecho é copiado para a área de transferência e simulado `Ctrl + V`.
7. **Copiar** → Copia todo o texto. 
8. **Excluir** → Limpa a caixa. 
9. **Sempre no topo** → Mantém a janela sempre na frente.

**Hot‑key**
----------
- `Ctrl + \` (Ctrl + tecla barra invertida) aciona disparo/gravação.

**Personalizações**
-------------------
- `DEFAULT_MODEL`: troque para outro modelo suportado.
- Cores de interface: editável via variáveis `BG`, `FG`, `ACCENT`, `ACCENT_REC`.
- `SAMPLE_RATE`: 16000 Hz; altere se desejar taxa de amostragem diferente (ex.: 48000).
- `LANGUAGES`: mapeia os idiomas exibidos no dropdown para o código usado na API.

**Threading e Responsividade**
------------------------------
O script usa *threads* para manter a interface responsiva:
- `threading.Thread` roda a função de gravação/transcrição em background, mantendo a GUI sem bloquear.
- A biblioteca `keyboard` cria internamente uma thread para escutar o hot‑key `Ctrl + \` sem interferir no loop principal do Tkinter.

**Notas Técnicas**
-----------------
- O áudio é salvo em memória (`BytesIO`) e enviado como arquivo *audio.wav* para a API.
- `keyboard` ouve a hot‑key em thread isolada; assim a GUI não bloqueia.
- O `tkinter` usa `after(100, process_queue)` para consumir eventos da fila de UI de forma não‑bloqueante.
- Carregamento de TTS ou plugins não incluídos; este script apenas grava e transcreve.

**Dicas de Depuração**
----------------------
- Se a transcrição falhar, verifique a saída no console (`[Erro]: …`).
- Certifique‑se de que as variáveis de ambiente estão configuradas (chaves API Groq e Mistral).
- Em Linux/macOS, use `sudo apt install portaudio19-dev libportaudio2` antes de instalar `sounddevice`.

**Licença**
--------
MIT. Sinta‑se livre para usar, modificar e distribuir, contanto que essa licença seja mantida.

**Como este projeto foi desenvolvido**
-----------------------------------------
- Definição dos requisitos e funcionalidades por mim.
- Desenvolvimento assistido por ferramentas de IA.
- Revisão e adaptação manual de todo o código gerado.
- Testes e validação das funcionalidades.
- Documentação escrita e mantida por mim.

**Versões/Alterações**
---------------------
- **1.0.0** – Versão inicial.
- **1.1.0** – Hot‑key `Ctrl + \`, colagem automática e integração `keyboard`.
- **2.0.0** – Dropdowns de seleção de provedor, modelo e idioma; suporte ao provedor Mistral (Voxtral); lista de fallback de modelos.