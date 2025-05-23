<template>
  <div class="server-list-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <h2>服务器管理</h2>
          <div class="header-actions">
            <el-input
              v-model="searchQuery"
              placeholder="搜索服务器"
              prefix-icon="Search"
              clearable
              style="width: 250px; margin-right: 15px"
            />
            <el-button type="primary" @click="refreshServers">
              <el-icon><Refresh /></el-icon>
              刷新
            </el-button>
            <el-button type="success" @click="showAddServerDialog">
              <el-icon><Plus /></el-icon>
              添加服务器
            </el-button>
          </div>
        </div>
      </template>

      <!-- 服务器列表 -->
      <el-table
        :data="filteredServers"
        style="width: 100%"
        v-loading="loading"
        border
        @row-click="handleRowClick"
      >
        <el-table-column prop="name" label="服务器名称" min-width="150" />
        <el-table-column prop="ip" label="IP地址" min-width="150" />
        <el-table-column prop="os" label="操作系统" min-width="150" />
        <el-table-column label="状态" width="100">
          <template #default="{row}">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="cpu" label="CPU使用率" width="120">
          <template #default="{row}">
            <el-progress
              :percentage="row.cpu || 0"
              :color="getCpuColor(row.cpu)"
              :stroke-width="15"
            />
          </template>
        </el-table-column>
        <el-table-column prop="memory" label="内存使用率" width="120">
          <template #default="{row}">
            <el-progress
              :percentage="row.memory || 0"
              :color="getMemoryColor(row.memory)"
              :stroke-width="15"
            />
          </template>
        </el-table-column>
        <el-table-column prop="disk" label="磁盘使用率" width="120">
          <template #default="{row}">
            <el-progress
              :percentage="row.disk || 0"
              :color="getDiskColor(row.disk)"
              :stroke-width="15"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{row}">
            <el-button
              size="small"
              type="primary"
              @click.stop="viewServerDetail(row)"
            >
              详情
            </el-button>
            <el-button
              size="small"
              type="success"
              @click.stop="openWebShell(row)"
            >
              终端
            </el-button>
            <el-dropdown @command="(command) => handleCommand(command, row)" trigger="click">
              <el-button size="small" type="info">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="edit">编辑</el-dropdown-item>
                  <el-dropdown-item command="restart">重启</el-dropdown-item>
                  <el-dropdown-item command="delete" divided>
                    <span style="color: #F56C6C">删除</span>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="totalServers"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 添加/编辑服务器对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑服务器' : '添加服务器'"
      width="500px"
    >
      <el-form
        ref="serverForm"
        :model="serverForm"
        :rules="serverRules"
        label-width="100px"
      >
        <el-form-item label="服务器名称" prop="name">
          <el-input v-model="serverForm.name" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip">
          <el-input v-model="serverForm.ip" placeholder="请输入IP地址" />
        </el-form-item>
        <el-form-item label="SSH端口" prop="port">
          <el-input-number v-model="serverForm.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="serverForm.username" placeholder="请输入SSH用户名" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="serverForm.password"
            type="password"
            placeholder="请输入SSH密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="描述" prop="description">
          <el-input
            v-model="serverForm.description"
            type="textarea"
            placeholder="请输入服务器描述"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitServerForm" :loading="submitting">
            确定
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, computed, onMounted, reactive } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'

