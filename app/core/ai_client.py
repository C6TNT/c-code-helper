import json
import os
import re
import urllib.error
import urllib.request

try:
    from core.config_store import DEFAULT_BASE_URL, DEFAULT_MODEL, load_ai_config
except ModuleNotFoundError:
    from .config_store import DEFAULT_BASE_URL, DEFAULT_MODEL, load_ai_config


class AIClientError(Exception):
    pass


class AIConfigError(AIClientError):
    pass


class AIRequestError(AIClientError):
    pass


SYSTEM_PROMPT = """你是一个面向蓝桥杯单片机新生的 C 代码讲解助手。
你已经拿到了本地规则引擎整理好的结构化代码信息。
你的任务不是重复所有卡片内容，而是：
1. 用更像学长带着看的方式解释这段代码到底在干什么。
2. 结合当前代码片段，指出最值得先盯住的变量、函数或分支。
3. 提醒用户如果要改这段代码，最容易漏掉哪一层联动。
4. 输出尽量具体，不要泛泛而谈，不要把所有代码都讲成一个模板。
5. 不要编造不存在的函数、变量、文件或行号。
6. 如果信息不足，就明确说“目前只能判断到这一步”。

请固定按下面 3 段输出：
1. 这段代码更像在干什么
2. 你应该先盯住哪几个点
3. 如果你准备改它，最容易漏掉哪里

每一段尽量控制在 2 到 4 句内，直接说重点。
"""


SECTION_PATTERNS = {
    "what": [
        "1. 这段代码更像在干什么",
        "一、这段代码更像在干什么",
        "这段代码更像在干什么",
    ],
    "focus": [
        "2. 你应该先盯住哪几个点",
        "二、你应该先盯住哪几个点",
        "你应该先盯住哪几个点",
    ],
    "risk": [
        "3. 如果你准备改它，最容易漏掉哪里",
        "三、如果你准备改它，最容易漏掉哪里",
        "如果你准备改它，最容易漏掉哪里",
    ],
}


def get_runtime_ai_config() -> dict:
    file_config = load_ai_config()
    return {
        "api_key": file_config.get("api_key", "").strip() or os.getenv("OPENAI_API_KEY", "").strip(),
        "base_url": file_config.get("base_url", "").strip()
        or os.getenv("OPENAI_BASE_URL", DEFAULT_BASE_URL).strip()
        or DEFAULT_BASE_URL,
        "model": file_config.get("model", "").strip()
        or os.getenv("C_CODE_HELPER_OPENAI_MODEL", DEFAULT_MODEL).strip()
        or DEFAULT_MODEL,
    }


def ai_is_configured() -> bool:
    return bool(get_runtime_ai_config()["api_key"])


def _extract_output_text(response_data: dict) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    texts = []
    for item in response_data.get("output", []):
        for content in item.get("content", []):
            if "text" in content and isinstance(content["text"], str):
                texts.append(content["text"])
            elif "text" in content and isinstance(content["text"], dict):
                value = content["text"].get("value", "")
                if value:
                    texts.append(value)

    merged = "\n".join(part.strip() for part in texts if part.strip()).strip()
    if merged:
        return merged

    raise AIRequestError("AI 已返回结果，但当前版本没有成功解析出文本内容。")


def _normalize_heading(text: str) -> str:
    return re.sub(r"^[\s\-•*\d一二三四五六七八九十、.．()（）]+", "", text.strip())


NORMALIZED_SECTION_PATTERNS = {
    key: [_normalize_heading(pattern) for pattern in patterns]
    for key, patterns in SECTION_PATTERNS.items()
}

SECTION_REGEXES = {
    "what": re.compile(r"^\s*(1|一)[、.．)\]）]?\s*"),
    "focus": re.compile(r"^\s*(2|二)[、.．)\]）]?\s*"),
    "risk": re.compile(r"^\s*(3|三)[、.．)\]）]?\s*"),
}


