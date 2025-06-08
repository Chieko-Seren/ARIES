import axios from 'axios'

// 初始状态
const state = {
  topology: {
    nodes: [],
    links: []
  },
  loading: false,
  error: null,
  taskResult: null
}

// getters
const getters = {
  topology: state => state.topology,
  nodes: state => state.topology.nodes,
  links: state => state.topology.links,
  isLoading: state => state.loading,
  hasError: state => !!state.error,
  errorMessage: state => state.error,
  taskResult: state => state.taskResult
}

// actions
const actions = {
  // 获取网络拓扑
  async fetchTopology({ commit, dispatch }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    let retryCount = 0
    const maxRetries = 3
    const retryDelay = 2000 // 2秒
    
    while (retryCount < maxRetries) {
      try {
        const response = await axios.get('/api/network/topology')
        if (!response.data) {
          throw new Error('服务器返回数据为空')
        }
        
        // 验证数据格式
        if (!Array.isArray(response.data.nodes) || !Array.isArray(response.data.links)) {
          throw new Error('服务器返回数据格式错误')
        }
        
        commit('SET_TOPOLOGY', response.data)
        return response.data
        
      } catch (error) {
        retryCount++
        const errorMessage = error.response?.data?.message || error.message || '获取网络拓扑失败'
        
        if (retryCount === maxRetries) {
          console.error(`获取网络拓扑失败 (尝试 ${retryCount}/${maxRetries}):`, error)
          commit('SET_ERROR', {
            message: errorMessage,
            code: error.response?.status,
            retryCount
          })
          // 通知用户
          dispatch('notification/showError', {
            title: '网络拓扑获取失败',
            message: `请检查网络连接后重试 (${errorMessage})`,
            duration: 5000
          }, { root: true })
          return { nodes: [], links: [] }
        }
        
        console.warn(`获取网络拓扑重试 (${retryCount}/${maxRetries}):`, error)
        await new Promise(resolve => setTimeout(resolve, retryDelay))
      }
    }
  },

  // 执行网络管理任务
  async executeNetworkTask({ commit }, description) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    commit('SET_TASK_RESULT', null)
    
    try {
      const response = await axios.post('/api/network', { description })
      commit('SET_TASK_RESULT', response.data)
      return response.data
    } catch (error) {
      console.error('执行网络任务失败:', error)
      commit('SET_ERROR', error.response?.data?.error || '执行网络任务失败')
      return { success: false, error: error.response?.data?.error || '执行网络任务失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 更新网络拓扑（添加/删除节点或链接）
  updateTopology({ commit }, { nodes, links }) {
    commit('SET_TOPOLOGY', { nodes, links })
  },

  // 添加节点
  addNode({ commit, state }, node) {
    const nodes = [...state.topology.nodes, node]
    commit('SET_TOPOLOGY', { nodes, links: state.topology.links })
  },

  // 删除节点
  removeNode({ commit, state }, nodeId) {
    const nodes = state.topology.nodes.filter(node => node.id !== nodeId)
    // 同时删除与该节点相关的链接
    const links = state.topology.links.filter(
      link => link.source !== nodeId && link.target !== nodeId
    )
    commit('SET_TOPOLOGY', { nodes, links })
  },

  // 添加链接
  addLink({ commit, state }, link) {
    const links = [...state.topology.links, link]
    commit('SET_TOPOLOGY', { nodes: state.topology.nodes, links })
  },

  // 删除链接
  removeLink({ commit, state }, linkId) {
    const links = state.topology.links.filter(link => link.id !== linkId)
    commit('SET_TOPOLOGY', { nodes: state.topology.nodes, links })
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
  SET_TOPOLOGY(state, topology) {
    state.topology = topology
  },
  SET_TASK_RESULT(state, result) {
    state.taskResult = result
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}