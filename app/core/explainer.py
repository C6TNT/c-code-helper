def build_syntax_summary(features: dict) -> list[str]:
    keys = set(features.get("keywords", []))
    summary = []

    if "typedef" in keys and "struct" in keys:
        summary.append("这段代码里出现了 typedef struct，通常是在定义一个结构体类型，用来把一组相关数据打包在一起。")
    elif "struct" in keys:
        summary.append("这段代码里出现了 struct，通常是在把多个相关变量整理成一个整体。")

    if "enum" in keys:
        summary.append("这段代码里出现了 enum，通常用来表示页面编号、状态编号或模式编号。")

    if "if" in keys or "else" in keys:
        summary.append("这段代码里出现了 if/else，通常是在做条件判断，比如判断按键、报警条件或页面状态。")

    if "switch" in keys:
        summary.append("这段代码里出现了 switch/case，通常是在做多页面切换、多模式分支或按键功能分发。")

    if "for" in keys or "while" in keys:
        summary.append("这段代码里出现了循环，通常是在处理数组、逐位显示或重复执行某类逻辑。")

    if "static" in keys:
        summary.append("这段代码里出现了 static，通常表示这个变量或函数只在当前文件内使用，或者需要保存上一次的状态。")

    if "array" in keys:
        summary.append("这段代码里出现了数组写法，通常是在保存一组显示数据、历史数据或缓冲区内容。")

    if not summary:
        summary.append("这段代码没有出现太多复杂语法，更像是普通变量处理或函数调用逻辑。")

    return summary


def build_reading_steps(features: dict) -> list[str]:
    steps = []

    if features.get("variables"):
        steps.append("先看变量名，判断这些变量是在存参数、实时数据、页面状态，还是输出状态。")

    if features.get("functions"):
        steps.append("再看函数名，先猜这个函数大概是显示、按键、参数、采样还是报警。")

    keys = set(features.get("keywords", []))
    if "if" in keys or "switch" in keys:
        steps.append("然后重点看判断语句，通常真正的题目逻辑就藏在 if 或 switch 里面。")

    if "for" in keys or "while" in keys:
        steps.append("如果出现循环，再看它是在遍历数组，还是在重复处理多个显示位。")

    steps.append("最后再看函数调用，把这段代码和页面显示、按键处理、数据采样这些题目要求对应起来。")
    return steps


def build_code_explanation(features: dict, scene: str) -> str:
    functions = features.get("functions", [])
    variables = features.get("variables", [])

    parts = [
        f"这段代码一共大约有 {features.get('non_empty_line_count', 0)} 行有效代码。",
        f"从名字和语法特征看，它{scene}。",
    ]

    if functions:
        parts.append("识别到的主要函数有：" + "、".join(functions[:6]) + "。")

    if variables:
        parts.append("识别到的主要变量有：" + "、".join(variables[:8]) + "。")

    parts.append("建议先不要逐行死抠，而是先分清这段代码属于页面、按键、参数、采样还是输出控制。")
    return "\n".join(parts)

