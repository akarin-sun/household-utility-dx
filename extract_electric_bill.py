#!/usr/bin/env python3
"""
電気代請求書画像から、Gemini API で情報を抽出し JSON で出力するスクリプト。
HEIC（iPhone）対応・Gemini 1.5 Pro 連携・スプレッドシート用 JSON。
Mac mini M4（あかりん基地）用・シンプルで確実な実装。

必要なライブラリのインストール:
  pip3 install -r requirements-electric-bill.txt
  または:
  pip3 install Pillow pillow-heif google-generativeai

API キー: 環境変数 GEMINI_API_KEY を設定するか --api-key で指定。
"""

import argparse
import base64
import json
import os
import re
import sys
from io import BytesIO
from pathlib import Path
from typing import Optional

# HEIC 対応のため、Pillow の前に pillow-heif を登録
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass  # HEIC 以外ならそのまま

from PIL import Image

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# 対象拡張子
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".heic", ".heif"}

EXTRACT_PROMPT = """この画像は電気料金の請求書（または領収書）です。
次の3項目だけを抽出し、**JSON のみ**で答えてください。説明文は不要です。

- 使用期間開始（日付）: YYYY-MM-DD 形式
- 使用期間終了（日付）: YYYY-MM-DD 形式
- 使用量（kWh）: 数値のみ
- 請求金額（円）: 数値のみ（円マークやカンマは除く）

出力形式（このキー名で必ず出力すること）:
{"使用期間開始": "YYYY-MM-DD", "使用期間終了": "YYYY-MM-DD", "使用量_kWh": 数値, "請求金額_円": 数値}

読み取れない項目は null にしてください。"""


def load_image_as_png_bytes(path: Path) -> bytes:
    """画像を開き（HEIC 対応）、PNG バイト列で返す"""
    with Image.open(path) as img:
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()


def extract_json_from_response(text: str) -> Optional[dict]:
    """応答テキストから JSON ブロックを1つ取り出す"""
    # コードブロックがあればその中身
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
    if m:
        try:
            return json.loads(m.group(1).strip())
        except json.JSONDecodeError:
            pass
    # そのまま {} のブロックを探す
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    return None


def extract_from_image_path(
    path: Path,
    model,
) -> dict:
    """1枚の画像を Gemini に送り、抽出結果の dict を返す"""
    png_bytes = load_image_as_png_bytes(path)
    # SDK が受け取る形式（base64 または bytes は実装依存のため両対応）
    try:
        image_part = genai.types.Part.from_bytes(data=png_bytes, mime_type="image/png")
    except (AttributeError, TypeError):
        image_part = {
            "inline_data": {
                "mime_type": "image/png",
                "data": base64.b64encode(png_bytes).decode("ascii"),
            }
        }
    response = model.generate_content([EXTRACT_PROMPT, image_part])
    if not response or not response.text:
        return {"_file": path.name, "_error": "空の応答"}
    raw = response.text.strip()
    out = extract_json_from_response(raw)
    if out is None:
        return {"_file": path.name, "_raw": raw[:200], "_error": "JSON 解析失敗"}
    out["_file"] = path.name
    return out


def main():
    parser = argparse.ArgumentParser(
        description="電気代請求書画像から使用期間・使用量・請求金額を抽出し JSON で出力"
    )
    parser.add_argument(
        "folder",
        nargs="?",
        default=".",
        help="画像が入ったフォルダ（Google ドライブのローカルパスや任意のパス）",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("GEMINI_API_KEY"),
        help="Gemini API キー（未指定時は環境変数 GEMINI_API_KEY）",
    )
    parser.add_argument(
        "--model",
        default="gemini-1.5-flash-latest",
        help="使用する Gemini モデル（例: gemini-1.5-flash-latest, gemini-1.5-flash, gemini-2.0-flash-lite-preview-02-05）",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="利用可能なモデル一覧を表示して終了",
    )
    parser.add_argument(
        "-o", "--output",
        help="結果を書き出す JSON ファイルパス（未指定時は標準出力のみ）",
    )
    args = parser.parse_args()

    if not args.api_key:
        print("エラー: API キーがありません。--api-key を指定するか GEMINI_API_KEY を設定してください。", file=sys.stderr)
        return 1

    if genai is None:
        print("エラー: google-generativeai がインストールされていません。pip install google-generativeai", file=sys.stderr)
        return 1

    genai.configure(api_key=args.api_key)

    # モデル一覧表示
    if args.list_models:
        try:
            models = genai.list_models()
            print("利用可能な Gemini モデル:\n")
            for m in models:
                if "generateContent" in m.supported_generation_methods:
                    print(f"  {m.name}")
            return 0
        except Exception as e:
            print(f"エラー: モデル一覧の取得に失敗しました: {e}", file=sys.stderr)
            return 1

    folder = Path(args.folder).resolve()
    if not folder.is_dir():
        print(f"エラー: フォルダが見つかりません: {folder}", file=sys.stderr)
        return 1

    image_paths = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in IMAGE_EXTENSIONS
    ]
    image_paths.sort(key=lambda p: p.name)

    if not image_paths:
        print(f"エラー: 画像ファイル（{', '.join(IMAGE_EXTENSIONS)}）がありません: {folder}", file=sys.stderr)
        return 1

    # モデル名から models/ プレフィックスを削除（あれば）
    model_name = args.model
    if model_name.startswith("models/"):
        model_name = model_name.replace("models/", "", 1)
    
    try:
        model = genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"エラー: モデル '{model_name}' が見つかりません: {e}", file=sys.stderr)
        print(f"ヒント: --list-models で利用可能なモデルを確認できます", file=sys.stderr)
        return 1

    results = []
    for path in image_paths:
        try:
            row = extract_from_image_path(path, model)
            results.append(row)
        except Exception as e:
            results.append({"_file": path.name, "_error": str(e)})

    json_str = json.dumps(results, ensure_ascii=False, indent=2)
    print(json_str)

    if args.output:
        Path(args.output).write_text(json_str, encoding="utf-8")
        print(f"\n→ 保存しました: {args.output}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
