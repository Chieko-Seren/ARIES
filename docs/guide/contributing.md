# 贡献指南

感谢您对 ARIES 项目的关注！我们欢迎任何形式的贡献，包括但不限于功能开发、问题报告、文档改进等。

## 开发流程

### 1. 环境准备

- Fork 项目到自己的账号下
- 克隆项目到本地
- 设置上游仓库
- 创建开发分支

```bash
# 克隆项目
git clone https://github.com/your-username/ARIES.git
cd ARIES

# 添加上游仓库
git remote add upstream https://github.com/Chieko-Seren/ARIES.git

# 创建开发分支
git checkout -b feature/your-feature-name
```

### 2. 开发规范

#### 代码风格

- 后端 Python 代码遵循 PEP 8 规范
- 前端代码使用 ESLint 和 Prettier 进行格式化
- 使用 TypeScript 编写前端代码
- 所有代码必须通过单元测试

#### 提交规范

提交信息格式：
```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）：
- feat: 新功能
- fix: 修复
- docs: 文档
- style: 格式
- refactor: 重构
- test: 测试
- chore: 构建过程或辅助工具的变动

示例：
```
feat(auth): 添加用户认证功能

- 实现 JWT 认证
- 添加用户登录接口
- 添加权限控制

Closes #123
```

### 3. 提交流程

1. 确保代码通过所有测试
2. 更新相关文档
3. 提交 Pull Request

```bash
# 更新本地代码
git fetch upstream
git rebase upstream/main

# 提交更改
git add .
git commit -m "feat: your feature description"

# 推送到远程
git push origin feature/your-feature-name
```

### 4. Pull Request 规范

- 标题清晰描述改动内容
- 详细描述改动原因和影响
- 关联相关 Issue
- 确保 CI 通过
- 等待至少一个维护者审查

## 问题报告

### 1. 报告规范

使用 Issue 模板，包含以下信息：
- 问题描述
- 复现步骤
- 预期行为
- 实际行为
- 环境信息
- 相关日志

### 2. 标签说明

- bug: 问题报告
- enhancement: 功能建议
- documentation: 文档相关
- question: 使用咨询
- help wanted: 需要帮助

## 文档贡献

### 1. 文档类型

- API 文档
- 使用教程
- 开发指南
- 部署文档
- 常见问题

### 2. 文档规范

- 使用 Markdown 格式
- 保持文档结构清晰
- 添加必要的代码示例
- 确保文档及时更新

## 行为准则

### 1. 基本原则

- 尊重所有贡献者
- 接受建设性批评
- 关注社区利益
- 展现同理心

### 2. 禁止行为

- 使用攻击性语言
- 发布不当内容
- 骚扰他人
- 歧视行为

## 发布流程

### 1. 版本规范

遵循语义化版本（Semantic Versioning）：
- 主版本号：不兼容的 API 修改
- 次版本号：向下兼容的功能性新增
- 修订号：向下兼容的问题修正

### 2. 发布检查清单

- 更新版本号
- 更新更新日志
- 更新文档
- 运行完整测试
- 构建发布包
- 创建发布标签

## 联系方式

- 项目维护者：@Chieko-Seren
- 邮件：your-email@example.com
- 讨论区：GitHub Discussions

## 致谢

感谢所有为 ARIES 项目做出贡献的开发者！ 