# C 语言代码理解助手

`c-code-helper` 是一个面向蓝桥杯单片机新生的 C 代码理解助手。

它不是通用 C 语言教学软件，也不是编译器，而是专门解决一个问题：

- 新手看见模板代码时，不知道每一行在干什么

V0.1 先聚焦最小能力：

- 粘贴一段 C 代码
- 识别常见语法元素
- 用中文解释代码大概在做什么
- 判断这段代码更像哪类赛题逻辑
- 给出推荐阅读顺序

## 当前目录结构

```text
C语言代码理解助手/
├─ app/
│  ├─ main.py
│  ├─ core/
│  ├─ ui/
│  └─ data/
├─ requirements.txt
└─ run_app.bat
```

## 运行方式

先安装依赖：

```powershell
pip install -r requirements.txt
```

再启动：

```powershell
python app/main.py
```

也可以双击：

`run_app.bat`

## V0.1 目标

第一版优先保证：

1. 能正常粘贴代码
2. 能输出可读的中文讲解
3. 能识别常见 C 语法元素
4. 能给出“这段代码更像哪类赛题逻辑”的建议

