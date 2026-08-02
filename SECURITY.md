# 安全政策

## 报告漏洞

如果您发现本项目存在安全漏洞，请通过以下方式报告：

- **推荐方式**: 创建 GitHub Issue，标注 `security` 标签
- **敏感漏洞**: 请发送邮件至 security@example.com（如已配置）

## 响应时间

- **确认收到**: 3 个工作日内
- **修复计划**: 5 个工作日内提供修复时间表
- **漏洞披露**: 修复后公开披露漏洞细节

## 安全考虑

本项目已实施以下安全措施：

### API 安全

- ✅ 输入验证（Pydantic 类型校验）
- ✅ SQL 注入防护（参数化查询）
- ✅ 速率限制（60 请求/分钟）
- ✅ CORS 配置（可配置白名单）
- ✅ 路径遍历防护（项目 ID / book_id 正则校验）
- ✅ JWT 签名密钥与 API Key 加盐强制来自环境变量（`API_KEY_SECRET`、`API_KEY_SALT`）

### 数据安全

- ✅ 结构化日志（JSON 格式）
- ✅ 指标监控（/metrics 端点）
- ✅ 数据库备份脚本（WAL 安全备份）
- ✅ 数据库文件存放于独立数据目录（`/app/data`）
- ⚠️ HTTPS 部署（需反向代理配置）
- ⚠️ API Key 管理接口已启用 JWT 认证，业务接口认证为规划中

### 依赖安全

定期更新依赖版本，建议：
```bash
# 每月检查依赖更新
pip install --upgrade -r app/requirements.txt
```

## 已知限制

1. **业务接口认证**: API Key 管理接口已启用 JWT 认证，其余业务接口（projects/download/design/structure/execution 等）尚未接入认证，暴露时应通过反向代理限制访问
2. **HTTP 明文**: 默认 HTTP 传输，生产环境请配置 HTTPS
3. **API Key 存储**: 前端使用 sessionStorage 存储，仍存在 XSS 风险
4. **JWT 密钥**: 必须通过 `API_KEY_SECRET` / `API_KEY_SALT` 环境变量配置，未配置时启动依赖认证的接口会失败
5. **AI 端点 SSRF 防护**: `/api/v2/settings/test-connection` 已默认拒绝私网/链路本地/保留地址，回环地址放行以支持本地模型（如 Ollama）；如需自建内网模型服务，通过 `ALLOWED_PROXY_DOMAINS` 白名单放行

## 部署建议

生产环境部署时，建议采取以下额外安全措施：

1. **反向代理**
   - 配置 Nginx/Apache 限制 IP 访问
   - 启用 HTTPS (Let's Encrypt)
   - 添加 Basic Auth 或 JWT 认证

2. **网络隔离**
   - 部署在私有网络
   - 仅开放必要端口
   - 使用防火墙规则

3. **监控审计**
   - 启用 JSON 结构化日志 (`JSON_LOG=true`)
   - 监控 `/metrics` 端点异常
   - 定期审查访问日志

## 版本安全记录

| 版本 | 日期 | 安全修复 |
|------|------|----------|
| v2.0 | 2026-01 | 初始安全审计 |

## 致谢

感谢以下贡献者报告安全漏洞：

（待补充）

---

**注意**: 本安全政策适用于 Novel Creator 项目 v2.0 及以上版本。
