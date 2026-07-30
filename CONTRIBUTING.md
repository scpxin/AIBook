# 贡献指南

感谢您对 Novel Creator 项目的关注！本文档提供贡献代码、报告问题和提出建议的指南。

## 快速导航

- [报告问题](#报告问题)
- [开发环境设置](#开发环境设置)
- [提交代码](#提交代码)
- [代码规范](#代码规范)
- [测试](#测试)

## 报告问题

### Bug 报告

创建 Issue 时，请包含以下信息：

1. **问题描述**: 清晰描述问题现象
2. **复现步骤**:
   ```markdown
   1. 步骤 1
   2. 步骤 2
   3. 期望结果 vs 实际结果
   ```
3. **环境信息**:
   - OS:
   - Python 版本:
   - Node.js 版本:
   - 浏览器（前端问题）:
4. **日志**: 相关错误日志（使用代码块）

### 功能建议

新功能建议请说明：
- **需求场景**: 什么情况下需要此功能
- **期望行为**: 功能应如何工作
- **替代方案**: 当前如何解决此问题

## 开发环境设置

### 后端

```bash
# 克隆仓库
git clone <repository-url>
cd novel_creator

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r app/requirements.txt

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 测试

```bash
# 后端测试
pytest tests/ -v

# 类型检查
ruff check app/ novel_creator/
vue-tsc --noEmit  # 前端
```

## 提交代码

### 分支命名

```bash
# 新功能
git checkout -b 260130-feat-auto-backup

# Bug 修复
git checkout -b 260130-fix-database-lock

# 重构
git checkout -b 260130-refactor-logger

# 文档
git checkout -b 260130-docs-security-guide
```

格式：`YYMMDD-(feat|fix|refactor|docs|test)-<简短描述>`

### 提交信息

```bash
# 格式
<type>(<scope>): <subject>

# 示例
feat(api): 添加数据库备份接口
fix(database): 修复 SQLite 锁竞争问题
docs(security): 添加安全部署指南
```

### Pull Request 检查清单

- [ ] 代码通过所有测试
- [ ] 运行 `ruff check` 无新增错误
- [ ] 前端运行 `vue-tsc --noEmit` 无错误
- [ ] 提交信息符合规范
- [ ] PR 描述清晰说明改动内容

## 代码规范

### Python

- 遵循 [PEP 8](https://pep8.org/)
- 使用 `ruff` 进行 linting
- 类型注解：推荐但不强制
- 文档字符串：公共函数和类必须包含

```python
def calculate_word_count(text: str) -> int:
    """计算文本字数（中文字符）"""
    return len([c for c in text if '\u4e00' <= c <= '\u9fff'])
```

### TypeScript/Vue

- 使用 ESLint + Prettier
- 类型安全：避免 `any`
- 组件命名：PascalCase（如 `ProjectView.vue`）
- Props 定义：使用 `withDefaults`

```typescript
interface Props {
  projectId: string
  title?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '未命名项目',
})
```

### 项目结构

```
novel_creator/
├── app/                # FastAPI 后端
│   ├── api/           # 路由处理器
│   ├── services/      # 业务逻辑
│   ├── models/        # Pydantic 模型
│   └── config.py      # 配置管理
├── frontend/          # Vue 3 前端
│   ├── src/
│   │   ├── views/    # 页面组件
│   │   ├── components/  # 通用组件
│   │   ├── composables/ # 组合式函数
│   │   └── types/      # TypeScript 类型
├── tests/             # 测试用例
├── docs/              # 项目文档
└── scripts/           # 运维脚本
```

## 测试指南

### 编写测试

```python
def test_project_creation():
    """测试项目创建功能"""
    # Given
    project_data = {"title": "测试项目", "genre": "玄幻"}
    
    # When
    response = client.post("/api/projects", json=project_data)
    
    # Then
    assert response.status_code == 200
    assert response.json()["title"] == "测试项目"
```

### 运行测试

```bash
# 全量测试
pytest tests/ -v

# 单个测试文件
pytest tests/test_pipeline.py -v

# 带覆盖率
pytest --cov=app --cov-report=html
```

## 文档维护

### 更新文档

- **API 变更**: 同步更新 `docs/api.md`
- **配置变更**: 更新环境变量表格
- **新功能**: 添加到用户指南

### 文档风格

- 标题清晰，使用层级结构
- 代码示例完整可运行
- 表格对齐，格式统一

## 发布流程

### 版本号规范

遵循语义化版本（Semantic Versioning）：

- **MAJOR**: 不兼容的 API 变更
- **MINOR**: 向后兼容的新功能
- **PATCH**: 向后兼容的问题修复

### 发布检查

1. 更新 `CHANGELOG.md`
2. 更新版本号
3. 运行全量测试
4. 创建 Git 标签
5. 发布 Release Note

## 需要帮助的领域

以下领域欢迎贡献：

- 🎨 UI/UX 改进
- 📱 移动端适配
- 🔐 认证授权系统
- 📊 数据可视化
- 🌍 国际化 (i18n)
- 🧪 测试覆盖率提升

## 常见问题

**Q: 如何运行 E2E 测试？**
```bash
pytest tests/test_pipeline_e2e.py -v
```

**Q: 前端构建失败怎么办？**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Q: 数据库锁错误如何处理？**
```bash
# 检查是否有未关闭的连接
lsof fanqie.db
# 重启服务
```

## 联系方式

- GitHub Issues: 提问和讨论
- Email: maintainers@example.com（如已配置）

---

感谢您的贡献！🎉