export default {
  name: 'ServerList',
  setup() {
    const store = useStore()
    const router = useRouter()
    const loading = ref(false)
    const searchQuery = ref('')
    const currentPage = ref(1)
    const pageSize = ref(10)
    const dialogVisible = ref(false)
    const isEdit = ref(false)
    const submitting = ref(false)
    const serverForm = reactive({
      id: '',
      name: '',
      ip: '',
      port: 22,
      username: '',
      password: '',
      description: ''
    })
    const serverFormRef = ref(null)

    // 表单验证规则
    const serverRules = {
      name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
      ip: [{ required: true, message: '请输入IP地址', trigger: 'blur' }],
      port: [{ required: true, message: '请输入SSH端口', trigger: 'blur' }],
      username: [{ required: true, message: '请输入SSH用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入SSH密码', trigger: 'blur' }]
    }

    // 获取服务器列表
    const fetchServers = async () => {
      loading.value = true
      try {
        await store.dispatch('server/fetchServers')
        await store.dispatch('server/fetchServerStatuses')
      } catch (error) {
        console.error('获取服务器列表失败:', error)
        ElMessage.error('获取服务器列表失败')
      } finally {
        loading.value = false
      }
    }

    // 刷新服务器列表
    const refreshServers = () => {
      fetchServers()
    }

    // 计算属性：过滤后的服务器列表
    const filteredServers = computed(() => {
      const servers = store.getters['server/servers'] || []
      const statuses = store.getters['server/serverStatuses'] || {}
      
      // 合并服务器信息和状态
      const mergedServers = servers.map(server => {
        const status = statuses[server.id] || {}
        return {
          ...server,
          status: status.status || 'unknown',
          cpu: status.cpu,
          memory: status.memory,
          disk: status.disk
        }
      })
      
      // 搜索过滤
      if (searchQuery.value) {
        const query = searchQuery.value.toLowerCase()
        return mergedServers.filter(server => 
          server.name.toLowerCase().includes(query) ||
          server.ip.toLowerCase().includes(query) ||
          (server.description && server.description.toLowerCase().includes(query))
        )
      }
      
      return mergedServers
    })

    // 计算属性：总服务器数量
    const totalServers = computed(() => filteredServers.value.length)

    // 分页处理
    const handleSizeChange = (size) => {
      pageSize.value = size
    }

    const handleCurrentChange = (page) => {
      currentPage.value = page
    }

    // 获取状态类型
    const getStatusType = (status) => {
      const statusMap = {
        'online': 'success',
        'offline': 'danger',
        'warning': 'warning',
        'unknown': 'info'
      }
      return statusMap[status] || 'info'
    }

    // 获取状态文本
    const getStatusText = (status) => {
      const statusMap = {
        'online': '在线',
        'offline': '离线',
        'warning': '警告',
        'unknown': '未知'
      }
      return statusMap[status] || '未知'
    }

    // 获取CPU使用率颜色
    const getCpuColor = (value) => {
      if (value >= 90) return '#F56C6C'
      if (value >= 70) return '#E6A23C'
      return '#67C23A'
    }

    // 获取内存使用率颜色
    const getMemoryColor = (value) => {
      if (value >= 90) return '#F56C6C'
      if (value >= 70) return '#E6A23C'
      return '#67C23A'
    }

    // 获取磁盘使用率颜色
    const getDiskColor = (value) => {
      if (value >= 90) return '#F56C6C'
      if (value >= 70) return '#E6A23C'
      return '#67C23A'
    }

    // 处理行点击
    const handleRowClick = (row) => {
      viewServerDetail(row)
    }

    // 查看服务器详情
    const viewServerDetail = (server) => {
      router.push(`/server/detail/${server.id}`)
    }

    // 打开Web终端
    const openWebShell = (server) => {
      router.push(`/system/web-shell?serverId=${server.id}`)
    }

    // 处理下拉菜单命令
    const handleCommand = (command, server) => {
      switch (command) {
        case 'edit':
          editServer(server)
          break
        case 'restart':
          restartServer(server)
          break
        case 'delete':
          deleteServer(server)
          break
      }
    }

    // 显示添加服务器对话框
    const showAddServerDialog = () => {
      isEdit.value = false
      resetServerForm()
      dialogVisible.value = true
    }

    // 编辑服务器
    const editServer = (server) => {
      isEdit.value = true
      Object.assign(serverForm, {
        id: server.id,
        name: server.name,
        ip: server.ip,
        port: server.port || 22,
        username: server.username,
        // 不回显密码
        password: '',
        description: server.description
      })
      dialogVisible.value = true
    }

    // 重启服务器
    const restartServer = (server) => {
      ElMessageBox.confirm(
        `确定要重启服务器 ${server.name} (${server.ip}) 吗？`,
        '重启确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      ).then(async () => {
        try {
          // 这里应该调用重启服务器的API
          // 实际项目中应该调用后端API
          ElMessage.success(`服务器 ${server.name} 重启命令已发送`)
        } catch (error) {
          console.error('重启服务器失败:', error)
          ElMessage.error('重启服务器失败')
        }
      }).catch(() => {
        // 取消操作
      })
    }

    // 删除服务器
    const deleteServer = (server) => {
      ElMessageBox.confirm(
        `确定要删除服务器 ${server.name} (${server.ip}) 吗？此操作不可恢复！`,
        '删除确认',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'error'
        }
      ).then(async () => {
        try {
          // 这里应该调用删除服务器的API
          // 实际项目中应该调用后端API
          ElMessage.success(`服务器 ${server.name} 已删除`)
          refreshServers()
        } catch (error) {
          console.error('删除服务器失败:', error)
          ElMessage.error('删除服务器失败')
        }
      }).catch(() => {
        // 取消操作
      })
    }

    // 重置服务器表单
    const resetServerForm = () => {
      Object.assign(serverForm, {
        id: '',
        name: '',
        ip: '',
        port: 22,
        username: '',
        password: '',
        description: ''
      })
      if (serverFormRef.value) {
        serverFormRef.value.resetFields()
      }
    }

    // 提交服务器表单
    const submitServerForm = () => {
      if (!serverFormRef.value) return
      
      serverFormRef.value.validate(async valid => {
        if (!valid) return
        
        submitting.value = true
        try {
          if (isEdit.value) {
            // 编辑服务器
            // 这里应该调用更新服务器的API
            // 实际项目中应该调用后端API
            ElMessage.success(`服务器 ${serverForm.name} 更新成功`)
          } else {
            // 添加服务器
            // 这里应该调用添加服务器的API
            // 实际项目中应该调用后端API
            ElMessage.success(`服务器 ${serverForm.name} 添加成功`)
          }
          
          dialogVisible.value = false
          refreshServers()
        } catch (error) {
          console.error(isEdit.value ? '更新服务器失败:' : '添加服务器失败:', error)
          ElMessage.error(isEdit.value ? '更新服务器失败' : '添加服务器失败')
        } finally {
          submitting.value = false
        }
      })
    }

    onMounted(() => {
      fetchServers()
    })

    return {
      loading,
      searchQuery,
      currentPage,
      pageSize,
      dialogVisible,
      isEdit,
      submitting,
      serverForm,
      serverFormRef,
      serverRules,
      filteredServers,
      totalServers,
      refreshServers,
      handleSizeChange,
      handleCurrentChange,
      getStatusType,
      getStatusText,
      getCpuColor,
      getMemoryColor,
      getDiskColor,
      handleRowClick,
      viewServerDetail,
      openWebShell,
      handleCommand,
      showAddServerDialog,
      submitServerForm
    }
  }
}
</script>

<style lang="scss" scoped>
.server-list-container {
  padding: 20px;

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;

    h2 {
      margin: 0;
      font-size: 20px;
      font-weight: 600;
    }

    .header-actions {
      display: flex;
      align-items: center;
    }
  }

  .el-table {
    margin-top: 20px;
    
    :deep(.el-table__row) {
      cursor: pointer;
    }
  }

  .pagination-container {
    margin-top: 20px;
    display: flex;
    justify-content: flex-end;
  }
}
</style>