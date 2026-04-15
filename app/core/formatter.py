def _bullet_join(items: list[str]) -> str:
    if not items:
        return "- 暂未识别到明显内容"
    return "\n".join(f"- {item}" for item in items)


def _number_join(items: list[str]) -> str:
    if not items:
        return "1. 暂未识别到明显内容"
    return "\n".join(f"{idx + 1}. {item}" for idx, item in enumerate(items))


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
    dependency_hints: list[str],
    related_function_hints: list[str],
    impact_hints: list[str],
    execution_chain: list[str],
) -> dict:
    return {
        "scene": scene,
        "requirement_text": requirement_text,
        "summary_text": _bullet_join(syntax_summary),
        "term_text": _bullet_join(term_explanations),
        "modify_hint_text": _bullet_join(modify_hints),
        "action_text": _bullet_join(specific_actions),
        "dependency_text": _bullet_join(dependency_hints),
        "related_function_text": _bullet_join(related_function_hints),
        "impact_text": _bullet_join(impact_hints),
        "execution_chain_text": _number_join(execution_chain),
        "reading_steps_text": _number_join(steps),
        "explanation_text": explanation,
        "feature_text": (
            f"有效代码行数：{features.get('non_empty_line_count', 0)}\n"
            f"识别到的函数：{', '.join(features.get('functions', [])) or '暂未明显识别到'}\n"
            f"识别到的变量：{', '.join(features.get('variables', [])) or '暂未明显识别到'}\n"
            f"识别到的调用：{', '.join(features.get('calls', [])) or '暂未明显识别到'}\n"
            f"识别到的被修改变量：{', '.join(features.get('assignments', [])) or '暂未明显识别到'}\n"
            f"识别到的外设接口：{', '.join(features.get('interfaces', [])) or '暂未明显识别到'}\n"
            f"识别到的语法：{', '.join(features.get('keywords', [])) or '暂未明显识别到'}"
        ),
    }
