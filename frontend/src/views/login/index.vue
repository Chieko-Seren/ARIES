<template>
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <img src="@/assets/logo.svg" alt="ARIES Logo" class="logo">
        <h1>ARIES 智能运维系统</h1>
      </div>
      
      <el-form
        ref="loginForm"
        :model="loginForm"
        :rules="loginRules"
        class="login-form"
        autocomplete="on"
        label-position="top"
      >
        <el-form-item prop="username" label="用户名">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            type="text"
            tabindex="1"
            autocomplete="on"
            prefix-icon="User"
          />
        </el-form-item>

        <el-form-item prop="password" label="密码">
          <el-input
            v-model="loginForm.password"
            :type="passwordVisible ? 'text' : 'password'"
            placeholder="请输入密码"
            tabindex="2"
            autocomplete="on"
            prefix-icon="Lock"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            :loading="loading"
            type="primary"
            class="login-button"
            @click.prevent="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        <p>© {{ new Date().getFullYear() }} ARIES 智能运维系统</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, toRefs } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

export default {
  name: 'Login',
  setup() {
    const loginForm = reactive({
      username: '',
      password: '',
      remember: false
    })

    const loginRules = {
      username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
      password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
    }

    const store = useStore()
    const router = useRouter()
    const loginFormRef = ref(null)
    const loading = ref(false)
    const passwordVisible = ref(false)

    // 处理登录
    const handleLogin = () => {
      loginFormRef.value.validate(async valid => {
        if (!valid) {
          return false
        }

        try {
          loading.value = true
          // 调用登录接口
          const result = await store.dispatch('user/login', {
            username: loginForm.username,
            password: loginForm.password
          })

          if (result) {
            ElMessage.success('登录成功')
            // 跳转到首页或者上次访问的页面
            const redirect = router.currentRoute.value.query.redirect || '/'
            router.push(redirect)
          }
        } catch (error) {
          console.error('登录失败:', error)
          ElMessage.error(error.message || '登录失败，请检查用户名和密码')
        } finally {
          loading.value = false
        }
      })
    }

    return {
      loginForm,
      loginRules,
      loginFormRef,
      loading,
      passwordVisible,
      handleLogin
    }
  }
}
</script>

<style lang="scss" scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;

  .login-card {
    width: 400px;
    padding: 40px;
    background-color: #fff;
    border-radius: 8px;
    box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
  }

  .login-header {
    text-align: center;
    margin-bottom: 30px;

    .logo {
      width: 80px;
      height: 80px;
      margin-bottom: 16px;
    }

    h1 {
      font-size: 24px;
      color: #303133;
      margin: 0;
    }
  }

  .login-form {
    margin-bottom: 30px;

    .login-button {
      width: 100%;
      padding: 12px 0;
      font-size: 16px;
    }
  }

  .login-footer {
    text-align: center;
    color: #909399;
    font-size: 14px;
  }
}
</style>