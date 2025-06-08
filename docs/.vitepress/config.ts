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
            { text: '架构设计', link: '/guide/architecture' }
          ]
        }
      ],
      '/api/': [
        {
          text: 'API 文档',
          items: [
            { text: '后端 API', link: '/api/backend' },
            { text: '前端 API', link: '/api/frontend' }
          ]
        }
      ],
      '/deployment/': [
        {
          text: '部署指南',
          items: [
            { text: '环境要求', link: '/deployment/requirements' },
            { text: '安装步骤', link: '/deployment/installation' },
            { text: '配置说明', link: '/deployment/configuration' }
          ]
        }
      ]
    },
    socialLinks: [
      { icon: 'github', link: 'https://github.com/your-repo' }
    ]
  }
}) 