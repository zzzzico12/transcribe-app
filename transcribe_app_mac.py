import warnings
warnings.filterwarnings("ignore", message=".*LibreSSL.*")

import gradio as gr
import whisper
import glob
import os
import shutil
import tempfile
import threading
import time

try:
    from faster_whisper import WhisperModel as FasterWhisperModel
except ImportError:
    FasterWhisperModel = None

MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
TRANSCRIBE_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "ja")
BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "1"))
MAX_FILE_SIZE_MB = 2000
ALLOWED_EXTENSIONS = {
    ".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac",
    ".aac", ".wma", ".mov", ".avi", ".mkv", ".webm",
}

CSS = """
.gradio-container {
    max-width: 700px !important;
    margin: 0 auto !important;
    padding: 3rem 1.5rem 5rem !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
    background: #f9fafb !important;
}

footer { display: none !important; }

/* ─── Header ─────────────────────────────────── */
.app-header {
    margin-bottom: 2.75rem;
}
.app-header-top {
    display: flex;
    align-items: center;
    gap: 1rem;
    margin-bottom: 0.875rem;
}
.app-icon {
    width: 46px;
    height: 46px;
    min-width: 46px;
    background: #0f172a;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(15,23,42,0.18);
}
.app-title {
    font-size: 1.5rem;
    font-weight: 700;
    color: #0f172a;
    letter-spacing: -0.035em;
    margin: 0 0 0.2rem;
    line-height: 1.2;
}
.app-subtitle {
    font-size: 0.875rem;
    color: #6b7280;
    margin: 0;
    line-height: 1.45;
}
.privacy-notice {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.775rem;
    font-weight: 500;
    color: #374151;
    background: #ffffff;
    border: 1px solid #e5e7eb;
    padding: 0.4rem 0.875rem;
    border-radius: 6px;
    letter-spacing: 0.01em;
    box-shadow: 0 1px 2px rgba(0,0,0,0.04);
}
.privacy-dot {
    width: 7px;
    height: 7px;
    min-width: 7px;
    background: #16a34a;
    border-radius: 50%;
    box-shadow: 0 0 0 2.5px rgba(22,163,74,0.18);
}
.header-rule {
    height: 1px;
    background: #e5e7eb;
    margin-top: 1.75rem;
    border: none;
}

/* ─── Tabs ───────────────────────────────────── */
.tab-nav {
    border-bottom: 1px solid #e5e7eb !important;
    background: transparent !important;
    gap: 0 !important;
    padding: 0 !important;
    margin-bottom: 1.875rem !important;
}
.tab-nav button {
    font-size: 0.875rem !important;
    font-weight: 500 !important;
    color: #6b7280 !important;
    border-radius: 0 !important;
    padding: 0.625rem 1.375rem !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -1px !important;
    letter-spacing: 0.005em !important;
    transition: color 0.12s !important;
}
.tab-nav button:hover {
    color: #111827 !important;
    background: transparent !important;
}
.tab-nav button.selected {
    color: #111827 !important;
    font-weight: 600 !important;
    border-bottom: 2px solid #111827 !important;
    background: transparent !important;
}

/* ─── Labels ─────────────────────────────────── */
.label-wrap > span {
    font-size: 0.775rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

/* ─── Button ─────────────────────────────────── */
#btn-file, #btn-mic {
    background: #0f172a !important;
    border: none !important;
    border-radius: 8px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 0.9375rem !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.18), 0 1px 2px rgba(0,0,0,0.1) !important;
    transition: background 0.15s, box-shadow 0.15s, transform 0.1s !important;
    margin-top: 0.25rem !important;
}
#btn-file:hover, #btn-mic:hover {
    background: #1e293b !important;
    box-shadow: 0 4px 14px rgba(0,0,0,0.2) !important;
    transform: translateY(-1px) !important;
}
#btn-file:active, #btn-mic:active {
    transform: translateY(0) !important;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15) !important;
}

/* ─── Output ─────────────────────────────────── */
#out-file, #out-mic {
    border-radius: 8px !important;
    overflow: hidden !important;
}
#out-file textarea, #out-mic textarea {
    font-size: 0.9375rem !important;
    line-height: 1.85 !important;
    color: #1e293b !important;
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    padding: 1rem 1.125rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
#out-file textarea:focus, #out-mic textarea:focus {
    border-color: #94a3b8 !important;
    box-shadow: 0 0 0 3px rgba(148,163,184,0.15) !important;
    outline: none !important;
}

/* マイク有効化ボタン */
#btn-mic-activate {
    background: #ffffff !important;
    border: 1px solid #e5e7eb !important;
    border-radius: 8px !important;
    color: #374151 !important;
    font-weight: 500 !important;
    font-size: 0.9375rem !important;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    transition: background 0.15s, border-color 0.15s !important;
}
#btn-mic-activate:hover {
    background: #f9fafb !important;
    border-color: #d1d5db !important;
}
.mic-notice {
    font-size: 0.8125rem;
    color: #9ca3af;
    margin: 0 0 1rem;
    line-height: 1.5;
}
"""

