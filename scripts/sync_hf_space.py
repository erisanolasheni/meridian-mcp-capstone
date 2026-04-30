#!/usr/bin/env python3
"""Stage the minimal Gradio app and upload to a Hugging Face Space (used by CI)."""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HF_README = ROOT / "docs" / "hf-space-README.md"

ARTIFACTS = (
    "app.py",
    "requirements.txt",
    "requirements-chatbot.txt",
    "meridian_chatbot",
)


def _stage() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="hf-space-"))
    for name in ARTIFACTS:
        src = ROOT / name
        dst = tmp / name
        if not src.exists():
            raise FileNotFoundError(f"Missing required path: {src}")
        if src.is_dir():
            shutil.copytree(
                src,
                dst,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store", "*.py[cod]"),
            )
        else:
            shutil.copy2(src, dst)
    shutil.copy2(HF_README, tmp / "README.md")
    return tmp


def main() -> None:
    repo_id = os.environ.get("HF_SPACE_REPO_ID", "").strip()
    if not repo_id:
        print("HF_SPACE_REPO_ID must be set (e.g. username/space-name).", file=sys.stderr)
        sys.exit(1)
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        print("HF_TOKEN must be set for upload.", file=sys.stderr)
        sys.exit(1)

    from huggingface_hub import HfApi

    folder = _stage()
    try:
        api = HfApi(token=token)
        sha = os.environ.get("GITHUB_SHA", "")
        msg = f"Deploy {sha[:7]}" if len(sha) >= 7 else "Deploy"
        api.upload_folder(
            folder_path=str(folder),
            repo_id=repo_id,
            repo_type="space",
            commit_message=msg,
        )
        print(f"Uploaded to https://huggingface.co/spaces/{repo_id}")
    finally:
        shutil.rmtree(folder, ignore_errors=True)


if __name__ == "__main__":
    main()
