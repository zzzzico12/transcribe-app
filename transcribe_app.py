import gradio as gr
import whisper
import os
import tempfile
import threading
import time

MODEL_SIZE = "medium"
MAX_FILE_SIZE_MB = 2000
ALLOWED_EXTENSIONS = {
    ".mp3", ".mp4", ".wav", ".m4a", ".ogg", ".flac",
    ".aac", ".wma", ".mov", ".avi", ".mkv", ".webm",
}

CSS = """
.gradio-container {
    max-width: 780px !important;
    margin: 0 auto !important;
    padding: 2rem 1rem 4rem !important;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif !important;
}

footer { display: none !important; }

/* ヘッダー */
.app-header {
    text-align: center;
    padding: 2.25rem 1.5rem 2rem;
    background: linear-gradient(135deg, #ede9fe 0%, #dbeafe 100%);
    border-radius: 20px;
    border: 1px solid #c7d2fe;
    margin-bottom: 1.75rem;
}
.app-title {
    font-size: 2rem;
    font-weight: 700;
    color: #1e1b4b;
    margin: 0 0 0.4rem;
    letter-spacing: -0.03em;
}
.app-subtitle {
    color: #4338ca;
    font-size: 0.9rem;
    margin: 0 0 1.1rem;
}
.privacy-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: #ffffff;
    color: #15803d;
    border: 1px solid #86efac;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.3rem 0.9rem;
    border-radius: 9999px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    letter-spacing: 0.01em;
}

/* タブ */
.tab-nav {
    border-bottom: 2px solid #e2e8f0 !important;
    gap: 0 !important;
    background: transparent !important;
    margin-bottom: 1.5rem !important;
}
.tab-nav button {
    font-size: 0.9rem !important;
    font-weight: 500 !important;
    color: #64748b !important;
    border-radius: 0 !important;
    padding: 0.7rem 1.5rem !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    margin-bottom: -2px !important;
    transition: color 0.15s !important;
}
.tab-nav button:hover {
    color: #4f46e5 !important;
    background: transparent !important;
}
.tab-nav button.selected {
    color: #4f46e5 !important;
    font-weight: 600 !important;
    background: transparent !important;
    border-bottom: 2px solid #4f46e5 !important;
}

/* 入力ラベル */
.label-wrap span {
    font-size: 0.875rem !important;
    font-weight: 600 !important;
    color: #374151 !important;
    letter-spacing: 0.01em !important;
}

/* ボタン */
#btn-file, #btn-mic {
    background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%) !important;
    border: none !important;
    border-radius: 12px !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    letter-spacing: 0.01em !important;
    box-shadow: 0 2px 10px rgba(79, 70, 229, 0.35) !important;
    transition: all 0.2s ease !important;
    margin-top: 0.25rem !important;
}
#btn-file:hover, #btn-mic:hover {
    background: linear-gradient(135deg, #4338ca 0%, #4f46e5 100%) !important;
    box-shadow: 0 4px 16px rgba(79, 70, 229, 0.45) !important;
    transform: translateY(-1px) !important;
}
#btn-file:active, #btn-mic:active {
    transform: translateY(0) !important;
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3) !important;
}

/* 出力テキストエリア */
#out-file, #out-mic {
    border-radius: 12px !important;
    overflow: hidden !important;
}
#out-file textarea, #out-mic textarea {
    font-size: 0.95rem !important;
    line-height: 1.8 !important;
    color: #1e293b !important;
    background: #f8fafc !important;
    border: 1px solid #e2e8f0 !important;
    padding: 1rem 1.1rem !important;
    border-radius: 12px !important;
}
#out-file textarea:focus, #out-mic textarea:focus {
    border-color: #a5b4fc !important;
    box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1) !important;
}
"""


def _get_device():
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except Exception:
        pass
    return "cpu"


device = _get_device()
try:
    model = whisper.load_model(MODEL_SIZE, device=device)
except (NotImplementedError, RuntimeError):
    device = "cpu"
    model = whisper.load_model(MODEL_SIZE, device=device)
print(f"デバイス: {device}")


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


def transcribe(audio_path, progress=gr.Progress()):
    if audio_path is None:
        return "音声ファイルをアップロードするか、マイクで録音してください。"

    try:
        _validate_path(audio_path)
        _validate_file(audio_path)

        audio_array = whisper.load_audio(audio_path)
        duration_sec = len(audio_array) / whisper.audio.SAMPLE_RATE

        result_holder = [None]
        error_holder = [None]

        def run():
            try:
                result_holder[0] = model.transcribe(audio_path)
            except Exception as e:
                error_holder[0] = e

        thread = threading.Thread(target=run, daemon=True)
        thread.start()

        estimated_sec = duration_sec / 10 if device == "cuda" else duration_sec * 3
        start = time.time()

        while thread.is_alive():
            elapsed = time.time() - start
            frac = min(elapsed / estimated_sec, 0.95)
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            progress(frac, desc=f"文字起こし中... ({minutes}分{seconds}秒経過)")
            time.sleep(1)

        if error_holder[0]:
            raise error_holder[0]

        progress(1.0, desc="完了")
        return result_holder[0]["text"]

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


with gr.Blocks(title="ローカル文字起こしアプリ", theme=gr.themes.Soft(), css=CSS) as demo:

    gr.HTML("""
    <div class="app-header">
        <div class="privacy-badge">🔒 完全ローカル処理 &nbsp;|&nbsp; データ送信なし</div>
        <h1 class="app-title">🎙️ 文字起こしアプリ</h1>
        <p class="app-subtitle">音声・動画ファイルをアップロードするか、マイクで録音してください</p>
    </div>
    """)

    with gr.Tabs():
        with gr.TabItem("📁　ファイルアップロード"):
            file_input = gr.Audio(
                type="filepath",
                label="音声・動画ファイル",
            )
            file_btn = gr.Button(
                "✨　文字起こし開始",
                variant="primary",
                elem_id="btn-file",
            )
            file_output = gr.Textbox(
                label="文字起こし結果",
                lines=12,
                show_copy_button=True,
                placeholder="ここに文字起こし結果が表示されます...",
                elem_id="out-file",
            )
            file_btn.click(fn=transcribe, inputs=file_input, outputs=file_output)

        with gr.TabItem("🎤　マイク録音"):
            mic_input = gr.Audio(
                sources=["microphone"],
                type="filepath",
                label="マイク録音",
            )
            mic_btn = gr.Button(
                "✨　文字起こし開始",
                variant="primary",
                elem_id="btn-mic",
            )
            mic_output = gr.Textbox(
                label="文字起こし結果",
                lines=12,
                show_copy_button=True,
                placeholder="ここに文字起こし結果が表示されます...",
                elem_id="out-mic",
            )
            mic_btn.click(fn=transcribe, inputs=mic_input, outputs=mic_output)


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )
