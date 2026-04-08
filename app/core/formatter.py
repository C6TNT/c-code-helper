def format_result(
    features: dict,
    scene: str,
    requirement_text: str,
    syntax_summary: list[str],
    steps: list[str],
    explanation: str,
    term_explanations: list[str],
    modify_hints: list[str],
    specific_actions: list[str],
) -> dict:
    return {
        "scene": scene,
        "requirement_text": requirement_text,
        "summary_text": "\n".join(f"- {item}" for item in syntax_summary),
        "term_text": "\n".join(f"- {item}" for item in term_explanations),
        "modify_hint_text": "\n".join(f"- {item}" for item in modify_hints),
        "action_text": "\n".join(f"- {item}" for item in specific_actions),
        "reading_steps_text": "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(steps)),
        "explanation_text": explanation,
        "feature_text": (
            f"有效代码行数：{features.get('non_empty_line_count', 0)}\n"
            f"识别到的函数：{', '.join(features.get('functions', [])) or '未明显识别到'}\n"
            f"识别到的变量：{', '.join(features.get('variables', [])) or '未明显识别到'}\n"
            f"识别到的调用：{', '.join(features.get('calls', [])) or '未明显识别到'}\n"
            f"识别到的被修改变量：{', '.join(features.get('assignments', [])) or '未明显识别到'}\n"
            f"识别到的语法：{', '.join(features.get('keywords', [])) or '未明显识别到'}"
        ),
    }
