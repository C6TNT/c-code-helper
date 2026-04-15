def _join_items(items: list[str], limit: int) -> str:
    picked = items[:limit]
    if not picked:
        return "未明显识别到"
    return "、".join(picked)


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
        summary.append("这段代码里出现了 if/else，说明它在做条件判断，比如按键分支、报警判断、页面判断。")

    if "switch" in keys:
        summary.append("这段代码里出现了 switch/case，通常是在做多页面切换、多模式切换或按键分发。")

    if "for" in keys or "while" in keys:
        summary.append("这段代码里出现了循环，通常是在处理数组、遍历显示位或重复执行某段逻辑。")

    if "static" in keys:
        summary.append("这段代码里出现了 static，通常表示变量或函数只在当前文件内使用，或者变量需要保留上一次状态。")

    if "array" in keys:
        summary.append("这段代码里出现了数组写法，通常是在保存一组显示数据、历史数据或缓冲区内容。")

    if not summary:
        summary.append("这段代码没有出现太多复杂语法，更像普通变量处理或函数调用逻辑。")

    return summary


def build_reading_steps(features: dict) -> list[str]:
    steps = []
    tags = set(features.get("semantic_tags", []))

    if features.get("variables"):
        steps.append("先看变量名，判断它们是在存参数、实时数据、页面状态，还是输出状态。")

    if features.get("functions"):
        steps.append("再看函数名，先猜这个函数更偏显示、按键、参数、采样，还是输出控制。")

    if "key_handle" in tags or "key_read" in tags:
        steps.append("重点看按键值是如何进入 if/switch 分支的，这里通常就是题目真正的功能入口。")
    elif "display_output" in tags:
        steps.append("重点看数码管接口前面的计算过程，显示函数本身通常只是最后一步，真正有用的是前面怎么算出显示内容。")
    elif "param_save" in tags or "param_load" in tags or "param_edit" in tags:
        steps.append("重点看参数变量在哪改、在哪显示、在哪保存，参数逻辑通常是三段联动的。")
    elif tags:
        steps.append("重点看关键调用前后的变量变化，通常真正的业务含义就藏在这里。")
    else:
        steps.append("然后重点看判断语句和函数调用，通常题目逻辑就藏在这里。")

    steps.append("最后把这段代码和赛题要求对上：它到底是在做显示、按键、参数、采样还是报警输出。")
    return steps


def build_code_explanation(features: dict, scene: str) -> str:
    functions = features.get("functions", [])
    variables = features.get("variables", [])
    calls = features.get("calls", [])
    tags = set(features.get("semantic_tags", []))
    assignments = features.get("assignments", [])

    parts = [
        f"这段代码大约有 {features.get('non_empty_line_count', 0)} 行有效代码。",
        f"从函数名、变量名和调用动作看，它{scene}。",
    ]

    if functions:
        parts.append(f"当前最像的核心函数是：{_join_items(functions, 3)}。")

    if "param_save" in tags and "eeprom_write" in tags:
        parts.append("它更像一段参数保存逻辑：先从参数变量里取值，再拆分成适合保存的格式，最后逐个地址写入 EEPROM。")
    elif "param_load" in tags and "eeprom_read" in tags:
        parts.append("它更像一段参数加载逻辑：先从 EEPROM 把原始值读出来，再拼回程序真正使用的参数变量。")
    elif "key_handle" in tags and "page_switch" in tags:
        parts.append("它更像按键业务分发函数：先取按键值，再根据不同键值进入不同分支，里面常见的是切页面、切模式、改参数状态。")
    elif "display_output" in tags:
        parts.append("它更像页面显示函数：前面负责算显示内容，后面负责把字符或数字送到数码管对应的位置。")
    elif "alarm_output" in tags:
        parts.append("它更像报警/输出控制函数：先根据条件形成状态，再把状态映射到 LED、继电器或蜂鸣器。")
    elif "temp_sample" in tags or "adc_sample" in tags or "freq_sample" in tags or "distance_sample" in tags:
        parts.append("它更像采样/更新函数：关键不是接口名字，而是采样值最后写进哪个变量，以及后面谁会继续用它。")
    elif "rtc_sample" in tags:
        parts.append("它更像时间读取或时间显示准备逻辑：重点通常是读出的时分秒最后如何拆位、显示或参与控制。")

    if assignments:
        parts.append(f"这段代码里真正被修改的关键变量有：{_join_items(assignments, 5)}。这比只看调用名更能说明它到底在改什么。")

    if calls:
        parts.append(f"这段代码里最关键的调用有：{_join_items(calls, 5)}。先盯住这些调用前后的变量变化，通常最容易看懂。")

    if variables:
        parts.append(f"最值得先盯的变量有：{_join_items(variables, 5)}。")

    return "\n".join(parts)


