// 初始状态
const state = {
  sidebar: {
    opened: true,
    withoutAnimation: false
  },
  device: 'desktop',
  theme: 'light',
  size: 'medium',
  alerts: [],
  plugins: [],
  loading: false
}

// getters
const getters = {
  sidebar: state => state.sidebar,
  device: state => state.device,
  theme: state => state.theme,
  size: state => state.size,
  alerts: state => state.alerts,
  plugins: state => state.plugins,
  isLoading: state => state.loading
}

// actions
const actions = {
  toggleSidebar({ commit }) {
    commit('TOGGLE_SIDEBAR')
  },
  closeSidebar({ commit }, { withoutAnimation }) {
    commit('CLOSE_SIDEBAR', withoutAnimation)
  },
  toggleDevice({ commit }, device) {
    commit('TOGGLE_DEVICE', device)
  },
  setTheme({ commit }, theme) {
    commit('SET_THEME', theme)
    // 保存到本地存储
    localStorage.setItem('theme', theme)
  },
  setSize({ commit }, size) {
    commit('SET_SIZE', size)
    // 保存到本地存储
    localStorage.setItem('size', size)
  },
  
  // 添加警报
  addAlert({ commit }, alert) {
    // 生成唯一ID
    const id = `alert_${Date.now()}`
    const newAlert = { ...alert, id, timestamp: new Date().toISOString() }
    commit('ADD_ALERT', newAlert)
    
    // 如果设置了自动关闭，则在指定时间后自动关闭
    if (alert.autoClose !== false) {
      const duration = alert.duration || 5000 // 默认5秒
      setTimeout(() => {
        commit('REMOVE_ALERT', id)
      }, duration)
    }
    
    return id
  },
  
  // 移除警报
  removeAlert({ commit }, alertId) {
    commit('REMOVE_ALERT', alertId)
  },
  
  // 清空所有警报
  clearAlerts({ commit }) {
    commit('CLEAR_ALERTS')
  },
  
  // 加载插件
  async loadPlugins({ commit }) {
    commit('SET_LOADING', true)
    
    try {
      // 假设有一个获取插件列表的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据
      const plugins = [
        { id: 'plugin1', name: '网络监控插件', version: '1.0.0', enabled: true, url: '/plugins/network-monitor.js' },
        { id: 'plugin2', name: '性能分析插件', version: '1.2.0', enabled: true, url: '/plugins/performance-analyzer.js' },
        { id: 'plugin3', name: '安全扫描插件', version: '0.9.0', enabled: false, url: '/plugins/security-scanner.js' }
      ]
      
      commit('SET_PLUGINS', plugins)
      return plugins
    } catch (error) {
      console.error('加载插件失败:', error)
      return []
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 启用/禁用插件
  togglePlugin({ commit, state }, pluginId) {
    const plugins = state.plugins.map(plugin => {
      if (plugin.id === pluginId) {
        return { ...plugin, enabled: !plugin.enabled }
      }
      return plugin
    })
    
    commit('SET_PLUGINS', plugins)
  },
  
  // 加载插件脚本
  loadPluginScript({ state }, pluginId) {
    const plugin = state.plugins.find(p => p.id === pluginId)
    
    if (!plugin || !plugin.enabled) {
      return Promise.reject(new Error('插件不存在或未启用'))
    }
    
    return new Promise((resolve, reject) => {
      const script = document.createElement('script')
      script.src = plugin.url
      script.async = true
      script.onload = () => resolve(plugin)
      script.onerror = () => reject(new Error(`加载插件脚本失败: ${plugin.name}`))
      document.head.appendChild(script)
    })
  }
}

// mutations
const mutations = {
  TOGGLE_SIDEBAR: state => {
    state.sidebar.opened = !state.sidebar.opened
    state.sidebar.withoutAnimation = false
    if (state.sidebar.opened) {
      localStorage.setItem('sidebarStatus', '1')
    } else {
      localStorage.setItem('sidebarStatus', '0')
    }
  },
  CLOSE_SIDEBAR: (state, withoutAnimation) => {
    localStorage.setItem('sidebarStatus', '0')
    state.sidebar.opened = false
    state.sidebar.withoutAnimation = withoutAnimation
  },
  TOGGLE_DEVICE: (state, device) => {
    state.device = device
  },
  SET_THEME: (state, theme) => {
    state.theme = theme
  },
  SET_SIZE: (state, size) => {
    state.size = size
  },
  ADD_ALERT: (state, alert) => {
    state.alerts.push(alert)
  },
  REMOVE_ALERT: (state, alertId) => {
    state.alerts = state.alerts.filter(alert => alert.id !== alertId)
  },
  CLEAR_ALERTS: (state) => {
    state.alerts = []
  },
  SET_PLUGINS: (state, plugins) => {
    state.plugins = plugins
  },
  SET_LOADING: (state, loading) => {
    state.loading = loading
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}