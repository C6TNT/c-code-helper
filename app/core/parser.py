import re


KEYWORD_PATTERNS = {
    "if": r"\bif\s*\(",
    "else": r"\belse\b",
    "switch": r"\bswitch\s*\(",
    "for": r"\bfor\s*\(",
    "while": r"\bwhile\s*\(",
    "struct": r"\bstruct\b",
    "typedef": r"\btypedef\b",
    "enum": r"\benum\b",
    "static": r"\bstatic\b",
    "array": r"\[[^\]]*\]",
}


FUNC_DEF_PATTERN = re.compile(
    r"\b(?:void|char|int|float|double|bit|u8|u16|u32|unsigned|signed|static)\b[^\n;{}]*\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{"
)

VAR_PATTERN = re.compile(
    r"\b(?:bit|char|int|u8|u16|u32|float|double)\s+([A-Za-z_]\w*)"
)


def parse_code_features(code_text: str) -> dict:
    features = {
        "keywords": [],
        "functions": [],
        "variables": [],
        "line_count": 0,
        "non_empty_line_count": 0,
    }

    lines = code_text.splitlines()
    features["line_count"] = len(lines)
    features["non_empty_line_count"] = sum(1 for line in lines if line.strip())

    for key, pattern in KEYWORD_PATTERNS.items():
        if re.search(pattern, code_text):
            features["keywords"].append(key)

    seen_funcs = []
    for match in FUNC_DEF_PATTERN.finditer(code_text):
        name = match.group(1)
        if name not in seen_funcs:
            seen_funcs.append(name)
    features["functions"] = seen_funcs

    seen_vars = []
    for match in VAR_PATTERN.finditer(code_text):
        name = match.group(1)
        if name not in seen_vars:
            seen_vars.append(name)
    features["variables"] = seen_vars[:12]

    return features

