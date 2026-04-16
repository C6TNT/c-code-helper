import json
import sys
from pathlib import Path


DEFAULT_BASE_URL = "https://api-inference.modelscope.cn/v1"
DEFAULT_MODEL = "Qwen/Qwen3.5-35B-A3B"


def get_app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


def get_config_path() -> Path:
    return get_app_root() / "config.json"


def load_ai_config() -> dict:
    path = get_config_path()
    default_data = {
        "api_key": "",
        "base_url": DEFAULT_BASE_URL,
        "model": DEFAULT_MODEL,
    }

    if not path.exists():
        return default_data

    try:
        with path.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
    except Exception:
        return default_data

    return {
        "api_key": str(data.get("api_key", "")).strip(),
        "base_url": str(data.get("base_url", DEFAULT_BASE_URL)).strip() or DEFAULT_BASE_URL,
        "model": str(data.get("model", DEFAULT_MODEL)).strip() or DEFAULT_MODEL,
    }


def save_ai_config(api_key: str, base_url: str, model: str) -> Path:
    path = get_config_path()
    data = {
        "api_key": api_key.strip(),
        "base_url": base_url.strip() or DEFAULT_BASE_URL,
        "model": model.strip() or DEFAULT_MODEL,
    }
    with path.open("w", encoding="utf-8") as file_obj:
        json.dump(data, file_obj, ensure_ascii=False, indent=2)
    return path


def mask_api_key(api_key: str) -> str:
    text = api_key.strip()
    if not text:
        return "未配置"
    if len(text) <= 8:
        return "*" * len(text)
    return f"{text[:4]}***{text[-4:]}"
