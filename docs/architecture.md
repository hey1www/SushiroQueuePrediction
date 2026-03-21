# Architecture

## 总体结构

- `frontend/`
  - Vue 3 + Vite + TypeScript
  - 面向 GitHub Pages 的静态部署
  - 只请求自建后端 API
- `backend/`
  - FastAPI 提供查询 API
  - APScheduler 每 2 分钟采集一次寿司郎公开接口
  - SQLite 保存静态门店、实时快照与 queue 快照
- `infra/`
  - Docker Compose 样例
  - Cloudflare Tunnel 配置样例
  - Synology 部署说明

## 后端职责

- 拉取 `storelist`
- 逐店拉取 `groupqueues`
- 保存原始 JSON 与衍生字段
- 提供当前门店、详情、历史、分析、推荐接口
- 使用规则模型生成基础 ETA

## 数据流

1. APScheduler 触发采集任务
2. 采集器拉取 `storelist`
3. 采集器逐店拉取 `groupqueues`
4. 静态字段 upsert 到 `stores`
5. 当前状态写入 `store_snapshots`
6. queue 信息写入 `queue_snapshots`
7. API 查询最新快照或近 6 小时历史
8. 前端把 UTC 时间转换为香港时间展示

## 降级策略

- `groupqueues` 返回空数组：写入空 queue 快照
- `groupqueues` 返回错误对象：保存错误原文，队列字段按空数组降级
- 单店 queue 拉取失败：不中断整轮采集
- `storelist` 失败：本轮采集失败，但 API 继续返回旧数据

## 部署建议

- 前端：GitHub Pages
- 后端：Synology Docker / Container Manager
- 域名暴露：Cloudflare Tunnel
