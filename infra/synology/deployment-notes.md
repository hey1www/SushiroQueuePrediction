# Synology Deployment Notes

## 推荐方式

使用群晖 `Container Manager` 直接导入 [docker-compose.yml](/Users/heyi/Project/SushiroQueuePrediction/infra/compose/docker-compose.yml) 或手动创建两个容器：

- `backend`
- `cloudflared`

## 后端容器建议

- 自动重启：开启
- 本地端口：`8000`
- 挂载目录：
  - 宿主机持久化目录 -> 容器 `/app/backend/data`
- 环境变量：
  - 直接使用 `backend/.env`

## Cloudflare Tunnel

- 使用你自己的 tunnel id 和 credentials json
- 将 `api.yourdomain.com` 指向 `http://backend:8000`
- 在 compose 中额外挂载 tunnel credentials json 到 `/etc/cloudflared/<tunnel-id>.json`

## 运行前检查

- `backend/.env` 已配置 CORS 白名单
- 数据库目录具备写权限
- Cloudflare Tunnel 凭证文件已放入容器可读取位置