def _split_ai_sections(raw_text: str) -> dict:
    sections = {"what": "", "focus": "", "risk": ""}
    current_key = ""

    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        normalized = _normalize_heading(stripped)
        matched_key = None

        for key, regex in SECTION_REGEXES.items():
            if regex.match(stripped):
                matched_key = key
                break

        if not matched_key:
            for key, patterns in NORMALIZED_SECTION_PATTERNS.items():
                for pattern in patterns:
                    if normalized.startswith(pattern):
                        matched_key = key
                        break
                if matched_key:
                    break

        if matched_key:
            current_key = matched_key
            content_after_title = stripped
            content_after_title = SECTION_REGEXES.get(matched_key, re.compile(r"$")).sub("", content_after_title, count=1).strip()
            for pattern in NORMALIZED_SECTION_PATTERNS[matched_key]:
                if _normalize_heading(content_after_title).startswith(pattern):
                    content_after_title = ""
                    break
            if content_after_title:
                sections[current_key] = content_after_title
            continue

        if current_key:
            if sections[current_key]:
                sections[current_key] += "\n" + stripped
            else:
                sections[current_key] = stripped

    return sections


def build_ai_cards(raw_text: str) -> dict:
    sections = _split_ai_sections(raw_text)
    return {
        "what": sections["what"].strip() or "AI 暂时没有单独提炼出这一段，建议先看完整结果。",
        "focus": sections["focus"].strip() or "AI 暂时没有明确列出重点，建议先盯住关键变量、关键函数和 if/switch 分支。",
        "risk": sections["risk"].strip() or "AI 暂时没有明确指出漏改点，建议先检查联动变量、调用链和相关文件。",
    }


def _format_ai_sections(raw_text: str) -> str:
    sections = build_ai_cards(raw_text)
    return (
        "AI 深入讲解结果\n\n"
        "1. 这段代码更像在干什么\n"
        f"{sections['what']}\n\n"
        "2. 你应该先盯住哪几个点\n"
        f"{sections['focus']}\n\n"
        "3. 如果你准备改它，最容易漏掉哪里\n"
        f"{sections['risk']}"
    )


def _post_json(path: str, body: dict) -> dict:
    config = get_runtime_ai_config()
    api_key = config["api_key"]
    if not api_key:
        raise AIConfigError("当前还没有在应用里配置 API Key。")

    base_url = config["base_url"].rstrip("/")
    req = urllib.request.Request(
        url=f"{base_url}/{path.lstrip('/')}",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise AIRequestError(f"AI 请求失败（HTTP {exc.code}）。\n\n{details}") from exc
    except urllib.error.URLError as exc:
        raise AIRequestError(f"AI 请求失败，网络不可用或服务不可达：{exc}") from exc
    except Exception as exc:
        raise AIRequestError(f"AI 请求过程中发生异常：{exc}") from exc


def test_ai_connection() -> str:
    config = get_runtime_ai_config()
    if not config["api_key"]:
        raise AIConfigError("当前还没有在应用里配置 API Key。")

    body = {
        "model": config["model"],
        "input": "Reply with OK only.",
        "text": {"verbosity": "low"},
        "reasoning": {"effort": "none"},
    }

    response_data = _post_json("responses", body)
    result_text = _extract_output_text(response_data)
    return (
        "AI 连接测试成功\n"
        f"Base URL：{config['base_url']}\n"
        f"Model：{config['model']}\n"
        f"返回结果：{result_text}"
    )


def build_ai_preview(payload_json: str) -> str:
    return (
        "AI 预览模式\n"
        "当前还没有配置 API Key，所以这里只显示将要发送给 AI 的结构化输入。\n\n"
        f"{payload_json}"
    )


def run_ai_explanation(payload_json: str) -> str:
    config = get_runtime_ai_config()
    if not config["api_key"]:
        return build_ai_preview(payload_json)

    body = {
        "model": config["model"],
        "instructions": SYSTEM_PROMPT,
        "input": "请根据下面结构化代码信息，给出适合蓝桥杯单片机新手的深入讲解。\n\n"
        f"{payload_json}",
        "text": {"verbosity": "low"},
        "reasoning": {"effort": "none"},
    }

    response_data = _post_json("responses", body)
    result = _extract_output_text(response_data)
    formatted_result = _format_ai_sections(result)
    return (
        f"AI 深入讲解\n"
        f"模型：{config['model']}\n"
        "说明：下面是基于本地规则分析 + 你提供的代码片段生成的辅助讲解，建议和右侧本地卡片一起看。\n\n"
        f"{formatted_result}"
    )
