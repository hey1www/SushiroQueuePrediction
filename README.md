# Sushiro HK Assistant Frontend

这个仓库只保留 GitHub Pages 所需的前端代码和部署工作流。

## 目录

```text
.
├─ .github/workflows/
└─ frontend/
```

## 本地开发

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

默认开发地址：

- 前端：`http://localhost:5173`

## 生产部署

- GitHub Pages 通过 GitHub Actions 构建 `frontend/`
- 生产静态资源路径由 `frontend/.env.production` 中的 `VITE_APP_BASE_PATH` 控制
- 前端运行时请求的后端 API 由 `VITE_API_BASE_URL` 指向外部服务

## 说明

- 本仓库不再追踪 `backend/`、`docs/`、`infra/`、`scripts/` 和 `sushiro-vue/`
- 如果需要后端，请单独放到另一个仓库，或者保留在本地但不要提交到这里