HEADER_HTML = """
<div class="app-header">
  <div class="app-header-top">
    <div class="app-icon">
      <svg width="22" height="22" viewBox="0 0 24 24" fill="none"
           stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="2" width="6" height="12" rx="3"/>
        <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
        <line x1="12" y1="19" x2="12" y2="22"/>
        <line x1="8"  y1="22" x2="16" y2="22"/>
      </svg>
    </div>
    <div>
      <h1 class="app-title">文字起こし</h1>
      <p class="app-subtitle">音声・動画ファイルをローカルで文字起こしします</p>
    </div>
  </div>
  <div class="privacy-notice">
    <span class="privacy-dot"></span>
    完全ローカル処理 — 音声データは端末外に送信されません
  </div>
  <hr class="header-rule">
</div>
"""


def _cleanup_stale_gradio_files() -> None:
    tmp = tempfile.gettempdir()
    for path in glob.glob(os.path.join(tmp, "gradio-*")):
        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)
        except OSError:
            pass


def _get_device():
    try:
        import torch
        if torch.backends.mps.is_available():
            torch.zeros(1).to("mps")
            return "mps"
    except Exception:
        pass
    return "cpu"


device = _get_device()
_model = None
_backend = "openai-whisper"
_model_ready = threading.Event()


def _configure_torch_for_cpu() -> None:
    if device != "cpu":
        return
    try:
        import torch
        cpu_threads = max(1, (os.cpu_count() or 1) - 1)
        torch.set_num_threads(cpu_threads)
        torch.set_num_interop_threads(max(1, cpu_threads // 2))
    except Exception:
        pass


def _load_model():
    global _model, device, _backend
    _configure_torch_for_cpu()

    if FasterWhisperModel is not None:
        # faster-whisper は MPS 非対応のため CPU で実行
        _model = FasterWhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
        _backend = "faster-whisper"
    else:
        try:
            _model = whisper.load_model(MODEL_SIZE, device=device)
        except (NotImplementedError, RuntimeError):
            device = "cpu"
            _configure_torch_for_cpu()
            _model = whisper.load_model(MODEL_SIZE, device=device)
    print(f"バックエンド: {_backend}  デバイス: {device}  モデル準備完了")
    _model_ready.set()


threading.Thread(target=_load_model, daemon=True).start()


def _validate_path(path: str) -> None:
    real = os.path.realpath(path)
    tmp = os.path.realpath(tempfile.gettempdir())
    if not real.startswith(tmp + os.sep) and not real.startswith(tmp):
        raise ValueError("無効なファイルパスです。")


def _validate_file(path: str) -> None:
    ext = os.path.splitext(path)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"対応していないファイル形式です: {ext}")
    size_mb = os.path.getsize(path) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise ValueError(f"ファイルサイズが上限 ({MAX_FILE_SIZE_MB}MB) を超えています。")


def _transcribe_with_backend(audio_path: str, duration_sec: float = 0, progress_holder=None) -> str:
    if _backend == "faster-whisper":
        segments, _ = _model.transcribe(
            audio_path,
            language=TRANSCRIBE_LANGUAGE,
            task="transcribe",
            beam_size=BEAM_SIZE,
            best_of=1,
            temperature=0.0,
            condition_on_previous_text=False,
            vad_filter=True,
        )
        texts = []
        for segment in segments:
            texts.append(segment.text)
            if progress_holder is not None and duration_sec > 0:
                progress_holder[0] = min(segment.end / duration_sec, 0.95)
        return "".join(texts).strip()

    result = _model.transcribe(
        audio_path,
        language=TRANSCRIBE_LANGUAGE,
        task="transcribe",
        fp16=False,
        temperature=0.0,
        best_of=1,
        condition_on_previous_text=False,
        verbose=False,
    )
    return result["text"].strip()


def transcribe(audio_path, progress=gr.Progress()):
    if audio_path is None:
        return "音声ファイルをアップロードするか、マイクで録音してください。"

    if not _model_ready.is_set():
        progress(0, desc="モデルを読み込み中...")
        _model_ready.wait()

    try:
        _validate_path(audio_path)
        _validate_file(audio_path)

        audio_array = whisper.load_audio(audio_path)
        duration_sec = len(audio_array) / whisper.audio.SAMPLE_RATE

        result_holder = [None]
        error_holder = [None]
        progress_holder = [0.0]

        def run():
            try:
                result_holder[0] = _transcribe_with_backend(audio_path, duration_sec, progress_holder)
            except Exception as e:
                error_holder[0] = e

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        estimated_sec = duration_sec / 3 if device == "mps" else duration_sec * 3
        start = time.time()

        while thread.is_alive():
            elapsed = time.time() - start
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            if _backend == "faster-whisper":
                frac = progress_holder[0]
                desc = f"処理中 — {int(frac * 100)}%  {minutes}分{seconds}秒経過"
            else:
                frac = min(elapsed / estimated_sec, 0.95)
                desc = f"処理中 — {minutes}分{seconds}秒経過"
            progress(frac, desc=desc)
            time.sleep(1)

        if error_holder[0]:
            raise error_holder[0]

        progress(1.0, desc="完了")
        return result_holder[0]

    except ValueError as e:
        return f"エラー: {e}"
    except Exception:
        return "文字起こし中にエラーが発生しました。"
    finally:
        try:
            if audio_path and os.path.isfile(audio_path):
                os.remove(audio_path)
        except OSError:
            pass


with gr.Blocks(title="文字起こし", theme=gr.themes.Base(), css=CSS) as demo:

    gr.HTML(HEADER_HTML)

    with gr.Tabs(selected=0):
        with gr.TabItem("ファイルアップロード", id=0):
            file_input = gr.File(
                type="filepath",
                label="音声・動画ファイル",
                file_types=sorted(ALLOWED_EXTENSIONS),
            )
            file_btn = gr.Button("文字起こしを開始", variant="primary", elem_id="btn-file")
            file_output = gr.Textbox(
                label="文字起こし結果",
                lines=12,
                placeholder="ここに文字起こし結果が表示されます",
                elem_id="out-file",
            )
            file_btn.click(fn=transcribe, inputs=file_input, outputs=file_output)

        with gr.TabItem("マイク録音", id=1):
            mic_enabled = gr.State(False)

            @gr.render(inputs=[mic_enabled])
            def mic_ui(enabled):
                if not enabled:
                    gr.HTML('<p class="mic-notice">録音を開始するとマイクへのアクセス許可を求めます</p>')
                    activate = gr.Button("録音を開始する", variant="secondary", elem_id="btn-mic-activate")
                    activate.click(fn=lambda: True, outputs=[mic_enabled])
                else:
                    mic = gr.Audio(sources=["microphone"], type="filepath", label="マイク録音")
                    run_btn = gr.Button("文字起こしを開始", variant="primary", elem_id="btn-mic")
                    out = gr.Textbox(
                        label="文字起こし結果",
                        lines=12,
                        placeholder="ここに文字起こし結果が表示されます",
                        elem_id="out-mic",
                    )
                    run_btn.click(fn=transcribe, inputs=mic, outputs=out)


if __name__ == "__main__":
    _cleanup_stale_gradio_files()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )
