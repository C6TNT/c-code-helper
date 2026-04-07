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


def build_term_explanations(features: dict) -> list[str]:
    keys = set(features.get("keywords", []))
    variables = [item.lower() for item in features.get("variables", [])]
    functions = [item.lower() for item in features.get("functions", [])]
    joined = " ".join(variables + functions)
    result = []

    if "static" in keys:
        result.append("static：通常表示这个变量或函数只在当前文件内使用，或者需要把上一次的值保留下来。")

    if "typedef" in keys and "struct" in keys:
        result.append("typedef struct：通常是在定义一个“数据包”，方便把一组相关变量放在一起。")
    elif "struct" in keys:
        result.append("struct：通常是在把多个相关变量打包成一个整体。")

    if "enum" in keys:
        result.append("enum：通常是在定义页面编号、状态编号或模式编号，让代码比直接写数字更清楚。")

    if any(token in joined for token in ("u8", "u16", "u32")):
        result.append("u8 / u16 / u32：是单片机里常见的整型别名，分别可以理解成 8 位、16 位、32 位无符号整数。")

    if any(token in joined for token in ("bit",)):
        result.append("bit：是 51 单片机里常见的位变量，通常只用来表示开关状态。")

    if "array" in keys:
        result.append("数组：通常是在保存一组显示数据、历史数据或缓冲区内容。")

    if "if" in keys:
        result.append("if：通常是在做条件判断，比如判断按键、页面、报警条件或阈值。")

    if "switch" in keys:
        result.append("switch：通常是在做多页面切换、多模式切换或多按键分发。")

    if not result:
        result.append("这段代码里暂时没有识别到特别典型的术语，先按变量、函数、判断语句的顺序看就可以。")

    return result


def build_modify_hints(features: dict, scene: str) -> list[str]:
    variables = features.get("variables", [])
    functions = features.get("functions", [])
    joined = " ".join([item.lower() for item in variables + functions])
    hints = []

    if "页面显示" in scene:
        hints.append("如果你想改显示内容，第一眼先看页面函数本身，再看里面调用的 SEG_SetCode / SEG_SetDigit。")
        if functions:
            hints.append("优先关注这些函数：" + "、".join(functions[:4]) + "。")
        if variables:
            hints.append("优先关注这些变量：" + "、".join(variables[:4]) + "。")

    elif "按键处理" in scene:
        hints.append("如果你想改按键功能，第一眼先看按键处理函数里的 if / switch 分支，不要先改底层驱动。")
        if functions:
            hints.append("优先关注这些函数：" + "、".join(functions[:4]) + "。")
        if any("key" in item.lower() for item in variables):
            hints.append("优先检查按键值变量和页面状态变量是不是配合使用。")

    elif "参数设置" in scene:
        hints.append("如果你想改参数，先看参数结构体，再看按键里加减逻辑，最后看页面显示有没有同步。")
        if variables:
            hints.append("优先关注这些变量：" + "、".join(variables[:5]) + "。")

    elif "报警或输出控制" in scene:
        hints.append("如果你想改 LED、继电器或蜂鸣器，先看报警状态变量，再看输出控制函数。")
        if "alarm" in joined:
            hints.append("先确认报警状态是在哪里被置位的，再看它最后是如何驱动输出的。")

    elif "数据采样或数据处理" in scene:
        hints.append("如果你想改温度、ADC、频率、距离，先看数据变量，再看这段代码是在哪里更新这些变量的。")
        if variables:
            hints.append("优先关注这些变量：" + "、".join(variables[:5]) + "。")

    else:
        hints.append("先看变量名和函数名，判断它是页面、按键、参数、采样还是输出控制，再决定往哪里改。")

    hints.append("最稳的改法永远是：一次只改一个点，改完立刻重新编译。")
    return hints
