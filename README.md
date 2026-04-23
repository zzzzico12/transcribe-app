# ローカル文字起こしアプリ

音声・動画ファイルをローカルで文字起こしするアプリです。音声データは外部に送信されません。

---

## Mac版

### 事前準備

```bash
# Homebrew（未インストールの場合）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ffmpeg（未インストールの場合）
brew install ffmpeg
```

### セットアップ

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# パッケージのインストール
pip install -r requirements.txt
```

### 起動

```bash
source venv/bin/activate
python3 transcribe_app_mac.py
```

ブラウザで http://127.0.0.1:7860 にアクセス。

### トラブルシューティング（Mac）

- `ffmpeg が見つかりません` → `brew install ffmpeg`
- `No module named 'whisper'` → `source venv/bin/activate` で仮想環境を有効化
- ポート7860が使用中 → `server_port=7860` を別の番号（例: 7861）に変更
- M1/M2/M3でエラー → `pip install torch torchvision torchaudio` を再実行
- `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'` → `huggingface_hub` の新しいバージョンで削除されたクラスを `gradio` が参照するため発生。以下で解決：
  ```bash
  pip install "huggingface_hub<1.0"
  ```

---

## Windows版

### 事前準備

以下がインストールされているか確認し、不足していれば導入してください。

- Python 3.9以上（`python --version` で確認）
- pip（`pip --version` で確認）
- ffmpeg（`ffmpeg -version` で確認）
  - 未インストールの場合: https://www.gyan.dev/ffmpeg/builds/ からzipをダウンロードし、`C:\ffmpeg` に展開、環境変数PATHに `C:\ffmpeg\bin` を追加

### セットアップ

PowerShellまたはコマンドプロンプトで実行：

```powershell
# 仮想環境の作成と有効化
python -m venv venv
venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt
```

プロンプトの先頭に `(venv)` が表示されれば有効化成功です。

### 起動

```powershell
venv\Scripts\activate
python transcribe_app.py
```

ブラウザで http://127.0.0.1:7860 にアクセス。

### GPU対応（NVIDIA）

NVIDIA製GPUがある場合、CUDAを使って高速処理できます。

```powershell
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

起動時に `デバイス: cuda` と表示されれば有効化成功です。

### トラブルシューティング（Windows）

- `ffmpeg が見つかりません` → 環境変数PATHの設定を確認
- `No module named 'whisper'` → `venv\Scripts\activate` で仮想環境を有効化
- ポート7860が使用中 → `server_port=7860` を別の番号（例: 7861）に変更
- スクリプトの実行が許可されていない → PowerShellで `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` を実行

---

## モデルサイズの変更

`transcribe_app_mac.py`（Mac）または `transcribe_app.py`（Windows）冒頭の `MODEL_SIZE` を変更します。

| 値 | サイズ | 速度 | 精度 |
|----|--------|------|------|
| `"small"` | 約500MB | 速い | 普通 |
| `"medium"` | 約1.5GB | 普通 | 良好（デフォルト） |
| `"large"` | 約3GB | 遅い | 最高 |
