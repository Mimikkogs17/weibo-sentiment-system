<template>
  <el-header class="nav">
    <div class="logo">微博情感挖掘系统</div>
    <el-menu mode="horizontal" :default-active="active" @select="go">
      <el-menu-item index="/">首页</el-menu-item>
      <el-menu-item index="streamlit-collector">数据采集</el-menu-item>
      <el-menu-item index="/analysis">情感分析</el-menu-item>
      <el-menu-item index="/visualization/1">可视化中心</el-menu-item>
      <el-menu-item index="/history">历史记录</el-menu-item>
      <el-menu-item index="/settings">设置</el-menu-item>
    </el-menu>
  </el-header>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";

const STREAMLIT_URL = "http://127.0.0.1:8501";

const route = useRoute();
const router = useRouter();

const active = computed(() => {
  if (route.path.startsWith("/visualization")) return "/visualization/1";
  return route.path;
});

const go = (index) => {
  if (index === "streamlit-collector") {
    //window.open(STREAMLIT_URL, "_blank"); // 新标签打开
    window.location.href = STREAMLIT_URL;
    return;
  }
  router.push(index);
};
</script>

<style scoped>
.nav { display:flex; align-items:center; background:#1e80ff; color:#fff; padding:0 14px; }
.logo { font-weight:700; margin-right:18px; white-space:nowrap; }
</style>