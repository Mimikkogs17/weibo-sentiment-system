<template>
  <div class="page">
    <div class="container">
      <div class="card head-card">
        <h2>{{ eventData.event_name || "情感分析可视化" }}</h2>
        <p class="sub">{{ eventData.event_time_range || "-" }}</p>

        <div class="uploader-row">
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".csv"
            :on-change="onFileChange"
            :show-file-list="true"
          >
            <el-button>选择CSV</el-button>
          </el-upload>
          <el-button type="primary" :loading="uploading" @click="submitCsv">上传并渲染</el-button>
        </div>
      </div>

      <div class="grid two">
        <div class="card">
          <h3>热点积极链接（Top5）</h3>
          <ul class="list">
            <li v-for="(item, i) in positiveList" :key="`p-${i}`">
              <a v-if="item.url && item.url !== '#'" :href="item.url" target="_blank">{{ item.title || "无标题" }}</a>
              <span v-else>{{ item.title || "无标题" }}</span>
              <span class="likes">{{ item.likes || 0 }}</span>
            </li>
            <li v-if="positiveList.length === 0" class="empty">暂无数据</li>
          </ul>
        </div>

        <div class="card">
          <h3>热点消极链接（Top5）</h3>
          <ul class="list">
            <li v-for="(item, i) in negativeList" :key="`n-${i}`">
              <a v-if="item.url && item.url !== '#'" :href="item.url" target="_blank">{{ item.title || "无标题" }}</a>
              <span v-else>{{ item.title || "无标题" }}</span>
              <span class="likes">{{ item.likes || 0 }}</span>
            </li>
            <li v-if="negativeList.length === 0" class="empty">暂无数据</li>
          </ul>
        </div>
      </div>

      <div class="card">
        <h3>词云图</h3>
        <div ref="cloudRef" class="chart lg"></div>
      </div>

      <div class="grid two">
        <div class="card">
          <h3>情感占比</h3>
          <div ref="pieRef" class="chart md"></div>
        </div>
        <div class="card">
          <h3>情绪时间趋势（10分钟刻度）</h3>
          <div ref="trendRef" class="chart md"></div>
        </div>
      </div>

      <div class="grid two">
        <div class="card">
          <h3>情绪-互动散点图（点赞 vs 评论）</h3>
          <div ref="scatterRef" class="chart md"></div>
        </div>
        <div class="card">
          <h3>性别情绪堆叠柱状图</h3>
          <div ref="genderRef" class="chart md"></div>
        </div>
      </div>

      <div class="card">
        <h3>事件总结</h3>
        <p class="summary">{{ eventData.summary || "暂无总结" }}</p>
        <h4>热点内容</h4>
        <ul class="list">
          <li v-for="(x, i) in hotPoints" :key="`h-${i}`">{{ x }}</li>
          <li v-if="hotPoints.length === 0" class="empty">暂无数据</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
import * as echarts from "echarts";
import "echarts-wordcloud";
import { onMounted, ref, nextTick, computed, onBeforeUnmount } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { getVisualizationEvent, uploadVisualizationCsv } from "@/api/visualization";

const route = useRoute();
const router = useRouter();

const cloudRef = ref(null);
const pieRef = ref(null);
const trendRef = ref(null);
const scatterRef = ref(null);
const genderRef = ref(null);

let cloudChart = null;
let pieChart = null;
let trendChart = null;
let scatterChart = null;
let genderChart = null;

const fileObj = ref(null);
const uploading = ref(false);

const eventData = ref({
  event_name: "",
  event_time_range: "",
  summary: "",
  hot_points: [],
  positive_links: [],
  negative_links: [],
  wordcloud: [],
  sentiment_distribution: { positive: 0, neutral: 0, negative: 0 },
  trend: { slots: [], positive: [], neutral: [], negative: [] },
  interaction_scatter: { positive: [], neutral: [], negative: [] },
  gender_sentiment: { categories: ["男", "女", "未知"], positive: [0,0,0], neutral: [0,0,0], negative: [0,0,0] }
});

const positiveList = computed(() => (eventData.value.positive_links || []).slice(0, 5));
const negativeList = computed(() => (eventData.value.negative_links || []).slice(0, 5));
const hotPoints = computed(() => (eventData.value.hot_points || []).slice(0, 12));
const wordcloudData = computed(() => (eventData.value.wordcloud || []).filter(w => (w?.name || "").length <= 8));

const initCharts = () => {
  if (cloudRef.value && !cloudChart) cloudChart = echarts.init(cloudRef.value);
  if (pieRef.value && !pieChart) pieChart = echarts.init(pieRef.value);
  if (trendRef.value && !trendChart) trendChart = echarts.init(trendRef.value);
  if (scatterRef.value && !scatterChart) scatterChart = echarts.init(scatterRef.value);
  if (genderRef.value && !genderChart) genderChart = echarts.init(genderRef.value);
};

const renderCloud = () => {
  if (!cloudChart) return;
  const palette = ["#3b82f6","#22c55e","#f59e0b","#ef4444","#8b5cf6","#06b6d4","#ec4899","#84cc16","#f97316","#14b8a6"];
  const wc = wordcloudData.value.map((item, i) => ({ ...item, textStyle: { color: palette[i % palette.length] } }));
  cloudChart.clear();
  cloudChart.setOption({
    tooltip: {},
    series: [{ type: "wordCloud", shape: "circle", sizeRange: [12, 50], rotationRange: [-45, 45], gridSize: 8, data: wc }]
  });
};

