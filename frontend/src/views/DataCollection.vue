<template>
  <el-card>
    <h3>数据采集</h3>
    <el-form :model="form" inline>
      <el-form-item label="任务名"><el-input v-model="form.task_name" /></el-form-item>
      <el-form-item label="关键词"><el-input v-model="form.keywords" /></el-form-item>
      <el-button type="primary" @click="submit">开始采集</el-button>
    </el-form>
  </el-card>
</template>

<script setup>
import { reactive } from "vue";
import { ElMessage } from "element-plus";
import { createTask } from "@/api/tasks";

const form = reactive({ task_name: "事件采集任务", keywords: "关键词A,关键词B" });
const submit = async () => {
  const { data } = await createTask(form);
  ElMessage.success(`任务已创建: ${data.task_id}`);
};
</script>