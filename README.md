# Sushiro HK Assistant Frontend

香港寿司郎排队助手前端。当前仓库只追踪 Vue 3 + Vite + TypeScript 前端代码，以及 GitHub Pages 部署工作流。

前端通过外部 API 拉取实时门店数据、历史走势和分析结果，适合作为静态站点部署到 GitHub Pages。

## 当前功能

- 即时看板：查看全港门店的等候组数、候位组数、显示号码和预估等候时间
- 门店筛选：支持按区域、营业状态、是否可现场派筹和排序方式筛选
- 快速推荐：展示当前建议优先前往的门店和推荐理由
- 门店详情：查看单店最新显示号码、最近 6 小时走势和今日时段观察
- 分析页：查看按小时的历史平均等候、号码推进速度、今日高峰和建议时段

## 技术栈

- Vue 3
- Vue Router 4
- TypeScript
- Vite
- GitHub Actions + GitHub Pages

## 仓库结构

```text
.
├─ .github/workflows/deploy-frontend.yml
├─ frontend/
│  ├─ src/
│  │  ├─ pages/
│  │  ├─ components/
│  │  ├─ api/
│  │  ├─ stores/
│  │  └─ utils/
│  ├─ .env.example
│  ├─ .env.production
│  ├─ package.json
│  └─ vite.config.ts
└─ README.md
```

## 页面路由

- `#/`：即时看板
- `#/stores/:storeId`：门店详情
- `#/analytics`：分析页

项目使用 `createWebHashHistory`，因此可以直接部署到 GitHub Pages，而不需要额外的服务端路由重写。

## 环境变量

`frontend/.env.example`

```bash
VITE_API_BASE_URL=http://127.0.0.1:8000/api
VITE_APP_BASE_PATH=/
```

`frontend/.env.production`

```bash
VITE_API_BASE_URL=https://sushi-api.heyi-direct.site/api
VITE_APP_BASE_PATH=/SushiroQueuePrediction/
```

说明：

- `VITE_API_BASE_URL`：前端请求的后端 API 根地址
- `VITE_APP_BASE_PATH`：静态资源和路由的部署根路径

## 本地开发

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认开发地址为 `http://localhost:5173`。

## 常用脚本

在 `frontend/` 目录下执行：

```bash
npm run dev
npm run build
npm run preview
npm run check
```

## 部署

仓库包含 GitHub Pages 工作流 [deploy-frontend.yml](/Users/heyi/Project/SushiroQueuePrediction/.github/workflows/deploy-frontend.yml)：

- 当 `main` 分支上的 `frontend/**` 或该 workflow 发生变更时自动触发
- 工作流会在 `frontend/` 下执行 `npm ci` 和 `npm run build`
- 构建产物 `frontend/dist` 会被上传并部署到 GitHub Pages

## 说明

- 当前仓库不再追踪 `backend/`、`docs/`、`infra/`、`scripts/` 和 `sushiro-vue/`
- 如果需要后端服务，请单独维护在其他仓库或本地环境中
