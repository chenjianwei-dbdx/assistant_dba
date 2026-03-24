# 团队成员

## 成员列表

| 姓名 | GitHub | 角色 | 职责 |
|------|--------|------|------|
| - | @chenjianwei-dbdx | Owner | 项目负责人 |

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

### 沟通方式

- GitHub Issues - 功能需求和 bug 追踪
- Pull Requests - 代码审查

---

## 团队成员更新指南

1. 编辑此文件添加新成员
2. 提交 PR
3. Review 通过后合并
