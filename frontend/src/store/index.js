import { createStore } from 'vuex'
import user from './modules/user'
import server from './modules/server'
import network from './modules/network'
import knowledge from './modules/knowledge'
import task from './modules/task'
import app from './modules/app'

export default createStore({
  modules: {
    user,
    server,
    network,
    knowledge,
    task,
    app
  },
  // 严格模式，禁止在mutation之外修改状态
  strict: process.env.NODE_ENV !== 'production'
})