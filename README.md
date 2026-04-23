# ローカル文字起こしアプリ

音声・動画ファイルをローカルで文字起こしするアプリです。音声データは外部に送信されません。

---

## Mac版

### 1. 事前準備

```bash
# Homebrewのインストール確認
brew --version

# 未インストールの場合はインストール
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

```bash
# ffmpegのインストール確認
ffmpeg -version

# 未インストールの場合はインストール
brew install ffmpeg
```

```bash
# Pythonのインストール確認（3.9以上）
python3 --version

# 未インストールの場合はインストール
brew install python
```

### 2. セットアップ

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# パッケージのインストール
pip install -r requirements.txt
```

### 3. 起動

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
- `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'` → 以下で解決：
  ```bash
  pip install "huggingface_hub<1.0"
  ```

---

## Windows版

### 1. 事前準備

```powershell
# Pythonのインストール確認（3.9以上）
python --version

# 未インストールの場合はMicrosoft Storeからインストール
# または https://www.python.org/downloads/ からダウンロード
```

```powershell
# ffmpegのインストール確認
ffmpeg -version

# wingetでインストール（Windows 10以降）
winget install ffmpeg

# wingetが使えない場合は https://www.gyan.dev/ffmpeg/builds/ からzipをダウンロードし、
# C:\ffmpeg に展開後、環境変数PATHに C:\ffmpeg\bin を追加
```

### 2. セットアップ

```powershell
# 仮想環境の作成と有効化
python -m venv venv
venv\Scripts\activate

# パッケージのインストール
pip install -r requirements.txt
```

プロンプトの先頭に `(venv)` が表示されれば有効化成功です。

### 3. 起動

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
- スクリプトの実行が許可されていない → 以下を実行：
  ```powershell
  Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

## モデルサイズの変更

`transcribe_app_mac.py`（Mac）または `transcribe_app.py`（Windows）冒頭の `MODEL_SIZE` を変更します。

| 値 | サイズ | 1時間音声の処理時間（M1 CPU目安） | 精度 |
|----|--------|----------------------------------|------|
| `"small"` | 約500MB | 約20〜40分 | 実用レベル（デフォルト） |
| `"medium"` | 約1.5GB | 約1〜2時間 | 高精度 |
| `"large"` | 約3GB | 約3〜4時間 | 最高精度 |