def build_term_explanations(features: dict) -> list[str]:
    keys = set(features.get("keywords", []))
    variables = [item.lower() for item in features.get("variables", [])]
    functions = [item.lower() for item in features.get("functions", [])]
    joined = " ".join(variables + functions)
    result = []

    if "static" in keys:
        result.append("static：通常表示变量或函数只在当前文件内使用，或者变量需要把上一次的值保留下来。")

    if "typedef" in keys and "struct" in keys:
        result.append("typedef struct：通常是在定义一个“数据包”，方便把一组相关变量放在一起。")
    elif "struct" in keys:
        result.append("struct：通常是在把多个相关变量打包成一个整体。")

    if "enum" in keys:
        result.append("enum：通常是在定义页面编号、状态编号或模式编号，让代码比直接写数字更清楚。")

    if any(token in joined for token in ("u8", "u16", "u32")):
        result.append("u8 / u16 / u32：是单片机里常见的整数别名，可以理解成 8 位、16 位、32 位无符号整数。")

    if any(token in joined for token in ("bit",)):
        result.append("bit：是 51 单片机里常见的位变量，通常只用来表示开关状态。")

    if "array" in keys:
        result.append("数组：通常是在保存一组显示数据、历史数据或缓冲区内容。")

    if "if" in keys:
        result.append("if：通常是在做条件判断，比如按键判断、页面判断、报警判断或阈值判断。")

    if "switch" in keys:
        result.append("switch：通常是在做多页面切换、多模式切换或多按键分发。")

    if not result:
        result.append("这段代码里暂时没有识别到特别典型的术语，先按变量、函数、判断语句的顺序看就可以。")

    return result


def build_modify_hints(features: dict, scene: str) -> list[str]:
    variables = features.get("variables", [])
    functions = features.get("functions", [])
    tags = set(features.get("semantic_tags", []))
    hints = []

    if "param_save" in tags and "eeprom_write" in tags:
        hints.append("如果你要改这段保存参数的代码，先看参数结构体里真正要保存哪些字段，再看它们被拆成了几个 EEPROM 地址。")
        hints.append("高风险点：结构体字段改了，但 WriteByte 的地址布局和拆分方式没同步。")
    elif "param_load" in tags and "eeprom_read" in tags:
        hints.append("如果你要改这段读参数的代码，先看 EEPROM 每个地址读出来后，最后是怎么还原回参数变量的。")
        hints.append("高风险点：保存逻辑改了，但读取还原逻辑没跟着改。")
    elif "key_handle" in tags and "page_switch" in tags:
        hints.append("如果你要改这段按键逻辑，先看 key 值进了哪个分支，再看分支里到底改的是页面、模式还是参数。")
        hints.append("高风险点：页面枚举改了，但按键分支里的目标页面没同步。")
    elif "display_output" in tags:
        hints.append("如果你要改这段显示代码，先看显示前的数据怎么计算出来，再看最后是哪一位显示哪个字符。")
        hints.append("高风险点：数字本身改了，但位号、字符位或小数点位没有同步。")
    elif "alarm_output" in tags:
        hints.append("如果你要改这段报警/输出代码，先看报警状态在哪被置位，再看输出函数怎么响应这个状态。")
        hints.append("高风险点：改了报警条件，但 LED、继电器或蜂鸣器输出没有一起调整。")
    elif {"temp_sample", "adc_sample", "freq_sample", "distance_sample"} & tags:
        hints.append("如果你要改这段采样代码，先确认采样值最终写入哪个变量，再找这个变量后面在哪显示或参与判断。")
        hints.append("高风险点：数据变量改名了，但显示页或报警判断里还在用旧变量。")
    else:
        hints.append("先从变量名和函数名判断这段代码属于哪一块，再只改这一块最核心的 1 到 2 个变量或分支。")

    if functions:
        hints.append(f"优先盯住这些函数：{_join_items(functions, 4)}。")
    if variables:
        hints.append(f"优先盯住这些变量：{_join_items(variables, 5)}。")

    hints.append("最稳的修改方式永远是：一次只改一个点，改完立刻重新运行或验证。")
    return hints


