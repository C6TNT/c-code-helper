from app.core.classifier import classify_code_scene
from app.core.explainer import (
    build_code_explanation,
    build_reading_steps,
    build_syntax_summary,
    build_term_explanations,
)
from app.core.formatter import format_result
from app.core.parser import parse_code_features


def analyze_code(code_text: str) -> dict:
    if not code_text.strip():
        raise ValueError("请先粘贴一段 C 代码，再开始分析。")

    features = parse_code_features(code_text)
    scene = classify_code_scene(features)
    syntax_summary = build_syntax_summary(features)
    term_explanations = build_term_explanations(features)
    steps = build_reading_steps(features)
    explanation = build_code_explanation(features, scene)
    return format_result(features, scene, syntax_summary, steps, explanation, term_explanations)
