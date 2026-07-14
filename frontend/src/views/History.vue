<template>
  <el-card>
    <h3>历史记录</h3>

    <el-space style="margin-bottom: 12px;">
      <el-input v-model="query.event_name" placeholder="事件名称搜索" style="width: 220px;" clearable />
      <el-button type="primary" @click="load">查询</el-button>
    </el-space>

    <el-table :data="rows" stripe>
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="event_name" label="事件名称" min-width="180" />
      <el-table-column prop="exported_count" label="导出次数" width="100" />
      <el-table-column prop="created_at" label="创建时间" width="180" />
      <el-table-column label="操作" width="300">
        <template #default="{ row }">
          <el-button size="small" @click="viewDetail(row.id)">详情</el-button>
          <el-button size="small" type="success" @click="downloadExcel(row.id)">Excel</el-button>
          <el-button size="small" type="danger" @click="downloadPdf(row.id)">PDF</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-pagination
      style="margin-top:12px;"
      background
      layout="total, prev, pager, next"
      :total="total"
      :current-page="query.page"
      :page-size="query.page_size"
      @current-change="onPageChange"
    />

    <el-dialog v-model="detailVisible" title="历史记录详情" width="760px">
      <pre style="white-space: pre-wrap; max-height: 500px; overflow:auto;">{{ detailText }}</pre>
    </el-dialog>
  </el-card>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { listHistory, getHistoryDetail, exportHistoryExcel, exportHistoryPdf } from "@/api/history";

const rows = ref([]);
const total = ref(0);
const query = reactive({ page: 1, page_size: 10, event_name: "" });

const detailVisible = ref(false);
const detailText = ref("");

const saveBlob = (blob, filename) => {
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(link.href);
};

const load = async () => {
  try {
    const { data } = await listHistory(query);
    rows.value = data.rows || [];
    total.value = data.total || 0;
  } catch (e) {
    ElMessage.error("加载历史记录失败");
  }
};

const onPageChange = (p) => {
  query.page = p;
  load();
};

const viewDetail = async (id) => {
  try {
    const { data } = await getHistoryDetail(id);
    detailText.value = JSON.stringify(data, null, 2);
    detailVisible.value = true;
  } catch {
    ElMessage.error("获取详情失败");
  }
};

const downloadExcel = async (id) => {
  try {
    const { data } = await exportHistoryExcel(id);
    saveBlob(data, `history_${id}.xlsx`);
    ElMessage.success("Excel 导出成功");
    load();
  } catch {
    ElMessage.error("Excel 导出失败");
  }
};

const downloadPdf = async (id) => {
  try {
    const { data } = await exportHistoryPdf(id);
    saveBlob(data, `history_${id}.pdf`);
    ElMessage.success("PDF 导出成功");
    load();
  } catch {
    ElMessage.error("PDF 导出失败");
  }
};

onMounted(load);
</script>