def build_specific_actions(features: dict) -> list[str]:
    tags = set(features.get("semantic_tags", []))
    calls = set(features.get("calls", []))
    actions = []

    if "eeprom_write" in tags:
        actions.append("识别到 EEPROM 写入动作，说明这段代码在保存参数或历史数据。")
    if "eeprom_read" in tags:
        actions.append("识别到 EEPROM 读取动作，说明这段代码在加载参数或恢复上电数据。")
    if "display_output" in tags:
        actions.append("识别到数码管显示动作，说明这段代码在决定哪一位显示什么。")
    if "key_read" in tags:
        actions.append("识别到按键取值动作，说明这段代码在以键值为入口做功能分发。")
    if "page_switch" in tags:
        actions.append("识别到页面状态相关变量，说明这段代码和页面切换或页面模式有关。")
    if "temp_sample" in tags:
        actions.append("识别到温度相关动作，说明这段代码和 DS18B20 温度数据有关。")
    if "adc_sample" in tags:
        actions.append("识别到 ADC 相关动作，说明这段代码和光敏、电位器或模拟量采样有关。")
    if "freq_sample" in tags:
        actions.append("识别到频率相关动作，说明这段代码和 NE555/测频逻辑有关。")
    if "distance_sample" in tags:
        actions.append("识别到距离相关动作，说明这段代码和超声波测距有关。")
    if "rtc_sample" in tags:
        actions.append("识别到 RTC 相关动作，说明这段代码和时钟读取或时间显示有关。")
    if "alarm_output" in tags:
        actions.append("识别到报警/输出相关动作，说明这段代码会影响 LED、继电器或蜂鸣器。")
    if "UART_SendString" in calls or "UART_SendByte" in calls:
        actions.append("识别到串口发送动作，说明这段代码可能在做调试输出或串口题要求。")

    if not actions:
        actions.append("暂时没有识别到特别鲜明的外设动作，这段代码更像纯业务判断或数据整理逻辑。")

    return actions


def build_dependency_hints(features: dict) -> list[str]:
    variables = features.get("variables", [])
    calls = features.get("calls", [])
    interfaces = features.get("interfaces", [])
    hints = []

    if variables:
        hints.append(f"这段代码依赖这些变量：{_join_items(variables, 6)}。")
    if calls:
        hints.append(f"这段代码依赖这些函数调用：{_join_items(calls, 6)}。")
    if interfaces:
        hints.append(f"这段代码依赖这些外设或接口层：{_join_items(interfaces, 5)}。")

    if not hints:
        hints.append("暂时没有识别到特别明确的依赖对象，它更像一段纯局部计算或判断逻辑。")

    return hints


def build_related_function_hints(features: dict, scene: str) -> list[str]:
    tags = set(features.get("semantic_tags", []))
    calls = list(features.get("calls", []))
    functions = list(features.get("functions", []))
    related = []

    def add_items(items: list[str]) -> None:
        for item in items:
            if item and item not in related:
                related.append(item)

    add_items(functions[:3])
    add_items(calls[:5])

    if "display_output" in tags:
        add_items(["App_UpdateDisplay", "SEG_SetCode", "SEG_SetDigit", "SEG_SetDigitDp"])
    if "key_handle" in tags or "key_read" in tags:
        add_items(["App_HandleKey", "Key_GetEvent", "Key_GetShortEvent", "Key_GetLongEvent"])
    if "page_switch" in tags:
        add_items(["App_HandleKey", "App_UpdateDisplay"])
    if "param_save" in tags:
        add_items(["App_SaveParam", "App_LoadParam", "App_HandleKey"])
    if "param_load" in tags:
        add_items(["App_LoadParam", "App_SaveParam", "App_Init"])
    if "param_edit" in tags:
        add_items(["App_HandleKey", "App_UpdateDisplay", "App_SaveParam"])
    if "temp_sample" in tags:
        add_items(["DS18B20_ReadTemp", "App_UpdateSampleData", "App_UpdateAlarm"])
    if "adc_sample" in tags:
        add_items(["PCF8591_ReadADC", "App_UpdateSampleData", "App_ShowDataPage"])
    if "freq_sample" in tags:
        add_items(["FREQ_ReadHz_250ms", "App_UpdateSampleData", "App_ShowFreqPage"])
    if "distance_sample" in tags:
        add_items(["Ultrasonic_ReadDistance", "App_UpdateSampleData", "App_UpdateAlarm"])
    if "rtc_sample" in tags:
        add_items(["DS1302_ReadTime", "App_ShowTimePage", "App_Init"])
    if "alarm_output" in tags:
        add_items(["App_UpdateAlarm", "LED_Set", "Relay_Set", "Beep_Set"])
    if "eeprom_write" in tags or "eeprom_read" in tags:
        add_items(["AT24C02_WriteByte", "AT24C02_ReadByte", "App_SaveParam", "App_LoadParam"])

    if not related:
        return [f"从当前特征看，这段代码最值得顺着当前函数本身和它直接调用的函数往下追。当前归类是：{scene}。"]

    hints = [
        f"和这段代码最相关的模板函数，优先建议你顺着这些名字往下看：{_join_items(related, 8)}。"
    ]

    if "显示" in scene:
        hints.append("这类代码通常不是单独存在的，往前看数据是怎么准备的，往后看数码管接口是怎么落到具体位上的。")
    elif "按键" in scene:
        hints.append("这类代码通常会把键值分发到页面切换、参数修改或模式切换，所以别只盯当前分支，顺着目标状态变量继续看。")
    elif "参数" in scene:
        hints.append("参数相关代码通常和“显示参数”“保存参数”“加载参数”是联动的，建议三处一起串起来看。")
    elif "采样" in scene or "数据处理" in scene:
        hints.append("采样代码通常要和后面的显示页、报警判断或输出控制配合起来看，不然只看接口调用会觉得很空。")

    return hints


