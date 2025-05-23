import axios from 'axios'

// 初始状态
const state = {
  tasks: [],
  scheduledTasks: [],
  currentTask: null,
  taskResult: null,
  loading: false,
  error: null
}

// getters
const getters = {
  tasks: state => state.tasks,
  scheduledTasks: state => state.scheduledTasks,
  currentTask: state => state.currentTask,
  taskResult: state => state.taskResult,
  isLoading: state => state.loading,
  hasError: state => !!state.error,
  errorMessage: state => state.error
}

// actions
const actions = {
  // 获取任务列表
  async fetchTasks({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个获取任务列表的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据
      const tasks = [
        { id: 'task1', description: '检查所有服务器状态', status: 'completed', createdAt: '2023-05-01T10:00:00Z', completedAt: '2023-05-01T10:05:00Z' },
        { id: 'task2', description: '更新Nginx配置并重启', status: 'completed', createdAt: '2023-05-02T14:30:00Z', completedAt: '2023-05-02T14:35:00Z' },
        { id: 'task3', description: '清理日志文件', status: 'in_progress', createdAt: '2023-05-03T09:15:00Z', completedAt: null },
        { id: 'task4', description: '备份数据库', status: 'pending', createdAt: '2023-05-03T16:00:00Z', completedAt: null }
      ]
      
      commit('SET_TASKS', tasks)
      return tasks
    } catch (error) {
      console.error('获取任务列表失败:', error)
      commit('SET_ERROR', '获取任务列表失败')
      return []
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 获取定时任务列表
  async fetchScheduledTasks({ commit }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个获取定时任务列表的API
      // 实际项目中应该从后端获取
      // 这里使用模拟数据
      const scheduledTasks = [
        { id: 'cron1', description: '每日备份数据库', schedule: '0 0 * * *', status: 'active', lastRun: '2023-05-01T00:00:00Z', nextRun: '2023-05-02T00:00:00Z' },
        { id: 'cron2', description: '每周清理日志文件', schedule: '0 0 * * 0', status: 'active', lastRun: '2023-04-30T00:00:00Z', nextRun: '2023-05-07T00:00:00Z' },
        { id: 'cron3', description: '每小时检查服务器状态', schedule: '0 * * * *', status: 'active', lastRun: '2023-05-01T15:00:00Z', nextRun: '2023-05-01T16:00:00Z' },
        { id: 'cron4', description: '每月更新系统包', schedule: '0 0 1 * *', status: 'inactive', lastRun: '2023-04-01T00:00:00Z', nextRun: '2023-05-01T00:00:00Z' }
      ]
      
      commit('SET_SCHEDULED_TASKS', scheduledTasks)
      return scheduledTasks
    } catch (error) {
      console.error('获取定时任务列表失败:', error)
      commit('SET_ERROR', '获取定时任务列表失败')
      return []
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 执行任务
  async executeTask({ commit }, description) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    commit('SET_TASK_RESULT', null)
    
    try {
      // 创建新任务
      const newTask = {
        id: `task_${Date.now()}`,
        description,
        status: 'in_progress',
        createdAt: new Date().toISOString(),
        completedAt: null
      }
      
      commit('SET_CURRENT_TASK', newTask)
      
      // 调用后端API执行任务
      const response = await axios.post('/api/eval', { description })
      
      // 更新任务状态
      const updatedTask = {
        ...newTask,
        status: 'completed',
        completedAt: new Date().toISOString()
      }
      
      commit('SET_CURRENT_TASK', updatedTask)
      commit('SET_TASK_RESULT', response.data)
      commit('ADD_TASK', updatedTask)
      
      return response.data
    } catch (error) {
      console.error('执行任务失败:', error)
      
      // 更新任务状态为失败
      if (state.currentTask) {
        const failedTask = {
          ...state.currentTask,
          status: 'failed',
          completedAt: new Date().toISOString()
        }
        
        commit('SET_CURRENT_TASK', failedTask)
        commit('ADD_TASK', failedTask)
      }
      
      commit('SET_ERROR', error.response?.data?.error || '执行任务失败')
      return { success: false, error: error.response?.data?.error || '执行任务失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 创建定时任务
  async createScheduledTask({ commit }, { description, schedule }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个创建定时任务的API
      // 实际项目中应该调用后端API
      // 这里直接更新状态
      const newTask = {
        id: `cron_${Date.now()}`,
        description,
        schedule,
        status: 'active',
        lastRun: null,
        nextRun: calculateNextRun(schedule)
      }
      
      commit('ADD_SCHEDULED_TASK', newTask)
      return { success: true, task: newTask }
    } catch (error) {
      console.error('创建定时任务失败:', error)
      commit('SET_ERROR', '创建定时任务失败')
      return { success: false, error: '创建定时任务失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 更新定时任务状态
  async updateScheduledTaskStatus({ commit, state }, { taskId, status }) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个更新定时任务状态的API
      // 实际项目中应该调用后端API
      // 这里直接更新状态
      const tasks = state.scheduledTasks.map(task => {
        if (task.id === taskId) {
          return { ...task, status }
        }
        return task
      })
      
      commit('SET_SCHEDULED_TASKS', tasks)
      return { success: true }
    } catch (error) {
      console.error('更新定时任务状态失败:', error)
      commit('SET_ERROR', '更新定时任务状态失败')
      return { success: false, error: '更新定时任务状态失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  },

  // 删除定时任务
  async deleteScheduledTask({ commit, state }, taskId) {
    commit('SET_LOADING', true)
    commit('SET_ERROR', null)
    
    try {
      // 假设有一个删除定时任务的API
      // 实际项目中应该调用后端API
      // 这里直接更新状态
      const tasks = state.scheduledTasks.filter(task => task.id !== taskId)
      
      commit('SET_SCHEDULED_TASKS', tasks)
      return { success: true }
    } catch (error) {
      console.error('删除定时任务失败:', error)
      commit('SET_ERROR', '删除定时任务失败')
      return { success: false, error: '删除定时任务失败' }
    } finally {
      commit('SET_LOADING', false)
    }
  }
}

// 辅助函数：计算下一次运行时间
function calculateNextRun(schedule) {
  // 这里应该有一个根据cron表达式计算下一次运行时间的逻辑
  // 简化起见，这里返回当前时间加一天
  const nextRun = new Date()
  nextRun.setDate(nextRun.getDate() + 1)
  return nextRun.toISOString()
}

// mutations
const mutations = {
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  SET_ERROR(state, error) {
    state.error = error
  },
  SET_TASKS(state, tasks) {
    state.tasks = tasks
  },
  SET_SCHEDULED_TASKS(state, tasks) {
    state.scheduledTasks = tasks
  },
  SET_CURRENT_TASK(state, task) {
    state.currentTask = task
  },
  SET_TASK_RESULT(state, result) {
    state.taskResult = result
  },
  ADD_TASK(state, task) {
    state.tasks = [task, ...state.tasks]
  },
  ADD_SCHEDULED_TASK(state, task) {
    state.scheduledTasks = [task, ...state.scheduledTasks]
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}