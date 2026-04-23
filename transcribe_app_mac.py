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

        # MPS は CPU の約3倍速、CPU は音声の約3倍の時間がかかる
        estimated_sec = duration_sec / 3 if device == "mps" else duration_sec * 3
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


with gr.Blocks(title="ローカル文字起こしアプリ") as demo:
    gr.Markdown("# ローカル文字起こしアプリ")
    gr.Markdown("音声・動画ファイルをアップロードするか、マイクで録音してください。文字起こし結果はこの画面にのみ表示され、外部には送信されません。")

    with gr.Tab("ファイルアップロード"):
        file_input = gr.Audio(type="filepath", label="音声・動画ファイル")
        file_output = gr.Textbox(label="文字起こし結果", lines=10, show_copy_button=True)
        file_btn = gr.Button("文字起こし開始", variant="primary")
        file_btn.click(fn=transcribe, inputs=file_input, outputs=file_output)

    with gr.Tab("マイク録音"):
        mic_input = gr.Audio(sources=["microphone"], type="filepath", label="マイク録音")
        mic_output = gr.Textbox(label="文字起こし結果", lines=10, show_copy_button=True)
        mic_btn = gr.Button("文字起こし開始", variant="primary")
        mic_btn.click(fn=transcribe, inputs=mic_input, outputs=mic_output)


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
    )
