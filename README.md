# HomePageScan

一个能扫描局域网中能访问的网站的工具，并可以将扫描到的项目添加到主页中，并能以网站的方式访问，类似于HomePage的nas主页。

## ✨ 主要特性

- **🔍 网络扫描**: 快速扫描并添加局域网中的服务。
- **🎨 个性化定制**:
  - **主题**: 支持浅色、深色模式，以及跟随系统自动切换。
  - **强调色**: 提供多种强调色供您选择，打造专属风格。
  - **布局**: 支持网格和列表视图，可调节卡片大小（小、中、大）。
- **🔒 管理员和多配置文件**:
  - 管理员身份验证。
  - 多配置文件管理，为不同用户提供不同视图。
- **📱 响应式设计**: 适配桌面端和移动端设备。

## 🛠️ 技术栈

- **前端**: Vue 3, TypeScript, Tailwind CSS, Vite
- **后端**: FastAPI (Python), SQLAlchemy, SQLite
- **部署**: Docker, Docker Compose

## 🚀 快速开始

### Docker 部署

**前置要求**: 安装 [Docker](https://docs.docker.com/get-docker/) 和 [Docker Compose](https://docs.docker.com/compose/install/)

1. 克隆仓库：
   ```bash
   git clone https://github.com/WhiteBr1ck/HomePageScan.git
   cd HomePageScan
   ```

2. (可选) 编辑 `docker-compose.yml` 设置管理员密码：
   ```yaml
   environment:
     - ADMIN_PASSWORD=your_secure_password
   ```

3. 构建并启动容器：
   ```bash
   docker-compose up -d --build
   ```

4. 访问应用：打开浏览器访问 `http://localhost:5173`

> [!NOTE]
> **Docker 网络扫描说明**  
> 默认使用 Bridge 网络模式，容器无法直接扫描宿主机局域网。扫描时请使用 `host.docker.internal` 或宿主机的内网 IP。  
> 不建议使用 `network_mode: host`，可能导致端口冲突。

## 📝 使用说明

- **默认账号**:
  - 用户名: `admin`
  - 密码: `admin` 
- **访客模式**: 未登录用户可以查看设置为“公开”的服务。
- **管理员模式**: 登录后拥有完全控制权，可添加、编辑、删除和排序服务。

## 📄 许可证

本项目采用 MIT 许可证。