const renderPie = () => {
  if (!pieChart) return;
  const s = eventData.value.sentiment_distribution || { positive: 0, neutral: 0, negative: 0 };
  pieChart.clear();
  pieChart.setOption({
    tooltip: { trigger: "item" },
    legend: { bottom: 0 },
    series: [{
      type: "pie",
      radius: ["35%", "65%"],
      data: [
        { name: "积极", value: s.positive, itemStyle: { color: "#22c55e" } },
        { name: "中性", value: s.neutral, itemStyle: { color: "#f59e0b" } },
        { name: "消极", value: s.negative, itemStyle: { color: "#ef4444" } }
      ]
    }]
  });
};

const renderTrend = () => {
  if (!trendChart) return;
  const t = eventData.value.trend || { slots: [], positive: [], neutral: [], negative: [] };
  trendChart.clear();
  trendChart.setOption({
    tooltip: { trigger: "axis" },
    legend: { data: ["积极", "中性", "消极"] },
    xAxis: { type: "category", data: t.slots || [], axisLabel: { rotate: 35 } },
    yAxis: { type: "value" },
    series: [
      { name: "积极", type: "line", smooth: true, data: t.positive || [], itemStyle: { color: "#22c55e" } },
      { name: "中性", type: "line", smooth: true, data: t.neutral || [], itemStyle: { color: "#f59e0b" } },
      { name: "消极", type: "line", smooth: true, data: t.negative || [], itemStyle: { color: "#ef4444" } }
    ]
  });
};

const renderScatter = () => {
  if (!scatterChart) return;
  const d = eventData.value.interaction_scatter || { positive: [], neutral: [], negative: [] };
  scatterChart.clear();
  scatterChart.setOption({
    tooltip: {
      formatter: (p) => {
        const v = p.value || [];
        return `${p.seriesName}<br/>点赞: ${v[0] || 0}<br/>评论: ${v[1] || 0}<br/>${v[2] || ""}`;
      }
    },
    legend: { data: ["积极", "中性", "消极"] },
    xAxis: { type: "value", name: "点赞数量" },
    yAxis: { type: "value", name: "评论数量" },
    series: [
      { name: "积极", type: "scatter", data: d.positive || [], itemStyle: { color: "#22c55e" }, symbolSize: 8 },
      { name: "中性", type: "scatter", data: d.neutral || [], itemStyle: { color: "#f59e0b" }, symbolSize: 8 },
      { name: "消极", type: "scatter", data: d.negative || [], itemStyle: { color: "#ef4444" }, symbolSize: 8 }
    ]
  });
};

const renderGender = () => {
  if (!genderChart) return;
  const g = eventData.value.gender_sentiment || { categories: ["男", "女", "未知"], positive: [], neutral: [], negative: [] };
  genderChart.clear();
  genderChart.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    legend: { data: ["积极", "中性", "消极"] },
    xAxis: { type: "category", data: g.categories || ["男", "女", "未知"] },
    yAxis: { type: "value" },
    series: [
      { name: "积极", type: "bar", stack: "sum", data: g.positive || [], itemStyle: { color: "#22c55e" } },
      { name: "中性", type: "bar", stack: "sum", data: g.neutral || [], itemStyle: { color: "#f59e0b" } },
      { name: "消极", type: "bar", stack: "sum", data: g.negative || [], itemStyle: { color: "#ef4444" } }
    ]
  });
};

const renderAll = async () => {
  await nextTick();
  initCharts();
  renderCloud();
  renderPie();
  renderTrend();
  renderScatter();
  renderGender();
};

const loadEvent = async (id) => {
  try {
    const { data } = await getVisualizationEvent(id);
    eventData.value = data || {};
    await renderAll();
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "加载可视化数据失败");
  }
};

const onFileChange = (file) => {
  fileObj.value = file.raw;
};

const submitCsv = async () => {
  if (!fileObj.value) return ElMessage.warning("请先选择CSV文件");
  uploading.value = true;
  try {
    const form = new FormData();
    form.append("file", fileObj.value);
    const { data } = await uploadVisualizationCsv(form);
    ElMessage.success(`上传成功，事件ID: ${data.event_id}`);
    await router.push(`/visualization/${data.event_id}`);
    await loadEvent(data.event_id);
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "上传失败");
  } finally {
    uploading.value = false;
  }
};

const onResize = () => {
  cloudChart?.resize();
  pieChart?.resize();
  trendChart?.resize();
  scatterChart?.resize();
  genderChart?.resize();
};

onMounted(async () => {
  await loadEvent(route.params.eventId || 1);
  window.addEventListener("resize", onResize);
});

onBeforeUnmount(() => {
  window.removeEventListener("resize", onResize);
  cloudChart?.dispose();
  pieChart?.dispose();
  trendChart?.dispose();
  scatterChart?.dispose();
  genderChart?.dispose();
});
</script>

<style scoped>
.page { background: #f5f7fb; min-height: calc(100vh - 64px); padding: 16px; }
.container { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 16px; }
.card { background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 14px; box-shadow: 0 2px 10px rgba(15,23,42,.04); }
.head-card h2 { margin: 0 0 6px; color: #111827; }
.sub { margin: 0 0 10px; color: #6b7280; }
.uploader-row { display: flex; gap: 10px; align-items: center; }
.grid.two { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.chart.lg { height: 360px; }
.chart.md { height: 320px; }
.summary { color: #374151; line-height: 1.8; margin: 4px 0 10px; }
.list { margin: 0; padding-left: 18px; }
.list li { margin: 6px 0; }
.empty { color: #9ca3af; }
a { color: #2563eb; text-decoration: none; }
a:hover { text-decoration: underline; }
.likes { margin-left: 8px; color: #f59e0b; font-size: 12px; }
@media (max-width: 900px) { .grid.two { grid-template-columns: 1fr; } }
</style>