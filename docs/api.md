# API

## `GET /api/health`

返回服务状态、最后一次快照时间和门店数量。

## `GET /api/stores/current`

返回所有门店当前状态。

### Query

- `region`
- `area`
- `open_only=true|false`
- `local_ticket_only=true|false`
- `sort=wait|eta|name`

### Response Highlights

- 门店基础信息
- 当前 `wait`
- 当前 `waitingGroup`
- 当前 `storeQueue`
- `queue_min / queue_max / queue_count / queue_span`
- ETA 估算
- 数据更新时间

## `GET /api/stores/{store_id}`

返回单店静态信息、最新状态、最新 queue 详情和当日摘要。

## `GET /api/stores/{store_id}/history?hours=6`

返回时间序列：

- `wait`
- `waiting_group`
- `queue_max`
- `queue_min`

## `GET /api/stores/{store_id}/analytics`

返回：

- 今日平均 `wait`
- 当前时段历史均值
- 工作日 / 周末平均 wait
- 今日高峰时段
- 建议时段
- 按小时平均 wait
- 按小时平均 queue 推进速度

## `GET /api/recommendations/fastest`

返回当前推荐门店列表。

### Query

- `region`
- `limit`
