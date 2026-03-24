# 团队成员

## 成员列表

| 姓名 | GitHub | 角色 | 职责 |
|------|--------|------|------|
| - | @chenjianwei-dbdx | Owner | 项目负责人 |
| - | @chenjianwei-dbdx | QA Engineer | 模块功能测试、pytest |
| - | @chenjianwei-dbdx | Backend Developer | 后端开发、依赖安装 |
| - | @chenjianwei-dbdx | Frontend Developer | 前端开发、技术选型 |
| - | @chenjianwei-dbdx | Code Reviewer | 代码安全、通用性审核 |

---

## 角色职责详情

### 1. 测试员 (QA Engineer)

**职责**：
- 对每个模块代码进行功能测试
- 使用 pytest 编写和执行测试用例
- 根据需要安装额外的测试库
- 记录测试结果和 bug

**测试规范**：
- 测试文件放在 `tests/` 目录
- 命名：`test_*.py`
- 运行：`pytest` 或 `pytest -x --tb=short`

### 2. 后端开发 (Backend Developer)

**职责**：
- 完成核心后端业务逻辑开发
- 依赖安装和版本管理
- API 接口开发
- 与前端开发协作定义接口规范

**技术栈**：
- Python 3.6.8+
- SQLAlchemy (数据库 ORM)
- 遵循现有架构

### 3. 前端开发 (Frontend Developer)

**职责**：
- 前端界面开发（不局限于 Streamlit）
- 选择合适的前端框架
- 与后端开发协作编写接口
- UI/UX 优化

**技术选型**：
- 可选择：Streamlit、Gradio、React+Vite、Vue 等
- 与后端协商确定最终方案

### 4. 代码审核 (Code Reviewer)

**职责**：
- 审核代码安全性（OWASP Top 10）
- 审核代码通用性和可维护性
- 审核测试覆盖率
- 确保代码符合项目规范

**审核清单**：
- [ ] 安全性：无注入、越权等漏洞
- [ ] 输入验证：所有用户输入经过验证
- [ ] 错误处理：异常被正确捕获和处理
- [ ] 代码可读性：命名清晰、注释适当
- [ ] 测试覆盖率：核心逻辑有测试

---

## 成员已完成任务清单

### Owner/全部角色 - 已完成任务

- [x] 初始化项目架构（React + Vite 前端，FastAPI 后端）
- [x] 前端页面搭建（Dashboard, Query, Monitor, Connections, Chat）
- [x] 后端核心模块（LLM客户端、意图分析、插件系统）
- [x] 数据库连接管理（DBConnection、ConnectionManager）
- [x] 3个DBA内置插件（QueryExecutor、SlowQueryAnalyzer、IndexAnalyzer）
- [x] 修复 .gitignore 排除 node_modules
- [x] Chat页面流式输出（SSE）
- [x] Connections完整CRUD
- [x] Dashboard监控仪表盘
- [x] Monitor性能监控页面
- [x] Query SQL执行页面

---

## 团队规范

### Git 工作流

1. **分支命名**
   - `main` - 主分支，受保护
   - `new_test` - 开发分支
   - `feature/xxx` - 功能分支
   - `fix/xxx` - 修复分支

2. **提交规范**
   ```
   feat: 新功能
   fix: 修复bug
   refactor: 重构
   docs: 文档更新
   test: 测试
   review: 代码审核
   chore: 杂项
   ```

3. **Code Review**
   - 所有 PR 需要至少 1 人 review
   - review 通过后才能合并到 main

### 开发规范

1. **配置管理**
   - 敏感配置不提交到 git
   - 使用 `settings.example.yaml` 作为模板

2. **代码规范**
   - Python 遵循 PEP 8
   - 使用 Ruff 进行格式化和检查

3. **测试规范**
   - 新功能需要附带测试
   - 运行 `pytest` 确保所有测试通过

### 完成任务后

每位成员完成任务后：
1. 在对应的"已完成任务清单"中打勾
2. 提交代码到 `new_test` 分支
3. 在 PR 描述中记录完成的工作

---

## 团队成员更新指南

1. 编辑此文件添加新成员
2. 提交 PR
3. Review 通过后合并
