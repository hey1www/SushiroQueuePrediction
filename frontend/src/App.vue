<template>
  <div class="app-shell">
    <header class="topbar">
      <div class="topbar__title-stack">
        <h1>郎來了</h1>
        <p class="topbar__subtitle">—— 香港壽司郎排隊助手</p>
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
