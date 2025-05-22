# ARIES - AI Native 自动运维系统

ARIES (AI-powered Reliable Infrastructure & Enterprise Systems) 是一个基于人工智能的自动化运维系统，旨在简化和自动化IT基础设施的管理和维护工作。

## 系统特点

- **智能Agent**：基于知识图谱(KG)和检索增强生成(RAG)的智能代理
- **自动监控**：定时扫描所有服务器，确保按照配置运行
- **自动修复**：检测到问题时自动尝试修复
- **多种连接方式**：支持Shell、RJ-45、SSH和Telnet操作服务器
- **网络拓扑分析**：读取并向量化网络拓扑信息
- **用户通知**：问题无法自动解决时通过webhook通知用户
- **RESTful API**：提供完整的API接口，支持各种运维操作

## 系统架构

### 后端

- **Agent核心**：基于LLM的智能代理，使用KG和RAG辅助推理
- **监控系统**：定时扫描服务器状态
- **自动修复模块**：根据问题类型自动执行修复操作
- **API服务**：基于FastAPI的RESTful API

### 前端

- **控制面板**：系统状态监控和操作界面
- **配置管理**：服务器和网络配置管理
- **日志查看**：系统日志和操作记录

## 安装与配置

### 环境要求

- Python 3.8+
- Node.js 14+（前端）

### 安装步骤

```bash
# 克隆仓库
git clone https://github.com/yourusername/ARIES.git
cd ARIES

# 安装后端依赖
cd backend
pip install -r requirements.txt

# 安装前端依赖
cd ../frontend
npm install
```

### 配置

在`config/`目录中创建配置文件，详见配置文档。

## 使用方法

### 启动服务

```bash
# 启动后端
cd backend
python main.py

# 启动前端（开发模式）
cd ../frontend
npm run dev
```

### API使用

详见API文档。

## 许可证

GNU General Public License v2.0