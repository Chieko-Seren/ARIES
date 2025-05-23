import axios from 'axios'

// 初始状态
const state = {
  knowledgeGraph: {
    nodes: [],
    edges: []
  },
  vectorDocuments: [],
  loading: false,
  error: null,
  searchResults: []
}

// getters
const getters = {
  knowledgeGraph: state => state.knowledgeGraph,
  graphNodes: state => state.knowledgeGraph.nodes,
  graphEdges: state => state.knowledgeGraph.edges,
  vectorDocuments: state => state.vectorDocuments,
  isLoading: state => state.loading,
  hasError: state => !!state.error,
  errorMessage: state => state.error,
  searchResults: state => state.searchResults
}

// actions
const actions = {
  // 获取知识图谱
  async fetchKnowledgeGraph({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个获取知识图谱的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据
      const graph = {
        nodes: [
          { id: 'nginx_error', label: 'Nginx错误', type: 'problem', category: 'web_server' },
          { id: 'nginx_config', label: 'Nginx配置问题', type: 'problem', category: 'web_server' },
          { id: 'nginx_restart', label: '重启Nginx', type: 'solution', description: '使用systemctl restart nginx命令重启Nginx服务' },
          { id: 'nginx_check_config', label: '检查Nginx配置', type: 'solution', description: '使用nginx -t命令检查配置文件语法' },
          { id: 'mysql_connection', label: 'MySQL连接问题', type: 'problem', category: 'database' },
          { id: 'mysql_restart', label: '重启MySQL', type: 'solution', description: '使用systemctl restart mysql命令重启MySQL服务' },
          { id: 'disk_full', label: '磁盘空间不足', type: 'problem', category: 'system' },
          { id: 'clean_logs', label: '清理日志文件', type: 'solution', description: '使用find /var/log -type f -name "*.log" -exec rm {} \; 命令清理日志文件' }
        ],
        edges: [
          { source: 'nginx_error', target: 'nginx_restart', weight: 0.8 },
          { source: 'nginx_config', target: 'nginx_check_config', weight: 0.9 },
          { source: 'mysql_connection', target: 'mysql_restart', weight: 0.7 },
          { source: 'disk_full', target: 'clean_logs', weight: 0.85 }
        ]
      }
      
      commit('SET_KNOWLEDGE_GRAPH', graph)
      return graph
    } catch (error) {
      console.error('获取知识图谱失败:', error)
      commit('SET_ERROR', '获取知识图谱失败')
      return { nodes: [], edges: [] }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取向量存储文档
  async fetchVectorDocuments({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个获取向量存储文档的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据
      const documents = [
        {
          id: 'linux_commands_1',
          content: 'Linux常用命令：ls（列出目录内容）、cd（切换目录）、pwd（显示当前目录）、mkdir（创建目录）、rm（删除文件或目录）...',
          type: 'knowledge',
          category: 'linux'
        },
        {
          id: 'nginx_troubleshooting',
          content: 'Nginx常见问题排查：1. 检查Nginx是否运行：systemctl status nginx；2. 检查配置文件语法：nginx -t...',
          type: 'knowledge',
          category: 'web_server'
        },
        {
          id: 'mysql_troubleshooting',
          content: 'MySQL常见问题排查：1. 检查MySQL是否运行：systemctl status mysql；2. 检查错误日志：tail /var/log/mysql/error.log...',
          type: 'knowledge',
          category: 'database'
        },
        {
          id: 'disk_management',
          content: '磁盘管理：1. 查看磁盘使用情况：df -h；2. 查看目录大小：du -sh /path/to/directory；3. 清理日志文件...',
          type: 'knowledge',
          category: 'system'
        }
      ]
      
      commit('SET_VECTOR_DOCUMENTS', documents)
      return documents
    } catch (error) {
      console.error('获取向量存储文档失败:', error)
      commit('SET_ERROR', '获取向量存储文档失败')
      return []
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 搜索向量存储
  async searchVectorStore({ commit }, query) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个搜索向量存储的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据和简单的关键词匹配
      const documents = [
        {
          id: 'linux_commands_1',
          content: 'Linux常用命令：ls（列出目录内容）、cd（切换目录）、pwd（显示当前目录）、mkdir（创建目录）、rm（删除文件或目录）...',
          type: 'knowledge',
          category: 'linux'
        },
        {
          id: 'nginx_troubleshooting',
          content: 'Nginx常见问题排查：1. 检查Nginx是否运行：systemctl status nginx；2. 检查配置文件语法：nginx -t...',
          type: 'knowledge',
          category: 'web_server'
        },
        {
          id: 'mysql_troubleshooting',
          content: 'MySQL常见问题排查：1. 检查MySQL是否运行：systemctl status mysql；2. 检查错误日志：tail /var/log/mysql/error.log...',
          type: 'knowledge',
          category: 'database'
        },
        {
          id: 'disk_management',
          content: '磁盘管理：1. 查看磁盘使用情况：df -h；2. 查看目录大小：du -sh /path/to/directory；3. 清理日志文件...',
          type: 'knowledge',
          category: 'system'
        }
      ]
      
      // 简单的关键词匹配
      const results = documents.filter(doc => 
        doc.content.toLowerCase().includes(query.toLowerCase()) ||
        doc.category.toLowerCase().includes(query.toLowerCase())
      )
      
      commit('SET_SEARCH_RESULTS', results)
      return results
    } catch (error) {
      console.error('搜索向量存储失败:', error)
      commit('SET_ERROR', '搜索向量存储失败')
      return []
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 添加文档到向量存储
  async addDocument({ commit, state }, document) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个添加文档的API
      // 实际项目中应该调用后端API
      // 这里直接更新状态
      const documents = [...state.vectorDocuments, document]
      commit('SET_VECTOR_DOCUMENTS', documents)
      return { success: true }
    } catch (error) {
      console.error('添加文档失败:', error)
      commit('SET_ERROR', '添加文档失败')
      return { success: false, error: '添加文档失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 删除文档
  async deleteDocument({ commit, state }, documentId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个删除文档的API
      // 实际项目中应该调用后端API
      // 这里直接更新状态
      const documents = state.vectorDocuments.filter(doc => doc.id !== documentId)
      commit('SET_VECTOR_DOCUMENTS', documents)
      return { success: true }
    } catch (error) {
      console.error('删除文档失败:', error)
      commit('SET_ERROR', '删除文档失败')
      return { success: false, error: '删除文档失败' }
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
  SET_KNOWLEDGE_GRAPH(state, graph) {
    state.knowledgeGraph = graph
  },
  SET_VECTOR_DOCUMENTS(state, documents) {
    state.vectorDocuments = documents
  },
  SET_SEARCH_RESULTS(state, results) {
    state.searchResults = results
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}