def build_impact_hints(features: dict, scene: str) -> list[str]:
    tags = set(features.get("semantic_tags", []))
    impacts = []

    if "param_save" in tags or "param_load" in tags or "param_edit" in tags:
        impacts.append("改这里可能会同时影响：参数保存、参数读取、参数显示。")
    if "page_switch" in tags:
        impacts.append("改这里可能会同时影响：按键切页、页面编号、页面显示函数。")
    if "display_output" in tags:
        impacts.append("改这里可能会同时影响：数码管布局、字符位置、小数点位置。")
    if "alarm_output" in tags:
        impacts.append("改这里可能会同时影响：LED、继电器、蜂鸣器的输出行为。")
    if {"temp_sample", "adc_sample", "freq_sample", "distance_sample"} & tags:
        impacts.append("改这里可能会同时影响：实时数据显示、报警判断、参数阈值判断。")
    if "rtc_sample" in tags:
        impacts.append("改这里可能会同时影响：时间显示、整点控制、历史时间记录。")
    if "uart_io" in tags:
        impacts.append("改这里可能会同时影响：串口输出格式、调试信息、串口题交互逻辑。")

    if not impacts:
        if "页面显示" in scene:
            impacts.append("改这里大概率会影响当前页面显示格式和对应的数据摆放方式。")
        elif "按键处理" in scene:
            impacts.append("改这里大概率会影响页面切换、模式切换或按键功能分发。")
        else:
            impacts.append("改这里大概率会影响和它共用变量的其他代码段，所以改完要回头检查调用链。")

    return impacts


def build_execution_chain(features: dict, scene: str) -> list[str]:
    tags = set(features.get("semantic_tags", []))
    variables = features.get("variables", [])
    calls = features.get("calls", [])
    assignments = features.get("assignments", [])

    chain = []

    if "key_read" in tags:
        chain.append("输入：先从按键接口读取键值。")
    elif {"temp_sample", "adc_sample", "freq_sample", "distance_sample", "rtc_sample"} & tags:
        chain.append("输入：先从外设或传感器读取原始数据。")
    elif variables:
        chain.append(f"输入：这段代码一开始主要依赖这些已有变量：{_join_items(variables, 4)}。")
    else:
        chain.append("输入：这段代码主要从当前函数已有变量或上层状态开始。")

    if assignments:
        chain.append(f"处理中：中间重点修改了这些变量：{_join_items(assignments, 5)}。")
    elif calls:
        chain.append(f"处理中：中间主要围绕这些调用展开：{_join_items(calls, 5)}。")
    else:
        chain.append("处理中：中间主要在做判断、计算或状态整理。")

    if "eeprom_write" in tags:
        chain.append("输出：最后把处理结果写进 EEPROM。")
    elif "display_output" in tags:
        chain.append("输出：最后把内容送到数码管显示接口。")
    elif "alarm_output" in tags:
        chain.append("输出：最后把状态映射到 LED、继电器或蜂鸣器。")
    elif "page_switch" in tags:
        chain.append("输出：最后把结果落到页面状态、模式状态或参数状态。")
    else:
        chain.append(f"输出：最后主要把结果保存在这些变量或状态里：{_join_items(assignments or variables, 4)}。")

    return chain
