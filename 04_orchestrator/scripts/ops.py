#!/usr/bin/env python3
"""Unified CLI entry point for Marketing Ops Agent."""

import sys
from pathlib import Path

# モジュール検索パスにリポジトリルートおよびカレントモジュールを追加
current_dir = Path(__file__).resolve().parent
module_dir = current_dir.parent
repo_root = module_dir.parent

if str(module_dir) not in sys.path:
    sys.path.insert(0, str(module_dir))
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from src.cli import main

if __name__ == "__main__":
    main()
