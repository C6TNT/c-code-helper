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
VAR_PATTERN = re.compile(r"\b(?:bit|char|int|u8|u16|u32|float|double)\s+([A-Za-z_]\w*)")
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


INTERFACE_PATTERNS = {
    "EEPROM": ("AT24C02_WriteByte", "AT24C02_ReadByte", "EEPROM_Write", "EEPROM_Read"),
    "数码管": ("SEG_SetCode", "SEG_SetDigit", "SEG_SetDigitDp", "SEG_Clear"),
    "按键": ("Key_GetEvent", "Key_GetShortEvent", "Key_GetLongEvent", "Key_GetDoubleEvent"),
    "温度传感器": ("DS18B20",),
    "时钟芯片": ("DS1302",),
    "ADC/DAC": ("PCF8591",),
    "频率测量": ("FREQ_", "freq_hz", "NE555"),
    "超声波": ("Ultrasonic", "distance_cm", "dist"),
    "串口": ("UART_", "uart"),
    "LED/继电器/蜂鸣器": ("led", "relay", "beep", "alarm"),
}


def _unique_items(items: list[str], limit: int) -> list[str]:
    seen = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen[:limit]


def parse_code_features(code_text: str) -> dict:
    features = {
        "keywords": [],
        "functions": [],
        "variables": [],
        "calls": [],
        "assignments": [],
        "semantic_tags": [],
        "interfaces": [],
        "line_count": 0,
        "non_empty_line_count": 0,
    }

    lines = code_text.splitlines()
    features["line_count"] = len(lines)
    features["non_empty_line_count"] = sum(1 for line in lines if line.strip())

    for key, pattern in KEYWORD_PATTERNS.items():
        if re.search(pattern, code_text):
            features["keywords"].append(key)

    functions = [match.group(1) for match in FUNC_DEF_PATTERN.finditer(code_text)]
    variables = [match.group(1) for match in VAR_PATTERN.finditer(code_text)]
    calls = []
    for match in CALL_PATTERN.finditer(code_text):
        name = match.group(1)
        if name in ("if", "for", "while", "switch", "return", "sizeof"):
            continue
        calls.append(name)
    assignments = [match.group(1) for match in ASSIGN_PATTERN.finditer(code_text)]

    features["functions"] = _unique_items(functions, 8)
    features["variables"] = _unique_items(variables, 14)
    features["calls"] = _unique_items(calls, 20)
    features["assignments"] = _unique_items(assignments, 14)

    joined = " ".join(
        features["functions"]
        + features["variables"]
        + features["calls"]
        + features["assignments"]
    )
    joined_lower = joined.lower()

    for tag, tokens in SEMANTIC_RULES:
        if any(token in joined for token in tokens):
            features["semantic_tags"].append(tag)

    for label, tokens in INTERFACE_PATTERNS.items():
        if any(token.lower() in joined_lower for token in tokens):
            features["interfaces"].append(label)

    return features
