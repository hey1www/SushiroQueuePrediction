<template>
  <div class="app-shell">
    <header class="topbar">
      <div>
        <p class="eyebrow">Hong Kong Queue Assistant v1</p>
        <h1>寿司郎香港排队助手</h1>
      </div>
      <nav class="topnav">
        <RouterLink to="/">实时看板</RouterLink>
        <RouterLink to="/analytics">分析页</RouterLink>
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
