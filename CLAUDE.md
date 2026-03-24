# 智能助手项目 - CLAUDE.md

## 项目概述

基于 Streamlit 的智能对话助手，支持多用户注册登录、LLM 意图分析、工具调用和流式输出。

## 技术栈

- **前端**: Streamlit
- **LLM**: MiniMax API (OpenAI 兼容格式)
- **数据库**: SQLite (开发) / MySQL (生产)
- **Python**: 3.6.8+

## 开发命令

```bash
# 安装依赖
pip install -r requirements.txt

# 启动应用
streamlit run src/smart_assistant/main.py

# 运行测试
pytest
```

## 配置管理

所有配置在 `configs/settings.yaml`，**不上传版本控制**。

敏感配置项：
- `llm.api_key` - LLM API Key
- `app.password` - 登录密码
- `app.invite_code` - 注册邀请码
- `database.password` - 数据库密码

复制配置模板：
```bash
cp configs/settings.example.yaml configs/settings.yaml
```

## 分支管理

- `main` - 主分支，保护分支
- `new_test` - 开发分支，所有修改在此进行

提交规范：
```
feat: 新功能
fix: 修复bug
refactor: 重构
docs: 文档
test: 测试
chore: 杂项
```

## 目录结构

```
smart-assistant/
├── configs/          # 配置文件
│   ├── settings.yaml       # 主配置（不上传）
│   ├── settings.example.yaml
│   ├── prompts.yaml       # LLM 提示词模板
│   └── tools.yaml         # 工具定义
├── scripts/          # 预定义脚本
├── src/smart_assistant/
│   ├── main.py       # Streamlit 入口
│   ├── config.py     # 配置管理
│   ├── llm/          # LLM 客户端
│   ├── tools/        # 工具系统
│   ├── db/           # 数据库
│   └── services/      # 业务逻辑
└── tests/           # 测试
```

## gstack Skills

本项目使用 gstack 辅助开发，可用的 slash commands：

| 命令 | 说明 |
|------|------|
| `/review` | PR 代码审查 |
| `/plan-eng-review` | 工程架构审查 |
| `/qa` | QA 测试 + 自动修复 |
| `/browse` | 浏览器自动化测试 |
| `/ship` | 提交流程 |
| `/retro` | 团队回顾 |

## 安全注意事项

1. 工具调用仅限预定义脚本，白名单机制
2. 所有敏感配置通过配置文件管理，不硬编码
3. 用户密码使用 SHA256 哈希存储

## 团队成员

详见 `TEAM.md`
