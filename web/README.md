# ARIES Web

ARIES Web 是一个基于 Vue.js 和 Tailwind CSS 构建的智能网络管理平台，支持通过自然语言进行网络配置和管理。

## 功能特点

- 🖥️ 多服务器管理：支持同时管理多个服务器
- 🤖 AI 辅助：集成 OpenAI API，支持自然语言生成网络配置
- 🔌 插件系统：可扩展的插件架构
- 📚 知识库：基于 RAG 的向量搜索
- 🔒 SSH 支持：安全的服务器连接
- 🎯 Cisco 配置：智能生成 Cisco 设备配置

## 快速开始

1. 克隆仓库：
```bash
git clone https://github.com/your-username/ARIES-Web.git
cd ARIES-Web
```

2. 配置 OpenAI API：
   - 在 `web/js/app.js` 中设置你的 OpenAI API 密钥
   ```javascript
   const OPENAI_API_KEY = 'your-api-key-here';
   ```

3. 启动服务：
   - 使用任意 HTTP 服务器托管 web 目录
   - 例如，使用 Python 的简单 HTTP 服务器：
   ```bash
   cd web
   python -m http.server 8000
   ```
   - 或使用 Node.js 的 http-server：
   ```bash
   npm install -g http-server
   cd web
   http-server
   ```

4. 访问网站：
   - 打开浏览器访问 `http://localhost:8000`

## 使用说明

### 服务器管理

1. 点击"服务器管理"标签
2. 点击"添加服务器"按钮添加新服务器
3. 输入服务器信息（名称、IP 地址等）
4. 点击"连接"按钮连接到服务器

### 网络配置

1. 点击"网络配置"标签
2. 在文本框中输入自然语言描述
3. 点击"生成配置"按钮
4. 查看生成的 Cisco 配置命令

### 插件系统

1. 点击"插件中心"标签
2. 浏览可用插件
3. 点击"启用"或"禁用"按钮管理插件

### 知识库

1. 点击"知识库"标签
2. 在搜索框中输入关键词
3. 查看搜索结果和相似度

## 开发指南

### 添加新插件

1. 在 `plugins` 目录下创建新的插件文件
2. 实现插件接口
3. 在插件中心注册插件

### 自定义样式

- 修改 `css/style.css` 文件
- 使用 Tailwind CSS 类进行快速样式调整

### API 集成

- 修改 `js/app.js` 中的 API 调用
- 添加新的 API 端点
- 实现自定义功能

## 安全说明

- 请妥善保管 OpenAI API 密钥
- 建议在生产环境中使用 HTTPS
- 定期更新依赖包
- 遵循最小权限原则配置服务器访问

## 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 许可证

MIT License

## 联系方式

- 项目维护者：[Your Name]
- 邮箱：[your.email@example.com]
- GitHub：[your-github-profile] 