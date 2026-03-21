# Data Model

## `stores`

保存门店静态信息。

- `id`
- `name`
- `address`
- `area`
- `region`
- `latitude`
- `longitude`
- `tables_capacity`
- `counters_capacity`
- `seat_config`
- `commencement_date`

## `store_snapshots`

保存每轮采集得到的门店状态快照。

- `ts`
- `store_id`
- `store_status`
- `net_ticket_status`
- `local_ticketing_status`
- `reservation_status`
- `checkin_status`
- `wait`
- `waiting_group`
- `wait_time_counter`
- `wait_time_cap`
- `waiting_group_table`
- `waiting_group_counter`
- `waiting_group_pair`
- `raw_storelist_json`

## `queue_snapshots`

保存 queue 相关快照与衍生字段。

- `ts`
- `store_id`
- `separate_queue`
- `store_queue_json`
- `booth_queue_json`
- `mixed_queue_json`
- `counter_queue_json`
- `store_counter_queue_json`
- `store_booth_queue_json`
- `reservation_queue_json`
- `reservation_counter_queue_json`
- `reservation_booth_queue_json`
- `queue_min`
- `queue_max`
- `queue_count`
- `queue_span`
- `raw_groupqueues_json`

## 索引

- `store_snapshots(store_id, ts)`
- `queue_snapshots(store_id, ts)`
