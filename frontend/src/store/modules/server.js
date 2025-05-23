import axios from 'axios'

// 初始状态
const state = {
  servers: [],
  serverStatuses: {},
  loading: false,
  error: null,
  currentServer: null
}

// getters
const getters = {
  allServers: state => state.servers,
  serverById: state => id => state.servers.find(server => server.id === id),
  serverStatus: state => id => state.serverStatuses[id] || null,
  isLoading: state => state.loading,
  hasError: state => !!state.error,
  errorMessage: state => state.error,
  currentServer: state => state.currentServer,
  healthyServersCount: state => {
    return Object.values(state.serverStatuses).filter(status => status?.healthy).length
  },
  unhealthyServersCount: state => {
    return Object.values(state.serverStatuses).filter(status => status && !status.healthy).length
  }
}

// actions
const actions = {
  // 获取所有服务器
  async fetchServers({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const response = await axios.get('/api/servers')
      commit('SET_SERVERS', response.data)
      return response.data
    } catch (error) {
      console.error('获取服务器列表失败:', error)
      commit('SET_ERROR', error.response?.data?.detail || '获取服务器列表失败')
      return []
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取单个服务器
  async fetchServer({ commit }, serverId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const response = await axios.get(`/api/servers/${serverId}`)
      commit('SET_CURRENT_SERVER', response.data)
      return response.data
    } catch (error) {
      console.error(`获取服务器 ${serverId} 失败:`, error)
      commit('SET_ERROR', error.response?.data?.detail || `获取服务器 ${serverId} 失败`)
      return null
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取所有服务器状态
  async fetchServersStatus({ commit }) {
    commit('SET_LOADING', true)
    
    try {
      const response = await axios.get('/api/servers/status')
      
      // 将状态数据转换为以服务器ID为键的对象
      const statusMap = {}
      response.data.forEach(status => {
        statusMap[status.id] = status
      })
      
      commit('SET_SERVERS_STATUS', statusMap)
      return statusMap
    } catch (error) {
      console.error('获取服务器状态失败:', error)
      commit('SET_ERROR', error.response?.data?.detail || '获取服务器状态失败')
      return {}
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取单个服务器状态
  async fetchServerStatus({ commit }, serverId) {
    try {
      const response = await axios.get(`/api/servers/${serverId}/status`)
      commit('SET_SERVER_STATUS', { id: serverId, status: response.data })
      return response.data
    } catch (error) {
      console.error(`获取服务器 ${serverId} 状态失败:`, error)
      return null
    }
  },

  // 执行Shell命令
  async executeShell({ commit }, { systemType, description }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      const response = await axios.post('/api/shell', { system_type: systemType, description })
      return response.data
    } catch (error) {
      console.error('执行Shell命令失败:', error)
      commit('SET_ERROR', error.response?.data?.error || '执行Shell命令失败')
      return { success: false, error: error.response?.data?.error || '执行Shell命令失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

// mutations
const mutations = {
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_ERROR(state, error) {
    state.error = error
  },
  SET_SERVERS(state, servers) {
    state.servers = servers
  },
  SET_CURRENT_SERVER(state, server) {
    state.currentServer = server
  },
  SET_SERVERS_STATUS(state, statusMap) {
    state.serverStatuses = statusMap
  },
  SET_SERVER_STATUS(state, { id, status }) {
    state.serverStatuses = { ...state.serverStatuses, [id]: status }
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}