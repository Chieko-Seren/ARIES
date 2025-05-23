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
  async fetchTopology({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个获取网络拓扑的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据
      const topology = {
        nodes: [
          { id: 'router1', type: 'router', ip: '192.168.1.1', name: '核心路由器' },
          { id: 'switch1', type: 'switch', ip: '192.168.1.2', name: '交换机1' },
          { id: 'switch2', type: 'switch', ip: '192.168.1.3', name: '交换机2' },
          { id: 'server1', type: 'server', ip: '192.168.1.100', name: 'Web服务器' },
          { id: 'server2', type: 'server', ip: '192.168.1.101', name: '数据库服务器' },
          { id: 'server3', type: 'server', ip: '192.168.1.102', name: '应用服务器' },
          { id: 'ap1', type: 'ap', ip: '192.168.1.10', name: '无线AP1' }
        ],
        links: [
          { source: 'router1', target: 'switch1', id: 'link1' },
          { source: 'router1', target: 'switch2', id: 'link2' },
          { source: 'switch1', target: 'server1', id: 'link3' },
          { source: 'switch1', target: 'server2', id: 'link4' },
          { source: 'switch2', target: 'server3', id: 'link5' },
          { source: 'switch2', target: 'ap1', id: 'link6' }
        ]
      }
      
      commit('SET_TOPOLOGY', topology)
      return topology
    } catch (error) {
      console.error('获取网络拓扑失败:', error)
      commit('SET_ERROR', '获取网络拓扑失败')
      return { nodes: [], links: [] }
    } finally {
      commit('SET_LOADING', false)
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