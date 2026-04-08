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

CALL_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\s*\(")
ASSIGN_PATTERN = re.compile(r"\b([A-Za-z_]\w*)\s*=")


SEMANTIC_RULES = [
    ("eeprom_write", ("AT24C02_WriteByte", "EEPROM_Write")),
    ("eeprom_read", ("AT24C02_ReadByte", "EEPROM_Read")),
    ("display_output", ("SEG_SetCode", "SEG_SetDigit", "SEG_SetDigitDp", "SEG_Clear")),
    ("key_read", ("Key_GetEvent", "Key_GetShortEvent", "Key_GetLongEvent", "Key_GetDoubleEvent")),
    ("key_handle", ("App_HandleKey",)),
    ("page_switch", ("PAGE_", "g_page", "page_mode")),
    ("param_save", ("App_SaveParam", "SaveParam")),
    ("param_load", ("App_LoadParam", "LoadParam")),
    ("param_edit", ("g_param", "param_mode", "limit", "threshold")),
    ("temp_sample", ("DS18B20", "temp10", "temperature")),
    ("rtc_sample", ("DS1302", "rtc", "clock")),
    ("adc_sample", ("PCF8591", "adc", "light", "pot")),
    ("freq_sample", ("FREQ_", "freq_hz", "NE555")),
    ("distance_sample", ("distance_cm", "Ultrasonic", "dist")),
    ("uart_io", ("UART_", "uart")),
    ("alarm_output", ("g_alarm", "Alarm", "beep", "relay", "led")),
]


def parse_code_features(code_text: str) -> dict:
    features = {
        "keywords": [],
        "functions": [],
        "variables": [],
        "calls": [],
        "assignments": [],
        "semantic_tags": [],
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

    seen_calls = []
    for match in CALL_PATTERN.finditer(code_text):
        name = match.group(1)
        if name in ("if", "for", "while", "switch", "return", "sizeof"):
            continue
        if name not in seen_calls:
            seen_calls.append(name)
    features["calls"] = seen_calls[:16]

    seen_assignments = []
    for match in ASSIGN_PATTERN.finditer(code_text):
        name = match.group(1)
        if name not in seen_assignments:
            seen_assignments.append(name)
    features["assignments"] = seen_assignments[:12]

    joined = " ".join(
        features["functions"]
        + features["variables"]
        + features["calls"]
        + features["assignments"]
    )
    for tag, tokens in SEMANTIC_RULES:
        if any(token in joined for token in tokens):
            features["semantic_tags"].append(tag)

    return features
