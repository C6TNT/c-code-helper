def classify_code_scene(features: dict) -> str:
    text_keys = set(features.get("keywords", []))
    functions = features.get("functions", [])
    variables = features.get("variables", [])
    joined = " ".join(functions + variables).lower()

    if "seg_" in joined or "show" in joined or "display" in joined:
        return "更像页面显示逻辑"

    if "key" in joined:
        return "更像按键处理逻辑"

    if "param" in joined or "field" in joined:
        return "更像参数设置逻辑"

    if "alarm" in joined or "relay" in joined or "led" in joined or "beep" in joined:
        return "更像报警或输出控制逻辑"

    if "temp" in joined or "freq" in joined or "adc" in joined or "dist" in joined or "uart" in joined:
        return "更像数据采样或数据处理逻辑"

    if "switch" in text_keys or "if" in text_keys:
        return "更像业务判断逻辑"

    return "更像通用业务代码"

