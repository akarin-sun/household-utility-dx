# Household Utility DX

光熱費自動化ガイド（Web）と、日々の自動化スクリプトをまとめたリポジトリです。

---

## 自動化スクリプト（Mac mini M4）

### 1. デスクトップ画像のアーカイブ — **Mac mini M4 初の自動化**

| ファイル | 説明 |
|----------|------|
| `archive_desktop_images.py` | デスクトップ直下の PNG/JPG を、`Inspiration_Vault/Archive_日付` に自動移動 |

**実行例**
```bash
python3 archive_desktop_images.py
```

**保存先**: `/Users/kana/Desktop/Inspiration_Vault/Archive_YYYY-MM-DD/`

---

### 2. 電気代請求書画像の情報抽出（Gemini 連携）

| ファイル | 説明 |
|----------|------|
| `extract_electric_bill.py` | フォルダ内の請求書画像（PNG/JPG/HEIC）を Gemini API で解析し、使用期間・使用量・請求金額を JSON で出力 |

**必要なライブラリのインストール**
```bash
cd /Users/kana/Desktop/Household-DX/household-utility-dx
pip3 install -r requirements-electric-bill.txt
```

| ライブラリ | 用途 |
|------------|------|
| Pillow | 画像読み込み |
| pillow-heif | iPhone の HEIC 形式を自動変換・読み込み |
| google-generativeai | Gemini API（1.5 Pro 等）連携 |

**API キー**  
環境変数 `GEMINI_API_KEY` を設定するか、実行時に `--api-key` で指定。

**実行例**
```bash
# カレントディレクトリの画像を処理
python3 extract_electric_bill.py

# 指定フォルダ（Google ドライブのローカルパス可）
python3 extract_electric_bill.py "/Users/kana/Library/CloudStorage/Google Drive/My Drive/電気代"

# 結果を JSON ファイルに保存
python3 extract_electric_bill.py ./請求書画像 -o result.json
```

**出力**  
スプレッドシートに入れやすい JSON 配列（使用期間開始・終了、使用量_kWh、請求金額_円）。

---

## ガイド（Web）

- **index.html** — Google Apps Script × Gemini API で実現する光熱費自動化・分析システムの導入ガイド（あかりん名刺ブランド連動デザイン）

ブラウザで `index.html` を開いて閲覧できます。
