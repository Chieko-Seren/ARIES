import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

// 路由懒加载
const Login = () => import('../views/Login.vue')
const Layout = () => import('../layout/index.vue')
const Dashboard = () => import('../views/Dashboard.vue')
const ServerList = () => import('../views/server/ServerList.vue')
const ServerDetail = () => import('../views/server/ServerDetail.vue')
const NetworkTopology = () => import('../views/network/NetworkTopology.vue')
const NetworkManagement = () => import('../views/network/NetworkManagement.vue')
const KnowledgeGraph = () => import('../views/knowledge/KnowledgeGraph.vue')
const VectorStore = () => import('../views/knowledge/VectorStore.vue')
const TaskExecution = () => import('../views/tasks/TaskExecution.vue')
const ScheduledTasks = () => import('../views/tasks/ScheduledTasks.vue')
const FileManager = () => import('../views/system/FileManager.vue')
const WebShell = () => import('../views/system/WebShell.vue')
const Settings = () => import('../views/system/Settings.vue')
const Plugins = () => import('../views/system/Plugins.vue')
const Alerts = () => import('../views/monitoring/Alerts.vue')

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/',
    component: Layout,
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: Dashboard,
        meta: { title: '仪表盘', icon: 'Odometer', requiresAuth: true }
      }
    ]
  },
  {
    path: '/servers',
    component: Layout,
    redirect: '/servers/list',
    meta: { title: '服务器管理', icon: 'Monitor', requiresAuth: true },
    children: [
      {
        path: 'list',
        name: 'ServerList',
        component: ServerList,
        meta: { title: '服务器列表', requiresAuth: true }
      },
      {
        path: 'detail/:id',
        name: 'ServerDetail',
        component: ServerDetail,
        meta: { title: '服务器详情', requiresAuth: true },
        props: true
      }
    ]
  },
  {
    path: '/network',
    component: Layout,
    redirect: '/network/topology',
    meta: { title: '网络管理', icon: 'Connection', requiresAuth: true },
    children: [
      {
        path: 'topology',
        name: 'NetworkTopology',
        component: NetworkTopology,
        meta: { title: '网络拓扑', requiresAuth: true }
      },
      {
        path: 'management',
        name: 'NetworkManagement',
        component: NetworkManagement,
        meta: { title: '网络编排', requiresAuth: true }
      }
    ]
  },
  {
    path: '/knowledge',
    component: Layout,
    redirect: '/knowledge/graph',
    meta: { title: '知识库', icon: 'DataAnalysis', requiresAuth: true },
    children: [
      {
        path: 'graph',
        name: 'KnowledgeGraph',
        component: KnowledgeGraph,
        meta: { title: '知识图谱', requiresAuth: true }
      },
      {
        path: 'vector',
        name: 'VectorStore',
        component: VectorStore,
        meta: { title: '向量存储', requiresAuth: true }
      }
    ]
  },
  {
    path: '/tasks',
    component: Layout,
    redirect: '/tasks/execution',
    meta: { title: '任务管理', icon: 'List', requiresAuth: true },
    children: [
      {
        path: 'execution',
        name: 'TaskExecution',
        component: TaskExecution,
        meta: { title: '自动运维', requiresAuth: true }
      },
      {
        path: 'scheduled',
        name: 'ScheduledTasks',
        component: ScheduledTasks,
        meta: { title: '定时任务', requiresAuth: true }
      }
    ]
  },
  {
    path: '/monitoring',
    component: Layout,
    redirect: '/monitoring/alerts',
    meta: { title: '监控告警', icon: 'Alarm', requiresAuth: true },
    children: [
      {
        path: 'alerts',
        name: 'Alerts',
        component: Alerts,
        meta: { title: '告警中心', requiresAuth: true }
      }
    ]
  },
  {
    path: '/system',
    component: Layout,
    redirect: '/system/file-manager',
    meta: { title: '系统管理', icon: 'Setting', requiresAuth: true },
    children: [
      {
        path: 'file-manager',
        name: 'FileManager',
        component: FileManager,
        meta: { title: '文件管理', requiresAuth: true }
      },
      {
        path: 'web-shell',
        name: 'WebShell',
        component: WebShell,
        meta: { title: 'Web终端', requiresAuth: true }
      },
      {
        path: 'plugins',
        name: 'Plugins',
        component: Plugins,
        meta: { title: '插件管理', requiresAuth: true }
      },
      {
        path: 'settings',
        name: 'Settings',
        component: Settings,
        meta: { title: '系统设置', requiresAuth: true }
      }
    ]
  },
  // 404页面
  {
    path: '/:pathMatch(.*)*',
    redirect: '/dashboard'
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局前置守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - ARIES自动运维系统` : 'ARIES自动运维系统'
  
  // 检查是否需要登录认证
  if (to.meta.requiresAuth !== false) {
    // 检查用户是否已登录
    const token = store.getters['user/token']
    if (!token) {
      // 未登录，重定向到登录页
      next({ name: 'Login', query: { redirect: to.fullPath } })
    } else {
      next()
    }
  } else {
    next()
  }
})

export default router