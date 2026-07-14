<template>
  <el-card>
    <h3>情感分析</h3>

    <el-row :gutter="16">
      <el-col :span="12">
        <el-card>
          <h4>单条语句分析</h4>
          <el-input
            v-model="singleText"
            type="textarea"
            :rows="5"
            placeholder="输入一句话..."
          />
          <el-button type="primary" style="margin-top:10px" @click="predictOne">开始分析</el-button>
          <div style="margin-top:12px;">结果：{{ singleResult }}</div>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card>
          <h4>CSV 文件分析</h4>
          <el-input v-model="textColumn" placeholder="文本列名（默认 展示内容）" style="margin-bottom:10px;" />
          <el-upload
            :auto-upload="false"
            :limit="1"
            accept=".csv"
            :on-change="onFileChange"
            :show-file-list="true"
          >
            <el-button>选择 CSV 文件</el-button>
          </el-upload>
          <el-button type="success" style="margin-top:10px" @click="predictCsv">上传并分析</el-button>
          <div style="margin-top:12px;">{{ csvMsg }}</div>
          <div style="margin-top:6px;color:#666;">
            正面: {{ stat.positive }} / 中性: {{ stat.neutral }} / 负面: {{ stat.negative }}
          </div>
        </el-card>
      </el-col>
    </el-row>
  </el-card>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import axios from "axios";

const singleText = ref("这次活动太棒了，我非常满意！");
const singleResult = ref("-");
const textColumn = ref("展示内容");
const csvMsg = ref("-");
const fileObj = ref(null);
const stat = ref({ positive: 0, neutral: 0, negative: 0 });

const onFileChange = (file) => {
  fileObj.value = file.raw;
};

const predictOne = async () => {
  try {
    const res = await axios.post("/api/analysis/predict", { text: singleText.value });
    singleResult.value = `label=${res.data.label}, score=${res.data.score}`;
  } catch (e) {
    ElMessage.error(e?.response?.data?.detail || "单句分析失败");
  }
};

const parseFileName = (contentDisposition) => {
  if (!contentDisposition) return "predicted_result.csv";
  const m1 = contentDisposition.match(/filename\*=UTF-8''([^;]+)/i);
  if (m1 && m1[1]) return decodeURIComponent(m1[1]);
  const m2 = contentDisposition.match(/filename="([^"]+)"/i);
  if (m2 && m2[1]) return m2[1];
  return "predicted_result.csv";
};

const predictCsv = async () => {
  if (!fileObj.value) {
    ElMessage.warning("请先选择 CSV 文件");
    return;
  }

  try {
    const formData = new FormData();
    formData.append("file", fileObj.value);
    formData.append("text_column", textColumn.value || "展示内容");

    const res = await axios.post("/api/analysis/predict_csv", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      responseType: "blob",
      validateStatus: (status) => status >= 200 && status < 500
    });

    if (res.status !== 200) {
      // 后端报错也可能以 blob 返回，转文本看 detail
      const errText = await res.data.text();
      throw new Error(errText || `CSV 分析失败，状态码 ${res.status}`);
    }

    const filename = parseFileName(res.headers["content-disposition"]);
    const blob = new Blob([res.data], { type: "text/csv;charset=utf-8;" });

    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);

    stat.value = {
      positive: Number(res.headers["x-stat-positive"] || 0),
      neutral: Number(res.headers["x-stat-neutral"] || 0),
      negative: Number(res.headers["x-stat-negative"] || 0)
    };

    csvMsg.value = "CSV 分析完成，结果已下载。";
    ElMessage.success("CSV 分析成功");
  } catch (e) {
    console.error(e);
    ElMessage.error("分析CSV文件失败");
    csvMsg.value = "分析失败，请检查文件格式或列名";
  }
};
</script>