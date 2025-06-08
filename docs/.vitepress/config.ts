import { defineConfig } from 'vitepress'

export default defineConfig({
  title: "ARIES 文档",
  description: "ARIES 项目官方文档",
  themeConfig: {
    nav: [
      { text: '首页', link: '/' },
      { text: '指南', link: '/guide/' },
      { text: 'API', link: '/api/' },
      { text: '部署', link: '/deployment/' }
    ],
    sidebar: {
      '/guide/': [
        {
          text: '指南',
          items: [
            { text: '介绍', link: '/guide/introduction' },
            { text: '快速开始', link: '/guide/getting-started' },
            { text: '架构设计', link: '/guide/architecture' },
            { text: '贡献指南', link: '/guide/contributing' }
          ]
        }
      ],
      '/api/': [
        {
          text: 'API 文档',
          items: [
            { text: '后端 API', link: '/api/backend' },
            { text: '前端 API', link: '/api/frontend' },
            { text: 'WebSocket API', link: '/api/websocket' }
          ]
        }
      ],
      '/deployment/': [
        {
          text: '部署指南',
          items: [
            { text: '环境要求', link: '/deployment/requirements' },
            { text: '安装步骤', link: '/deployment/installation' },
            { text: '配置说明', link: '/deployment/configuration' },
            { text: 'Docker 部署', link: '/deployment/docker' }
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/Chieko-Seren/ARIES' }
    ],
    footer: {
      message: '基于 MIT 许可证发布',
      copyright: 'Copyright © 2024-present ARIES Team'
    }
  }
}) 