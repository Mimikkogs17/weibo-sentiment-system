<template>
  <div class="home-page">
    <div class="container">
      <div class="title-row">
        <h2>系统首页</h2>
        <el-button size="small" @click="loadData" :loading="loading">刷新</el-button>
      </div>

      <!-- 概览卡片 -->
      <div class="cards">
        <div class="card">
          <div class="label">事件总数</div>
          <div class="value">{{ overview.total_events }}</div>
        </div>

        <div class="card">
          <div class="label">微博总数</div>
          <div class="value">{{ overview.total_weibos }}</div>
          <div class="subtle">历史ID上限：{{ overview.max_weibo_id || 0 }}</div>
        </div>

        <div class="card">
          <div class="label">今日新增</div>
          <div class="value">{{ overview.new_today }}</div>
        </div>

        <div class="card">
          <div class="label">负面占比</div>
          <div class="value danger">{{ overview.negative_ratio }}%</div>
        </div>
      </div>

      <div class="grid-two">
        <!-- 系统状态 -->
        <el-card shadow="never">
          <template #header>
            <div class="section-title">系统状态</div>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="后端状态">
              <el-tag type="success">{{ systemStatus.backend }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="模型状态">
              <el-tag type="success">{{ systemStatus.model }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="最近分析时间">
              {{ systemStatus.last_analysis_time }}
            </el-descriptions-item>
            <el-descriptions-item label="历史记录总数">
              {{ systemStatus.history_count }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <!-- 最近分析记录 -->
        <el-card shadow="never">
          <template #header>
            <div class="section-title">最近分析记录</div>
          </template>
          <el-table :data="recentHistory" size="small" stripe>
            <el-table-column prop="id" label="记录ID" width="80" />
            <el-table-column prop="event_name" label="事件名称" min-width="180" />
            <el-table-column prop="exported_count" label="导出次数" width="90" />
            <el-table-column prop="created_at" label="时间" min-width="160" />
            <el-table-column label="操作" width="120">
              <template #default="{ row }">
                <el-button type="primary" link @click="goViz(row.event_id)">查看可视化</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div v-if="recentHistory.length === 0" class="empty-tip">暂无历史记录</div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getDashboard } from "@/api/home";

const router = useRouter();
const loading = ref(false);

const overview = ref({
  total_events: 0,
  total_weibos: 0,
  max_weibo_id: 0,
  new_today: 0,
  negative_ratio: 0
});

const systemStatus = ref({
  backend: "online",
  model: "ready",
  last_analysis_time: "-",
  history_count: 0
});

const recentHistory = ref([]);

const loadData = async () => {
  loading.value = true;
  try {
    const { data } = await getDashboard();
    overview.value = {
      ...overview.value,
      ...(data.overview || {}),
      // 兼容后端暂未返回该字段时，从debug拿
      max_weibo_id: data?.overview?.max_weibo_id ?? data?.debug?.max_weibo_id ?? 0
    };
    systemStatus.value = data.system_status || systemStatus.value;
    recentHistory.value = data.recent_history || [];
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "加载首页数据失败");
  } finally {
    loading.value = false;
  }
};

const goViz = (eventId) => {
  if (!eventId) return ElMessage.warning("该记录没有关联事件");
  router.push(`/visualization/${eventId}`);
};

loadData();
</script>

<style scoped>
.home-page {
  background: #f5f7fb;
  min-height: calc(100vh - 64px);
  padding: 16px;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
}
.title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.title-row h2 {
  margin: 0;
  color: #111827;
}
.cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 12px;
}
.label {
  color: #6b7280;
  font-size: 13px;
}
.value {
  margin-top: 8px;
  font-size: 24px;
  font-weight: 700;
  color: #111827;
}
.value.danger {
  color: #ef4444;
}
.subtle {
  margin-top: 6px;
  font-size: 12px;
  color: #9ca3af;
}
.grid-two {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.section-title {
  font-weight: 600;
}
.empty-tip {
  margin-top: 8px;
  color: #9ca3af;
}
@media (max-width: 1000px) {
  .cards {
    grid-template-columns: repeat(2, 1fr);
  }
  .grid-two {
    grid-template-columns: 1fr;
  }
}
</style>