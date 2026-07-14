<template>
  <div class="login-page">
    <el-card class="login-card" shadow="hover">
      <div class="title-wrap">
        <h2>微博舆情情感分析系统</h2>
        <p>{{ isLogin ? "登录后进入系统" : "注册后自动登录进入系统" }}</p>
      </div>

      <el-tabs v-model="tab" stretch>
        <el-tab-pane label="登录" name="login" />
        <el-tab-pane label="注册" name="register" />
      </el-tabs>

      <el-form :model="form" label-position="top">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>

        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            show-password
            placeholder="请输入密码"
          />
        </el-form-item>

        <el-form-item v-if="!isLogin" label="确认密码">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            placeholder="请再次输入密码"
          />
        </el-form-item>

        <el-button type="primary" class="submit-btn" :loading="loading" @click="submit">
          {{ isLogin ? "登录" : "注册" }}
        </el-button>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { loginApi, registerApi } from "@/api/auth";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const tab = ref("login");
const loading = ref(false);

const form = reactive({
  username: "",
  password: "",
  confirmPassword: ""
});

const isLogin = computed(() => tab.value === "login");

const submit = async () => {
  if (!form.username.trim()) return ElMessage.warning("请输入用户名");
  if (!form.password.trim()) return ElMessage.warning("请输入密码");

  if (!isLogin.value) {
    if (form.password.length < 6) return ElMessage.warning("密码至少6位");
    if (form.password !== form.confirmPassword) return ElMessage.warning("两次密码输入不一致");
  }

  loading.value = true;
  try {
    const api = isLogin.value ? loginApi : registerApi;
    const { data } = await api({
      username: form.username,
      password: form.password
    });

    const token = data?.token || "";
    if (!token) throw new Error("未获取到token");

    auth.token = token;
    localStorage.setItem("token", token);
    ElMessage.success(isLogin.value ? "登录成功" : "注册成功");
    router.push("/");
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || (isLogin.value ? "登录失败" : "注册失败"));
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #eef4ff 0%, #f7faff 100%);
  padding: 16px;
}
.login-card {
  width: 420px;
  max-width: 100%;
  border-radius: 16px;
}
.title-wrap {
  text-align: center;
  margin-bottom: 10px;
}
.title-wrap h2 {
  margin: 0 0 8px;
  color: #111827;
}
.title-wrap p {
  margin: 0;
  color: #6b7280;
  font-size: 13px;
}
.submit-btn {
  width: 100%;
  margin-top: 8px;
}
</style>