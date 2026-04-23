# ローカル文字起こしアプリ（Mac版）

音声・動画ファイルをローカルで文字起こしするアプリです。音声データは外部に送信されません。

## 事前準備

```bash
# Homebrew（未インストールの場合）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# ffmpeg（未インストールの場合）
brew install ffmpeg
```

## セットアップ

```bash
# 仮想環境の作成と有効化
python3 -m venv venv
source venv/bin/activate

# パッケージのインストール
pip install -r requirements.txt
```

## 起動

```bash
source venv/bin/activate
python3 transcribe_app_mac.py
```

ブラウザで http://127.0.0.1:7860 にアクセス。

## モデルサイズの変更

`transcribe_app_mac.py` 冒頭の `MODEL_SIZE` を変更します。

| 値 | サイズ | 速度 | 精度 |
|----|--------|------|------|
| `"small"` | 約500MB | 速い | 普通 |
| `"medium"` | 約1.5GB | 普通 | 良好（デフォルト） |
| `"large"` | 約3GB | 遅い | 最高 |

## トラブルシューティング

- `ffmpeg が見つかりません` → `brew install ffmpeg`
- `No module named 'whisper'` → `source venv/bin/activate` で仮想環境を有効化
- ポート7860が使用中 → `server_port=7860` を別の番号（例: 7861）に変更
- M1/M2/M3でエラー → `pip install torch torchvision torchaudio` を再実行
- `ImportError: cannot import name 'HfFolder' from 'huggingface_hub'` → `huggingface_hub` の新しいバージョンで削除されたクラスを `gradio` が参照するため発生。以下で解決：
  ```bash
  pip install "huggingface_hub<1.0"
  ```
