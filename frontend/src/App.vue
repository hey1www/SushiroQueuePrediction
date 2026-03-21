<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <h1>朗来了 —— 香港寿司郎排队助手</h1>
      </div>
      <nav class="topnav">
        <RouterLink to="/">即時看板</RouterLink>
        <RouterLink to="/analytics">分析頁</RouterLink>
      </nav>
    </header>
    <main class="page-frame">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from "vue-router";
</script>
