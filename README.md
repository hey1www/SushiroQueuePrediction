# Sushiro HK Assistant

香港寿司郎排队助手 v1 的独立实现仓库。

本项目严格把参考源码与新系统隔离：

- `sushiro-vue/` 仅作只读参考，不参与新系统运行
- `frontend/` 是新的 Vue 3 + Vite + TypeScript 前端
- `backend/` 是新的 FastAPI + SQLite + APScheduler 后端
- `infra/` 存放 Docker / Synology / Cloudflare Tunnel 配置样例

## 目录

```text
.
├─ backend/
├─ docs/
├─ frontend/
├─ infra/
├─ scripts/
└─ sushiro-vue/   # 仅参考，不参与部署
```

## 本地开发

### 1. 后端

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认情况下：

- 前端：`http://localhost:5173`
- 后端：`http://localhost:8000`
- API 前缀：`/api`

## 已实现的 v1 范围

- 实时看板
- 单店详情页
- 最近 6 小时历史曲线
- 基础 ETA 规则模型
- 最快门店推荐
- SQLite 持久化
- APScheduler 定时采集
- Docker / Cloudflare Tunnel / Synology 部署样例

## 设计原则

- 时间统一按 UTC 存储，前端显示转换为 `Asia/Hong_Kong`
- 前端不直接请求寿司郎官方接口
- `groupqueues` 为空或报错时优雅降级
- 保留原始 JSON，便于后续字段追溯
- 后端采集异常不阻断 API 服务

## 部署

- 前端建议部署到 GitHub Pages
- 后端建议部署到 Synology Docker / Container Manager
- 外部 API 暴露建议通过 Cloudflare Tunnel

具体说明见：

- [架构文档](/Users/heyi/Project/SushiroQueuePrediction/docs/architecture.md)
- [API 文档](/Users/heyi/Project/SushiroQueuePrediction/docs/api.md)
- [数据模型](/Users/heyi/Project/SushiroQueuePrediction/docs/data-model.md)
- [群晖部署说明](/Users/heyi/Project/SushiroQueuePrediction/infra/synology/deployment-notes.md)
