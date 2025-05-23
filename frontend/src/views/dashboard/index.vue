<template>
  <div class="dashboard-container">
    <el-row :gutter="20">
      <!-- 系统概览卡片 -->
      <el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24">
        <el-card class="overview-card">
          <template #header>
            <div class="card-header">
              <h3>系统概览</h3>
              <el-button type="primary" size="small" @click="refreshData">
                <el-icon><Refresh /></el-icon>
                刷新
              </el-button>
            </div>
          </template>
          <el-row :gutter="20">
            <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
              <div class="stat-item">
                <div class="stat-icon healthy">
                  <el-icon><Monitor /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ healthyServers }}</div>
                  <div class="stat-label">健康服务器</div>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
              <div class="stat-item">
                <div class="stat-icon warning">
                  <el-icon><Warning /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ unhealthyServers }}</div>
                  <div class="stat-label">异常服务器</div>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
              <div class="stat-item">
                <div class="stat-icon info">
                  <el-icon><Connection /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ networkDevices }}</div>
                  <div class="stat-label">网络设备</div>
                </div>
              </div>
            </el-col>
            <el-col :xs="12" :sm="12" :md="6" :lg="6" :xl="6">
              <div class="stat-item">
                <div class="stat-icon danger">
                  <el-icon><Bell /></el-icon>
                </div>
                <div class="stat-info">
                  <div class="stat-value">{{ activeAlerts }}</div>
                  <div class="stat-label">活跃警报</div>
                </div>
              </div>
            </el-col>
          </el-row>
        </el-card>
      </el-col>

      <!-- 服务器状态图表 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>服务器状态</h3>
            </div>
          </template>
          <div class="chart-container" ref="serverStatusChart"></div>
        </el-card>
      </el-col>

      <!-- 网络流量图表 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <h3>网络流量</h3>
            </div>
          </template>
          <div class="chart-container" ref="networkTrafficChart"></div>
        </el-card>
      </el-col>

      <!-- 最近任务 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="task-card">
          <template #header>
            <div class="card-header">
              <h3>最近任务</h3>
              <router-link to="/task/execution">
                <el-button type="text">查看全部</el-button>
              </router-link>
            </div>
          </template>
          <el-table :data="recentTasks" style="width: 100%" v-loading="loading.tasks">
            <el-table-column prop="description" label="任务描述" min-width="180" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{row}">
                <el-tag :type="getTaskStatusType(row.status)">
                  {{ getTaskStatusText(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createdAt" label="创建时间" width="180">
              <template #default="{row}">
                {{ formatDate(row.createdAt) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 最近警报 -->
      <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
        <el-card class="alert-card">
          <template #header>
            <div class="card-header">
              <h3>最近警报</h3>
              <router-link to="/monitoring/alerts">
                <el-button type="text">查看全部</el-button>
              </router-link>
            </div>
          </template>
          <el-table :data="recentAlerts" style="width: 100%" v-loading="loading.alerts">
            <el-table-column prop="title" label="警报标题" min-width="180" />
            <el-table-column prop="level" label="级别" width="100">
              <template #default="{row}">
                <el-tag :type="getAlertLevelType(row.level)">
                  {{ row.level }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="timestamp" label="时间" width="180">
              <template #default="{row}">
                {{ formatDate(row.timestamp) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script>
import { ref, onMounted, reactive, computed, onBeforeUnmount } from 'vue'
import { useStore } from 'vuex'
import * as echarts from 'echarts'

export default {
  name: 'Dashboard',
  setup() {
    const store = useStore()
    const serverStatusChart = ref(null)
    const networkTrafficChart = ref(null)
    let serverStatusChartInstance = null
    let networkTrafficChartInstance = null

    // 加载状态
    const loading = reactive({
      servers: false,
      tasks: false,
      alerts: false,
      network: false
    })

    // 计算属性
    const healthyServers = computed(() => store.getters['server/healthyServersCount'] || 0)
    const unhealthyServers = computed(() => store.getters['server/unhealthyServersCount'] || 0)
    const networkDevices = computed(() => {
      const nodes = store.getters['network/nodes'] || []
      return nodes.filter(node => node.type !== 'server').length
    })
    const activeAlerts = computed(() => {
      return store.getters['app/alerts'].length || 0
    })

    // 最近任务
    const recentTasks = computed(() => {
      const tasks = store.getters['task/tasks'] || []
      return tasks.slice(0, 5)
    })

    // 最近警报
    const recentAlerts = computed(() => {
      const alerts = store.getters['app/alerts'] || []
      return alerts.slice(0, 5)
    })

    // 初始化图表
    const initCharts = () => {
      // 初始化服务器状态图表
      if (serverStatusChart.value) {
        serverStatusChartInstance = echarts.init(serverStatusChart.value)
        const option = {
          tooltip: {
            trigger: 'item'
          },
          legend: {
            orient: 'vertical',
            left: 'left'
          },
          series: [
            {
              name: '服务器状态',
              type: 'pie',
              radius: '70%',
              data: [
                { value: healthyServers.value, name: '健康', itemStyle: { color: '#67C23A' } },
                { value: unhealthyServers.value, name: '异常', itemStyle: { color: '#F56C6C' } }
              ],
              emphasis: {
                itemStyle: {
                  shadowBlur: 10,
                  shadowOffsetX: 0,
                  shadowColor: 'rgba(0, 0, 0, 0.5)'
                }
              }
            }
          ]
        }
        serverStatusChartInstance.setOption(option)
      }

      // 初始化网络流量图表
      if (networkTrafficChart.value) {
        networkTrafficChartInstance = echarts.init(networkTrafficChart.value)
        const option = {
          tooltip: {
            trigger: 'axis'
          },
          legend: {
            data: ['入站流量', '出站流量']
          },
          grid: {
            left: '3%',
            right: '4%',
            bottom: '3%',
            containLabel: true
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00', '24:00']
          },
          yAxis: {
            type: 'value',
            axisLabel: {
              formatter: '{value} MB/s'
            }
          },
          series: [
            {
              name: '入站流量',
              type: 'line',
              data: [1.2, 0.8, 1.5, 3.2, 2.5, 1.8, 1.3],
              itemStyle: { color: '#409EFF' }
            },
            {
              name: '出站流量',
              type: 'line',
              data: [0.6, 0.4, 0.8, 1.5, 1.2, 0.9, 0.6],
              itemStyle: { color: '#E6A23C' }
            }
          ]
        }
        networkTrafficChartInstance.setOption(option)
      }
    }

    // 刷新数据
    const refreshData = async () => {
      loading.servers = true
      loading.tasks = true
      loading.alerts = true
      loading.network = true

      try {
        // 获取服务器列表和状态
        await store.dispatch('server/fetchServers')
        await store.dispatch('server/fetchServerStatuses')
        
        // 获取网络拓扑
        await store.dispatch('network/fetchTopology')
        
        // 获取任务列表
        await store.dispatch('task/fetchTasks')
        
        // 更新图表
        updateCharts()
      } catch (error) {
        console.error('刷新数据失败:', error)
      } finally {
        loading.servers = false
        loading.tasks = false
        loading.alerts = false
        loading.network = false
      }
    }

    // 更新图表
    const updateCharts = () => {
      if (serverStatusChartInstance) {
        serverStatusChartInstance.setOption({
          series: [
            {
              data: [
                { value: healthyServers.value, name: '健康', itemStyle: { color: '#67C23A' } },
                { value: unhealthyServers.value, name: '异常', itemStyle: { color: '#F56C6C' } }
              ]
            }
          ]
        })
      }
    }

    // 格式化日期
    const formatDate = (dateString) => {
      if (!dateString) return ''
      const date = new Date(dateString)
      return date.toLocaleString()
    }

    // 获取任务状态类型
    const getTaskStatusType = (status) => {
      const statusMap = {
        'completed': 'success',
        'in_progress': 'primary',
        'pending': 'info',
        'failed': 'danger'
      }
      return statusMap[status] || 'info'
    }

    // 获取任务状态文本
    const getTaskStatusText = (status) => {
      const statusMap = {
        'completed': '已完成',
        'in_progress': '进行中',
        'pending': '等待中',
        'failed': '失败'
      }
      return statusMap[status] || status
    }

    // 获取警报级别类型
    const getAlertLevelType = (level) => {
      const levelMap = {
        'critical': 'danger',
        'warning': 'warning',
        'info': 'info'
      }
      return levelMap[level] || 'info'
    }

    // 窗口大小变化时重新调整图表大小
    const handleResize = () => {
      if (serverStatusChartInstance) {
        serverStatusChartInstance.resize()
      }
      if (networkTrafficChartInstance) {
        networkTrafficChartInstance.resize()
      }
    }

    onMounted(() => {
      refreshData()
      initCharts()
      window.addEventListener('resize', handleResize)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
      if (serverStatusChartInstance) {
        serverStatusChartInstance.dispose()
      }
      if (networkTrafficChartInstance) {
        networkTrafficChartInstance.dispose()
      }
    })

    return {
      serverStatusChart,
      networkTrafficChart,
      loading,
      healthyServers,
      unhealthyServers,
      networkDevices,
      activeAlerts,
      recentTasks,
      recentAlerts,
      refreshData,
      formatDate,
      getTaskStatusType,
      getTaskStatusText,
      getAlertLevelType
    }
  }
}
</script>

<style lang="scss" scoped>
.dashboard-container {
  padding: 20px;

  .el-row {
    margin-bottom: 20px;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h3 {
      margin: 0;
      font-size: 18px;
      font-weight: 600;
    }
  }

  .overview-card {
    margin-bottom: 20px;
  }

  .stat-item {
    display: flex;
    align-items: center;
    padding: 10px;

    .stat-icon {
      width: 60px;
      height: 60px;
      border-radius: 50%;
      display: flex;
      justify-content: center;
      align-items: center;
      margin-right: 15px;

      .el-icon {
        font-size: 24px;
        color: white;
      }

      &.healthy {
        background-color: #67C23A;
      }

      &.warning {
        background-color: #E6A23C;
      }

      &.info {
        background-color: #409EFF;
      }

      &.danger {
        background-color: #F56C6C;
      }
    }

    .stat-info {
      .stat-value {
        font-size: 24px;
        font-weight: bold;
        line-height: 1.2;
      }

      .stat-label {
        font-size: 14px;
        color: #909399;
      }
    }
  }

  .chart-card {
    margin-bottom: 20px;

    .chart-container {
      height: 300px;
    }
  }

  .task-card,
  .alert-card {
    margin-bottom: 20px;
  }
}
</style>