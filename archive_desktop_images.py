#!/usr/bin/env python3
"""
デスクトップの画像（PNG / JPG）を Inspiration_Vault/Archive_日付 に自動移動するスクリプト
Mac mini M4 などで実行するたびに、デスクトップ直下の画像を Inspiration_Vault 内のその日のフォルダに整理します。

使い方:
  python3 archive_desktop_images.py
  # または
  chmod +x archive_desktop_images.py && ./archive_desktop_images.py

自動実行（例: 毎日 18:00）:
  launchd で登録するか、cron で "0 18 * * * cd /path/to/dir && python3 archive_desktop_images.py"
"""

import shutil
from pathlib import Path
from datetime import datetime

# 対象拡張子（小文字で比較）
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg"}

# アーカイブの保存先ベース（Inspiration_Vault 内に Archive_日付 を作る）
VAULT_BASE = Path("/Users/kana/Desktop/Inspiration_Vault")

def get_desktop_path() -> Path:
    """ユーザーのデスクトップパスを返す"""
    return Path.home() / "Desktop"

def get_archive_folder_name() -> str:
    """今日の日付を使ったアーカイブフォルダ名を返す（例: Archive_2026-02-17）"""
    return f"Archive_{datetime.now().strftime('%Y-%m-%d')}"

def main():
    desktop = get_desktop_path()
    if not desktop.exists():
        print(f"エラー: デスクトップが見つかりません ({desktop})")
        return 1

    archive_name = get_archive_folder_name()
    archive_path = VAULT_BASE / archive_name
    archive_path.parent.mkdir(parents=True, exist_ok=True)  # Inspiration_Vault がなければ作成
    archive_path.mkdir(exist_ok=True)

    moved_count = 0
    for path in desktop.iterdir():
        if not path.is_file():
            continue
        if path.suffix.lower() in IMAGE_EXTENSIONS:
            dest = archive_path / path.name
            if dest.exists():
                # 同名ファイルがある場合は連番を付ける
                stem, suffix = path.stem, path.suffix
                n = 1
                while dest.exists():
                    dest = archive_path / f"{stem}_{n}{suffix}"
                    n += 1
            try:
                shutil.move(str(path), str(dest))
                print(f"移動: {path.name} → Inspiration_Vault/{archive_name}/")
                moved_count += 1
            except OSError as e:
                print(f"失敗: {path.name} - {e}")

    if moved_count == 0:
        print(f"移動する画像はありませんでした。（Inspiration_Vault/{archive_name} は用意済み）")
    else:
        print(f"完了: {moved_count} 件を Inspiration_Vault/{archive_name} に移動しました。")
    return 0

if __name__ == "__main__":
    exit(main())
