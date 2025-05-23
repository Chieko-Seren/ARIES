import axios from 'axios'
import Cookies from 'js-cookie'
import router from '@/router'

// 初始状态
const state = {
  token: Cookies.get('token') || '',
  username: '',
  fullName: '',
  email: '',
  avatar: '',
  roles: []
}

// getters
const getters = {
  token: state => state.token,
  username: state => state.username,
  fullName: state => state.fullName || state.username,
  email: state => state.email,
  avatar: state => state.avatar,
  isAuthenticated: state => !!state.token
}

// actions
const actions = {
  // 登录
  async login({ commit }, { username, password }) {
    try {
      // 创建表单数据（OAuth2要求）
      const formData = new FormData()
      formData.append('username', username)
      formData.append('password', password)

      const response = await axios.post('/api/auth/token', formData)
      const { access_token, token_type } = response.data
      
      // 保存token
      const token = `${token_type} ${access_token}`
      commit('SET_TOKEN', token)
      
      // 设置axios默认Authorization头
      axios.defaults.headers.common['Authorization'] = token
      
      // 保存到cookie，7天过期
      Cookies.set('token', token, { expires: 7 })
      
      // 获取用户信息
      await dispatch('getUserInfo')
      
      return { success: true }
    } catch (error) {
      console.error('登录失败:', error)
      return { 
        success: false, 
        message: error.response?.data?.detail || '用户名或密码错误'
      }
    }
  },

  // 登出
  logout({ commit }) {
    // 清除token
    commit('SET_TOKEN', '')
    commit('SET_USER_INFO', { username: '', fullName: '', email: '', roles: [] })
    
    // 清除cookie
    Cookies.remove('token')
    
    // 清除axios默认头
    delete axios.defaults.headers.common['Authorization']
    
    // 重定向到登录页
    router.push('/login')
  },

  // 获取用户信息
  async getUserInfo({ commit, state }) {
    if (!state.token) return
    
    try {
      // 这里应该有一个获取用户信息的API
      // 由于示例中没有，我们假设用户信息包含在token中或使用默认值
      
      // 设置用户信息（实际项目中应该从API获取）
      const userInfo = {
        username: 'admin', // 默认用户名
        fullName: '管理员',
        email: 'admin@example.com',
        roles: ['admin']
      }
      
      commit('SET_USER_INFO', userInfo)
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  },

  // 检查认证状态
  checkAuth({ dispatch, state }) {
    if (state.token) {
      // 设置axios默认Authorization头
      axios.defaults.headers.common['Authorization'] = state.token
      
      // 如果有token但没有用户信息，获取用户信息
      if (!state.username) {
        dispatch('getUserInfo')
      }
    }
  }
}

// mutations
const mutations = {
  SET_TOKEN(state, token) {
    state.token = token
  },
  SET_USER_INFO(state, { username, fullName, email, roles }) {
    state.username = username
    state.fullName = fullName
    state.email = email
    state.roles = roles
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}