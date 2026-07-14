<template>
  <div>
    <HeaderNav />
    <div style="padding:16px;"><router-view /></div>
  </div>
</template>
<script setup>
import HeaderNav from "@/components/HeaderNav.vue";
</script>