# 内网部署指南

本文档说明如何将智能助手部署到内网环境，以及如何新增工具。

---

## 目录

1. [环境要求](#环境要求)
2. [配置变更](#配置变更)
3. [部署步骤](#部署步骤)
4. [新增工具](#新增工具)
5. [常见问题](#常见问题)

---

## 环境要求

- Python 3.6.8 或更高版本
- MySQL 5.7+（如使用 MySQL 存储）
- LLM 服务（Ollama 或其他 OpenAI 格式 API）

---

## 配置变更

### 1. LLM 配置

编辑 `configs/settings.yaml`：

```yaml
llm:
  # 方式一：使用 Ollama（内网推荐）
  provider: "ollama"
  model: "qwen2.5:14b"           # 根据你的模型调整
  api_key: "ollama"               # Ollama 不需要真实 key
  base_url: "http://your-ollama-server:11434/v1"
  timeout: 120

  # 方式二：使用其他 OpenAI 格式 API
  # provider: "openai"
  # model: "gpt-4"
  # api_key: "your-api-key"
  # base_url: "https://your-api-endpoint/v1"
```

### 2. 数据库配置

```yaml
database:
  type: "mysql"                    # 改为 mysql
  # db_path: "data/smart_assistant.db"  # SQLite 时使用

  # MySQL 配置
  host: "your-mysql-host"
  port: 3306
  username: "your-username"
  password: "your-password"
  database: "smart_assistant"
  charset: "utf8mb4"
```

### 3. 敏感信息配置

建议使用环境变量：

```bash
# 设置环境变量
export MINIMAX_API_KEY=""
export DB_PASSWORD="your-db-password"
export OLLAMA_BASE_URL="http://your-ollama-server:11434/v1"
```

或创建 `.env` 文件（不要提交到版本控制）：

```bash
cp .env.example .env
# 编辑 .env 填入实际值
```

---

## 部署步骤

### 1. 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 或使用 pyproject.toml
pip install streamlit sqlalchemy requests pyyaml pysqlite3
```

### 2. 初始化数据库

```bash
# 确保 MySQL 中创建了数据库
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS smart_assistant CHARACTER SET utf8mb4;"

# 启动应用时自动创建表（首次运行）
streamlit run src/smart_assistant/main.py
```

### 3. 启动应用

```bash
# 基本启动
streamlit run src/smart_assistant/main.py

# 指定端口
streamlit run src/smart_assistant/main.py --server.port 8501

# 生产环境启动（建议使用 gunicorn 或 nginx）
```

### 4. 验证部署

1. 访问 `http://your-server:8501`
2. 输入测试问题验证 LLM 连接
3. 尝试触发工具（如"帮我搜索文件"）

---

## 新增工具

### 方式一：通过 YAML 配置（推荐）

编辑 `configs/tools.yaml`，添加新工具：

```yaml
tools:
  # 现有工具...

  # 新增工具示例
  - name: my_custom_tool
    description: 我的自定义工具描述
    category: custom
    parameters:
      - name: param1
        type: string
        required: true
        description: 参数1描述
      - name: param2
        type: integer
        required: false
        default: 10
        description: 参数2描述
    script_path: scripts/my_tool.sh
    timeout: 30
```

创建对应的脚本 `scripts/my_tool.sh`：

```bash
#!/bin/bash
# 我的自定义工具
# 参数通过 --param_name value 传入

PARAM1=""
PARAM2=10

while [[ $# -gt 0 ]]; do
    case $1 in
        --param1)
            PARAM1="$2"
            shift 2
            ;;
        --param2)
            PARAM2="$2"
            shift 2
            ;;
    esac
done

# 工具逻辑
echo "Param1: $PARAM1"
echo "Param2: $PARAM2"
```

让脚本可执行：

```bash
chmod +x scripts/my_tool.sh
```

### 方式二：通过 Python 代码

如果工具需要更复杂的逻辑，可以添加 Python 内置工具：

1. 在 `src/smart_assistant/tools/builtin/` 中创建新文件：

```python
# src/smart_assistant/tools/builtin/my_tool.py

from ..base import BaseTool, ToolDefinition


class MyCustomTool(BaseTool):
    """我的自定义工具"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="my_custom_tool",
            description="我的自定义工具描述",
            category="custom",
            parameters=[
                {
                    "name": "param1",
                    "type": "string",
                    "required": True,
                    "description": "参数1描述"
                }
            ],
            timeout=30
        )

    def execute(self, **kwargs) -> dict:
        param1 = kwargs.get("param1")

        # 工具逻辑
        result = do_something(param1)

        return {
            "success": True,
            "output": result
        }
```

2. 注册工具。找到 `src/smart_assistant/tools/loader.py`，在 `register_builtin_tools` 函数中添加：

```python
def register_builtin_tools(registry=None):
    if registry is None:
        registry = get_registry()

    # 注册新工具
    from .builtin.my_tool import MyCustomTool
    registry.register(MyCustomTool())
```

3. 重启应用

---

## 新增工具变更清单

新增工具时需要修改的文件：

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `configs/tools.yaml` | 必须 | 添加工具定义 |
| `scripts/your_tool.sh` | 必须 | 创建脚本文件 |
| `src/smart_assistant/tools/builtin/your_tool.py` | 可选 | 如需 Python 实现则创建 |
| `src/smart_assistant/tools/loader.py` | 可选 | 如使用 Python 内置工具则修改 |

---

## 常见问题

### 1. LLM 调用超时

```
原因：模型响应慢或服务不可达
解决：增加 timeout 配置，或检查 LLM 服务状态
```

### 2. 数据库连接失败

```
原因：MySQL 服务未启动或配置错误
解决：检查 database 配置，确保 MySQL 服务运行
```

### 3. 工具执行失败

```
原因：脚本不存在或权限不足
解决：确保脚本存在且可执行 chmod +x scripts/*.sh
```

### 4. 工具参数提取不准确

```
原因：提示词未能有效引导 LLM
解决：优化 configs/prompts.yaml 中的参数提取模板
```

---

## 配置速查表

| 配置项 | 文件 | 必填 | 说明 |
|--------|------|------|------|
| LLM provider | settings.yaml | 是 | ollama/minimax/openai |
| LLM model | settings.yaml | 是 | 模型名称 |
| LLM api_key | settings.yaml/环境变量 | 是 | API Key |
| LLM base_url | settings.yaml | 是 | API 端点 |
| database type | settings.yaml | 是 | sqlite/mysql |
| MySQL 连接信息 | settings.yaml | 当 type=mysql | 数据库配置 |

---

## 维护

- **更新提示词**：修改 `configs/prompts.yaml`
- **添加新工具**：参考上方「新增工具」章节
- **查看日志**：Streamlit 日志输出到 stdout
- **生产部署**：建议使用 systemd 或 supervisor 管理进程
