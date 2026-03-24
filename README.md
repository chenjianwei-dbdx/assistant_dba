# Smart Assistant - 智能对话助手

基于 Streamlit 的智能对话助手，支持意图分析、工具调用和多轮对话。

## 功能特性

- 💬 多轮对话：支持上下文记忆
- 🎯 意图分析：自动识别用户意图
- 🛠️ 工具调用：执行预定义脚本工具
- 📝 参数提取：支持多轮对话提取参数
- 🔧 可扩展：轻松添加新工具

## 快速开始

### 1. 安装依赖

```bash
pip install streamlit sqlalchemy requests pyyaml pysqlite3
```

### 2. 配置

编辑 `configs/settings.yaml`：

```yaml
llm:
  provider: "minimax"           # 或 "ollama"
  model: "abab6.5s-chat"
  api_key: "your-api-key"
  base_url: "https://api.minimax.chat/v1"
```

### 3. 启动

```bash
streamlit run src/smart_assistant/main.py
```

## 项目结构

```
smart-assistant/
├── src/smart_assistant/
│   ├── main.py              # Streamlit 入口
│   ├── config.py           # 配置管理
│   ├── llm/                # LLM 调用
│   ├── tools/              # 工具系统
│   ├── db/                 # 数据库
│   └── services/           # 业务逻辑
├── configs/                # 配置文件
│   ├── settings.yaml       # 主配置
│   ├── tools.yaml          # 工具定义
│   └── prompts.yaml        # 提示词模板
├── scripts/                # 预定义脚本
└── DEPLOYMENT.md          # 部署指南
```

## 使用方法

### 基本对话

直接输入问题，AI 会直接回答。

### 触发工具

描述需要执行的任务，如：
- "帮我搜索 Desktop 下的 Python 文件"
- "查看系统 CPU 使用情况"
- "查看 Git 仓库状态"

### 参数提取

如果工具需要参数，系统会询问：
- "请提供要搜索的目录路径"
- "请选择要查询的资源类型"

## 内网部署

详细说明请参考 [DEPLOYMENT.md](DEPLOYMENT.md)。

## 添加新工具

详见 [DEPLOYMENT.md - 新增工具](DEPLOYMENT.md#新增工具)。

## 依赖

- Python >= 3.6.8
- Streamlit
- SQLAlchemy
- Requests
- PyYAML
- psutil（系统监控工具）
