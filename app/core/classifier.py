def classify_code_scene(features: dict) -> str:
    tags = set(features.get("semantic_tags", []))
    text_keys = set(features.get("keywords", []))
    joined = " ".join(
        features.get("functions", [])
        + features.get("variables", [])
        + features.get("calls", [])
        + features.get("assignments", [])
    ).lower()

    if "display_output" in tags:
        return "更像页面显示逻辑"

    if "key_read" in tags or "key_handle" in tags or "key" in joined:
        return "更像按键处理逻辑"

    if "param_save" in tags or "param_load" in tags or "param_edit" in tags:
        return "更像参数设置逻辑"

    if "alarm_output" in tags:
        return "更像报警或输出控制逻辑"

    if {
        "temp_sample",
        "rtc_sample",
        "adc_sample",
        "freq_sample",
        "distance_sample",
        "uart_io",
        "eeprom_write",
        "eeprom_read",
    } & tags:
        return "更像数据采样或数据处理逻辑"

    if "switch" in text_keys or "if" in text_keys:
        return "更像业务判断逻辑"

    return "更像通用业务代码"


def map_scene_to_requirement(scene: str) -> str:
    mapping = {
        "更像页面显示逻辑": "这段代码更像在完成赛题里的“数码管显示”或“页面显示格式”要求。",
        "更像按键处理逻辑": "这段代码更像在完成赛题里的“按键切换页面”“按键改参数”或“按键触发功能”要求。",
        "更像参数设置逻辑": "这段代码更像在完成赛题里的“参数设置”“阈值调整”“范围限制”要求。",
        "更像报警或输出控制逻辑": "这段代码更像在完成赛题里的“LED 指示”“继电器控制”“蜂鸣器报警”要求。",
        "更像数据采样或数据处理逻辑": "这段代码更像在完成赛题里的“温度读取”“ADC 采样”“频率测量”“距离测量”要求。",
        "更像业务判断逻辑": "这段代码更像在完成赛题里的“状态判断”“模式切换”“多条件分支”要求。",
        "更像通用业务代码": "这段代码更像基础业务层代码，通常是在给页面、按键、参数或采样逻辑做支撑。",
    }
    return mapping.get(scene, "这段代码更像基础业务代码，需要结合变量名和函数名继续判断它对应的题目要求。")
