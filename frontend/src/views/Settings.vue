<template>
  <div class="settings-page">
    <div class="container">
      <div class="grid-two">
        <el-card shadow="never">
          <template #header>
            <div class="section-title">用户信息</div>
          </template>

          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户ID">{{ userInfo.id || "-" }}</el-descriptions-item>
            <el-descriptions-item label="用户名">{{ userInfo.username || "-" }}</el-descriptions-item>
            <el-descriptions-item label="角色">{{ userInfo.role || "-" }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="userInfo.is_active ? 'success' : 'danger'">
                {{ userInfo.is_active ? "正常" : "停用" }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ userInfo.created_at || "-" }}</el-descriptions-item>
          </el-descriptions>

          <div class="action-row">
            <el-button type="danger" plain @click="logout">退出登录</el-button>
          </div>
        </el-card>

        <el-card shadow="never">
          <template #header>
            <div class="section-title">修改密码</div>
          </template>

          <el-form :model="pwdForm" label-position="top">
            <el-form-item label="原密码">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input v-model="pwdForm.new_password" type="password" show-password />
            </el-form-item>
            <el-form-item label="确认新密码">
              <el-input v-model="pwdForm.confirm_password" type="password" show-password />
            </el-form-item>
            <el-button type="primary" :loading="pwdLoading" @click="changePassword">
              保存新密码
            </el-button>
          </el-form>
        </el-card>
      </div>

      <el-card shadow="never" class="mt16">
        <template #header>
          <div class="section-title">系统设置（真实采集器 / 模型切换）</div>
        </template>

        <el-descriptions :column="1" border>
          <el-descriptions-item label="当前采集器">
            {{ collector.name }} ({{ collector.endpoint }})
          </el-descriptions-item>
          <el-descriptions-item label="当前模型">
            {{ model.name }} ({{ model.version }})
          </el-descriptions-item>
        </el-descriptions>

        <el-divider />

        <el-form :model="form" inline>
          <el-form-item label="类型">
            <el-select v-model="form.switch_type" style="width:120px;">
              <el-option value="collector" label="采集器" />
              <el-option value="model" label="模型" />
            </el-select>
          </el-form-item>
          <el-form-item label="名称">
            <el-input v-model="form.name" />
          </el-form-item>
          <el-form-item label="Endpoint">
            <el-input v-model="form.endpoint" />
          </el-form-item>
          <el-form-item label="Version">
            <el-input v-model="form.version" />
          </el-form-item>
          <el-button type="primary" @click="submitSwitch">切换</el-button>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getIntegrations, switchIntegration } from "@/api/settings";
import { getMeApi, changePasswordApi } from "@/api/auth";
import { useAuthStore } from "@/stores/auth";

const router = useRouter();
const auth = useAuthStore();

const collector = ref({});
const model = ref({});
const userInfo = ref({});
const pwdLoading = ref(false);

const form = reactive({
  switch_type: "collector",
  name: "",
  endpoint: "",
  version: ""
});

const pwdForm = reactive({
  old_password: "",
  new_password: "",
  confirm_password: ""
});

const load = async () => {
  try {
    const [{ data: settingsData }, { data: meData }] = await Promise.all([
      getIntegrations(),
      getMeApi()
    ]);
    collector.value = settingsData.collector_active || {};
    model.value = settingsData.model_active || {};
    userInfo.value = meData || {};
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "加载设置失败");
  }
};

const submitSwitch = async () => {
  try {
    await switchIntegration(form);
    ElMessage.success("切换成功");
    await load();
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "切换失败");
  }
};

const changePassword = async () => {
  if (!pwdForm.old_password) return ElMessage.warning("请输入原密码");
  if (!pwdForm.new_password) return ElMessage.warning("请输入新密码");
  if (pwdForm.new_password.length < 6) return ElMessage.warning("新密码至少6位");
  if (pwdForm.new_password !== pwdForm.confirm_password) {
    return ElMessage.warning("两次输入的新密码不一致");
  }

  pwdLoading.value = true;
  try {
    await changePasswordApi({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password
    });
    ElMessage.success("密码修改成功，请重新登录");
    logout();
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "修改密码失败");
  } finally {
    pwdLoading.value = false;
  }
};

const logout = () => {
  auth.token = "";
  localStorage.removeItem("token");
  ElMessage.success("已退出登录");
  router.push("/login");
};

onMounted(load);
</script>

<style scoped>
.settings-page {
  background: #f5f7fb;
  min-height: calc(100vh - 64px);
  padding: 16px;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
}
.grid-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.section-title {
  font-weight: 600;
}
.action-row {
  margin-top: 16px;
}
.mt16 {
  margin-top: 16px;
}
@media (max-width: 900px) {
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>