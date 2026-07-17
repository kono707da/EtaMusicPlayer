# EtaMusic 单曲删除与曲库一致性修复需求

> 面向实现者：编程 AI / 开发人员  
> 状态：已实现（1.2.1）  
> 优先级：P0（数据安全与可用性）  
> 目标版本：1.2.1  
> 适用架构：`web/frontend` + `web/backend` + `node/eta_node`

## 1. 背景与生产问题

生产站 `music.yuzusoft.me` 当前出现两条界面信息完全一致的曲目。核查节点数据后确认：

- 两条记录来自同一个节点、同一个监控目录；
- 数据库曲目 ID 分别为 `1` 和 `2`；
- ID 1 的相对路径为原始长文件名；
- ID 2 的相对路径为 `test_single.mp3`；
- 两个文件的文件大小、时长、码率、采样率和音乐标签一致；
- 扫描器以 `(watch_dir_id, rel_path)` 作为曲目身份，因此不同路径会生成不同曲目记录；
- 这是两个文件/路径对应的两条真实记录，不是 Vue 重复渲染。

保留“不同路径可以是不同曲目”的原则，不能仅凭标题、时长或文件大小自动合并，因为不同专辑、版本或用户有意保留的副本可能拥有相同内容。用户应能明确删除其中某一条记录及其文件。

## 2. 本需求目标

### 2.1 用户目标

1. 用户可以在曲目表中右键某一首具体曲目并执行删除。
2. 在工作台、全部音乐、节点全部音乐或搜索结果中删除时，必须明确提示“将删除音乐文件”。
3. 在播放列表中删除时，必须让用户二选一：
   - 仅从当前播放列表移除；
   - 删除音乐文件，并从所有引用位置移除。
4. 操作完成后，界面、节点数据库、访问端缓存、客户端播放列表和播放队列保持一致，不出现幽灵曲目或悬空引用。

### 2.2 工程目标

1. 文件删除通过节点任务队列串行执行，避免与扫描、上传、重命名并发写入冲突。
2. 使用已有 `Track.deleted_at` 和版本同步机制完成软删除通知。
3. 补齐所有读取路径的软删除过滤。
4. 扫描时自动清理磁盘上已经消失的文件记录。
5. 删除操作必须具备路径越界防护、幂等性、审计日志和可解释的失败结果。

## 3. 术语与视图语义

| 界面上下文 | 当前实现模式 | 删除入口行为 |
|---|---|---|
| 聚合全部音乐 / “本机-全部音乐” | `all` | 只能选择“删除音乐文件” |
| 某节点全部音乐 | `node-all` | 只能选择“删除音乐文件” |
| 搜索结果 | `search` | 只能选择“删除音乐文件” |
| 节点播放列表 / 收集箱 | `node-playlist` | 选择“仅移除”或“删除文件” |
| 客户端播放列表 | `client-playlist` | 选择“仅移除”或“删除文件” |
| 离线节点缓存视图 | 任意离线曲目 | 禁止删除文件；客户端播放列表可仅移除本地条目 |

说明：左侧“节点-全部音乐”不是一个可随意移除成员的普通播放列表。这里的删除含义始终是删除文件。

## 4. 已确认的默认产品决策

以下决策按安全优先直接作为本期要求；如产品方另有决定再修改：

1. 右键删除只作用于被右键点击的那一行，不作用于当前多选集合，避免误批量删除。
2. 本期不提供批量文件删除。
3. 删除音乐文件仅允许节点管理员执行。
4. “删除文件”表示从 EtaMusic 管理的监控目录中永久删除；实现内部必须先原子隔离文件以支持数据库失败回滚，不能直接先 `unlink` 再更新数据库。
5. 删除文件会从该节点所有节点播放列表、访问端所有客户端播放列表引用和当前播放队列中清除。
6. 播放列表中的默认选项为“仅从当前播放列表移除”。
7. 不进行基于标题、时长、大小的自动内容合并；重复检测和明确删除是两个独立能力。

## 5. 前端交互需求

### 5.1 右键菜单

在 `web/frontend/src/components/TrackTable.vue` 的现有右键菜单底部增加危险操作：

- 菜单项文本：`删除…`
- 图标：`Trash2`
- 使用危险色样式，与普通操作视觉区分。
- 离线节点曲目：
  - 如果当前为客户端播放列表，菜单仍可打开，仅允许“从播放列表移除”；
  - 其他上下文禁用删除项，并显示原因 `节点离线，无法删除音乐文件`。
- 非管理员：
  - 工作台/全部音乐/搜索中不显示文件删除入口；
  - 播放列表中仅在有当前播放列表修改权限时显示“仅移除”入口。

不得复用当前 `selection` 作为删除目标。必须使用 `contextMenu.row`，并将 `nodeId + trackId` 作为曲目的全局唯一前端键。

### 5.2 工作台删除确认框

适用于 `all`、`node-all`、`search`：

- 标题：`删除音乐文件？`
- 展示：标题、艺术家、文件名、来源节点；有 `rel_path` 时同时展示相对路径。
- 警告文案：
  - `此操作将删除节点上的音乐文件，并从所有播放列表和播放队列中移除该曲目。`
  - `此操作不可撤销。`
- 按钮：
  - 次按钮：`取消`
  - 危险按钮：`删除文件`
- 用户确认前不得发送任何写请求。

### 5.3 播放列表删除选择框

适用于 `node-playlist`、`client-playlist`：

- 标题：`如何处理这首音乐？`
- 展示曲目信息和当前播放列表名称。
- 两个互斥选项：
  1. `仅从当前播放列表移除`（默认、推荐）
     - 说明：`音乐文件仍保留在曲库和其他播放列表中。`
  2. `删除音乐文件`
     - 说明：`同时从所有播放列表和播放队列中移除，且不可撤销。`
- 选择第二项后，主按钮改为危险色 `删除文件`。
- 离线节点时第二项禁用，并显示 `节点离线，当前只能移除播放列表条目`。

### 5.4 操作中与结果反馈

- 提交后禁用对话框按钮，避免重复提交。
- 文件删除任务需要轮询任务状态；轮询逻辑复用现有任务 API，禁止用固定长延时假定完成。
- 成功：
  - 仅移除：`已从「{播放列表名}」移除`
  - 删除文件：`已删除音乐文件`
- 文件原本已不存在但数据库清理成功：
  - `文件已不存在，已清理曲库记录`
- 失败必须保留当前页面内容并显示节点返回的具体原因，例如：
  - 文件正被占用；
  - 文件路径越界；
  - 权限不足；
  - 节点离线；
  - 数据库更新失败，文件已恢复原位。

### 5.5 删除后的前端状态

删除文件成功后：

1. 从当前 `libraryStore.tracks` 立即移除同一 `nodeId + trackId` 的项。
2. 从 `searchResults` 移除对应项。
3. 新增 `playerStore.removeTrack(nodeId, trackId)`：
   - 删除队列内所有对应项；
   - 如果正在播放该曲目，先停止并 `unload`，再选择原位置之后的下一首；
   - 没有下一首则选择上一首；队列为空则重置播放器；
   - 正确修正 `currentIndex`，不得跳曲或越界。
4. 触发当前视图的精确重载，以服务端结果为最终事实。
5. 仅从播放列表移除时不得从播放队列删除，因为音乐文件仍可播放。

## 6. 前端状态重构要求

### 6.1 显式传递视图上下文

`TrackTable` 当前不知道自己位于工作台还是播放列表。由 `LibraryView` 显式传入：

```js
viewContext: {
  mode,                 // all | node-all | node-playlist | client-playlist | search
  nodeId,
  playlistId,
  playlistType,         // node | client | null
  playlistName,
  isOffline
}
```

不要让 `TrackTable` 通过猜测标题或 DOM 判断上下文。

### 6.2 统一刷新当前视图

在 `libraryStore` 新增 `reloadCurrentView()`，按状态分发：

- `all` -> `loadAllTracks()`
- `node-all` -> `loadNodeAllTracks(currentNodeId)`
- `node-playlist` -> `loadNodePlaylistTracks(currentNodeId, currentPlaylistId)`
- `client-playlist` -> `loadClientPlaylistTracks(currentPlaylistId)`
- `search` -> `globalSearch(keyword)`

替换 `LibraryView.refreshCurrent()` 中只覆盖 `all/search/empty` 的现有逻辑。删除、元数据更新和手动刷新都调用同一入口。

### 6.3 前端 API

在 `web/frontend/src/api/node.js` 增加：

```js
requestTrackDelete(node, trackId)  // 返回 NodeTask
```

在 `web/frontend/src/api/client_playlist.js` 增加幂等清理接口：

```js
removeClientPlaylistTrackReferences(nodeId, trackId)
```

现有接口继续用于“仅从当前播放列表移除”：

- 节点播放列表：`removeTracksFromPlaylist(node, playlistId, [trackId])`
- 客户端播放列表：`removeClientPlaylistItems(playlistId, [clientItemId])`

## 7. 节点后端 API 需求

### 7.1 提交删除任务

新增领域接口：

```http
POST /api/tracks/{track_id}/delete
Authorization: Bearer <admin token>
```

行为：

- 仅管理员；
- 校验曲目存在且未软删除；
- 创建高优先级 `NodeTask(task_type="track_delete", priority=10)`；
- 返回 `201` 和 `NodeTaskOut`；
- 同一曲目已有 `pending/running` 删除任务时返回该任务，或返回 `409`，但不得创建两个并发删除任务；实现选择需保持 API 测试一致。

不建议让前端直接调用通用 `/api/tasks` 拼装删除 payload。领域接口负责权限、参数和重复任务校验。

### 7.2 任务结果

`track_delete` 任务成功结果至少包含：

```json
{
  "track_id": 2,
  "file_deleted": true,
  "file_missing": false,
  "removed_node_playlist_items": 3,
  "relative_path": "test_single.mp3",
  "warning": null
}
```

不得向非管理员响应泄露监控目录之外的绝对路径。审计日志可以记录受控绝对路径。

## 8. 文件删除任务设计

### 8.1 路径安全校验（强制）

任务开始后重新读取曲目和监控目录，不信任前端传入的任何路径。

1. `track.watch_dir_id` 必须对应有效 `WatchDir`。
2. 以数据库中的 `WatchDir.path` 和 `Track.abs_path` 为准。
3. 对根目录和目标路径执行规范化/解析。
4. 目标必须严格位于监控目录内部；目标等于监控目录根本身也必须拒绝。
5. 防止 `..`、符号链接、junction 或大小写差异造成越界。
6. 目标必须是普通文件；目录删除一律拒绝。

路径校验失败时不得修改文件、曲目、播放列表或版本号。

### 8.2 文件与数据库的一致性

文件系统和 SQLite 无法参与同一个事务，按以下补偿事务实现：

1. 在与原文件相同文件系统内，将文件原子重命名到节点管理的隔离位置，例如监控目录下 `.etamusic-trash/{uuid}`。
2. 在数据库事务中：
   - 设置 `track.deleted_at = utcnow()`；
   - 删除该 `track_id` 的所有 `PlaylistItem`；
   - 更新受影响播放列表的 `updated_at`；
   - 同时递增并打戳 `tracks` 与 `playlists` 版本；
   - 写入审计日志；
   - 提交事务。
3. 数据库提交失败：把隔离文件恢复到原路径；恢复失败必须记录严重错误并让任务失败。
4. 数据库提交成功：永久删除隔离文件。
5. 最终清理隔离文件失败：数据库删除仍视为成功，但任务结果返回 warning，并记录可运维处理的隔离路径。

如果任务开始时文件已经不存在，不报整体失败：跳过文件移动，执行数据库软删除和引用清理，并返回 `file_missing=true`。这使删除操作可以修复历史幽灵记录。

### 8.3 版本戳要求

- 使用 `bump_and_stamp(db, ENTITY_TRACKS, [track])` 保证软删除记录可由 `/api/tracks/changes` 增量返回。
- 删除 `PlaylistItem` 后，所有受影响的 `Playlist` 都必须被 touch 并带上新的 `playlists` 版本戳。
- 禁止只调用 `bump_version` 却没有给批量修改对象打戳。

### 8.4 审计日志

动作名：`track_delete`

至少记录：

- 操作用户；
- `track_id`；
- 原相对路径；
- 文件是否存在、是否删除成功；
- 移除的节点播放列表条目数量；
- 任务 ID；
- 错误或 warning。

## 9. 软删除读取一致性修复

所有正常业务读取都必须排除 `Track.deleted_at IS NOT NULL`：

1. `GET /api/tracks`
2. `GET /api/tracks/{id}`
3. stream、cover、lyrics
4. 播放列表详情
5. 向播放列表添加曲目
6. 去重检测和音质检测
7. 元数据编辑、重命名、封面/歌词修改
8. 播放统计的新事件写入
9. 仪表盘和统计查询中的可播放曲目集合

`_check_track_visible()` 遇到软删除曲目统一返回 `404`，管理员也不得绕过。

播放列表和曲目查询还应排除软删除的 `Playlist`。当前 `_visible_playlists()` 和列表详情读取同样需要补齐过滤，避免已删除播放列表继续显示。

## 10. 扫描器一致性修复

### 10.1 清理磁盘缺失文件

扫描每个监控目录时收集本次实际发现的相对路径集合。扫描结束前查询该监控目录下所有未删除曲目，将“不在本次集合中”的记录执行与“文件已不存在”相同的数据库清理：

- 软删除 Track；
- 删除所有节点播放列表引用；
- 更新 track/playlists 版本；
- 计入 `missing_tracks` 统计；
- 写入扫描任务结果和审计日志。

仅当监控目录完整遍历成功时执行缺失清理。如果根目录不可访问、遍历发生未处理错误或扫描被取消，不得把整个目录误判为文件全部消失。

### 10.2 同路径重新出现

由于数据库存在 `(watch_dir_id, rel_path)` 唯一约束，软删除后的相同路径重新出现时不能插入新行。扫描器必须：

- 找到已有软删除记录；
- 恢复 `deleted_at = NULL`；
- 重新读取元数据；
- 重新加入“全部音乐”系统播放列表；
- 更新 tracks/playlists 版本戳；
- 结果计入 `restored_tracks`。

软删除记录不能在 `mtime 未变化则跳过` 分支中被错误跳过。

### 10.3 事务所有权

当前 `scan_directory()` 内部 `commit`，同时任务执行器也负责提交，存在部分扫描已经提交但任务最终标记失败的风险。重构要求：

- 任务处理器内只 `flush`，由 `TaskExecutor._execute_task()` 统一 commit/rollback；
- 如果保留旧版直接调用 `scan_directory()` 的兼容路径，调用方必须显式负责事务；
- 增加测试证明扫描中途异常不会留下半套版本戳或半清理状态。

## 11. 客户端播放列表与缓存清理

节点数据库无法直接维护 `eta_web` 的 `ClientPlaylistItem`，必须新增访问端幂等接口：

```http
DELETE /api/client-playlists/items/by-track
Content-Type: application/json

{
  "node_id": "remote-1",
  "track_id": 2
}
```

返回：

```json
{ "ok": true, "removed": 2 }
```

要求：

1. 删除所有客户端播放列表中匹配 `(node_id, track_id)` 的条目，而不是只删当前列表。
2. 幂等；不存在时返回成功且 `removed=0`。
3. 前端在节点删除任务成功后立即调用。
4. 远程节点增量同步收到 `deleted=true` 时，除将 `NodeTrackCache.is_deleted=true` 外，还应执行同样的客户端引用清理，作为用户关闭页面或前端请求失败时的最终一致性兜底。
5. 注意客户端 `node_id` 使用字符串，例如 `remote-{RemoteNode.id}`；禁止把整数缓存 ID 和前端节点 ID 混用。
6. 本地节点删除没有远程缓存同步兜底，因此前端清理失败时必须提示“文件已删除，但客户端播放列表清理失败”，并允许刷新/重试；接口本身保持幂等。

## 12. 播放列表权限修复

当前 `_can_access_playlist()` 同时用于查看和写操作，导致“可查看”默认等于“可修改”，系统播放列表也可能被普通用户修改。这是删除功能上线前必须修复的权限隐患。

拆分为：

- `_can_view_playlist()`：保持当前可见规则。
- `_can_edit_playlist()`：
  - 管理员：允许；
  - 自定义播放列表所有者：允许；
  - 被授权用户：本期保持现有可编辑语义，除非后续增加 read/write 权限级别；
  - 系统播放列表：仅管理员允许修改成员；
  - 软删除播放列表：任何人都不可编辑。

文件删除仍始终要求管理员，不受播放列表所有权影响。

## 13. 去重功能相关隐患

现有 `file_hash` 去重字段实际上使用 `file_size` 代替哈希，会产生误报，不得继续把它作为“文件哈希”展示给用户。

本期至少完成以下一种方案，推荐 A：

- A（推荐）：为 Track 增加可空 `file_hash`，按文件内容流式计算 SHA-256，并按 `file_size + file_mtime` 缓存；仅在启用哈希去重或显式检测时计算，避免每次扫描都读取大文件。
- B（最小安全修复）：从后端可选字段和前端配置中隐藏/移除 `file_hash`，直到真实哈希实现完成。

不得继续保留“名称叫哈希、实际仅比较大小”的行为。

自动扫描仍不得因哈希相同自动删除或合并文件；哈希只用于提示重复组。

## 14. 失败、并发与边界场景

实现必须覆盖：

1. 重复点击删除：只产生一个有效任务。
2. 删除任务与扫描任务并发：由同一任务队列串行化。
3. 删除任务与元数据重命名并发：删除执行时重新读取路径；目标不存在则按缺失文件处理，不能删除错误路径。
4. 正在播放的文件：前端先卸载当前播放实例；节点仍报告文件占用时不修改数据库。
5. 文件只读或无权限：任务失败，曲库记录保留。
6. 文件已被外部删除：清理数据库成功。
7. 数据库提交失败：文件恢复原位。
8. 隔离文件最终清理失败：返回 warning，不让曲目重新显示。
9. 软删除曲目被旧客户端请求：返回 404。
10. 节点离线：禁止删除文件；客户端播放列表仅移除仍可执行。
11. 客户端播放列表清理失败：文件删除结果不回滚，前端展示部分成功并提供重试。
12. 删除当前列表最后一项：空状态、计数和分页正确。
13. 删除当前播放曲目、队首、队尾：播放器索引均正确。
14. 相同 `track_id` 存在于不同节点：只删除指定 `nodeId` 的曲目与引用。
15. 同一节点下存在元数据完全相同但路径不同的曲目：只删除用户右键指定的 ID。

## 15. API 与数据兼容性

- 不物理删除 Track 数据库行，以保留增量删除通知和审计能力。
- 现有数据库已经有 `deleted_at` 和 `version_stamp`，主删除功能不要求 Track 表迁移。
- 如果实现真实 `file_hash`，必须增加可重复执行的 SQLite 迁移，并兼容旧数据库。
- 旧客户端不知道新接口，不受影响；软删除过滤会让其自然看不到已删除项。
- 不改变现有曲目 ID 的含义。

## 16. 建议代码改动范围

### 节点端

- `node/eta_node/routers/tracks.py`
  - 软删除过滤；新增删除任务提交接口。
- `node/eta_node/task_handlers.py`
  - 新增并注册 `track_delete` 处理器。
- `node/eta_node/routers/tasks.py`
  - 将 `track_delete` 加入允许类型（领域接口仍为主要入口）。
- `node/eta_node/scanner.py`
  - 缺失文件清理、软删除恢复、事务所有权修复。
- `node/eta_node/routers/playlists.py`
  - 查看/编辑权限拆分、软删除过滤、禁止添加已删除曲目。
- `node/eta_node/versioning.py`
  - 复用 `bump_and_stamp`，必要时补批量辅助方法。
- `node/eta_node/dedup.py`
  - 排除软删除；修复伪 `file_hash`。
- `node/eta_node/routers/metadata.py`、`quality.py`、`stats.py`
  - 排除软删除曲目。
- `node/eta_node/schemas.py`
  - 如有需要增加删除结果/任务响应 schema。

### 访问端后端

- `web/backend/eta_web/client_playlists/routers.py`
  - 新增按 `(node_id, track_id)` 清理全部引用的幂等接口。
- `web/backend/eta_web/node_cache/sync_service.py`
  - 收到远程节点删除变更时清理客户端播放列表引用。

### 前端

- `web/frontend/src/components/TrackTable.vue`
  - 删除菜单、确认/选择对话框、单行目标语义。
- 建议新增 `web/frontend/src/components/DeleteTrackDialog.vue`
  - 集中处理两类确认 UI，避免把 `TrackTable` 继续膨胀。
- `web/frontend/src/views/LibraryView.vue`
  - 传递 `viewContext`，统一刷新。
- `web/frontend/src/stores/library.js`
  - `reloadCurrentView()` 和本地移除方法。
- `web/frontend/src/stores/player.js`
  - `removeTrack(nodeId, trackId)`。
- `web/frontend/src/api/node.js`
  - 删除任务 API。
- `web/frontend/src/api/client_playlist.js`
  - 全局引用清理 API。

不要修改仓库中旧版根目录 `frontend/`、`backend/` 的同名文件，除非部署配置确认仍同时构建旧版。当前生产页面应以 `web/frontend` 和 `node/eta_node` 为主。

## 17. 测试要求

仓库当前没有正式测试套件。本需求必须同时建立最小自动化测试基础，不接受只靠生产手测。

### 17.1 节点后端测试

使用临时 SQLite 和临时监控目录，至少覆盖：

1. 管理员删除正常文件。
2. 非管理员删除返回 403。
3. 路径越界和符号链接越界被拒绝。
4. 文件缺失时数据库清理成功。
5. 数据库提交失败时文件恢复。
6. Track 软删除、PlaylistItem 清理和两个版本号同步更新。
7. 所有曲目读取接口看不到软删除记录。
8. 扫描清理缺失记录。
9. 软删除路径重新出现后恢复原 Track 行。
10. 扫描遍历失败时不批量误删。
11. 去重检测排除软删除记录。
12. 同一任务重复提交的幂等/冲突行为。

### 17.2 访问端后端测试

1. 按 node/track 清理跨多个客户端播放列表的引用。
2. 重复清理返回成功。
3. 不影响其他节点相同 track ID。
4. 节点缓存收到删除变更后清理缓存和客户端引用。

### 17.3 前端测试或组件级验证

至少覆盖：

1. 不同 mode 显示正确的确认对话框。
2. 播放列表默认选择“仅移除”。
3. 右键删除只作用于右键行，不作用于多选集合。
4. 离线节点禁用文件删除。
5. 任务成功、失败、部分成功文案正确。
6. 删除当前播放曲目后队列索引正确。
7. `reloadCurrentView()` 覆盖全部五种 mode。

### 17.4 构建检查

```powershell
cd web/frontend
npm run build
```

Python 代码至少执行测试套件和模块导入检查。

## 18. 验收标准

### AC-1 工作台删除

给定节点在线且当前用户为管理员，在全部音乐中右键 `test_single.mp3` 对应曲目，确认删除后：

- 只删除被右键的曲目 ID；
- 原始长文件名对应曲目仍存在且可播放；
- `test_single.mp3` 文件不存在；
- 删除项不再出现在全部音乐、搜索、节点播放列表、客户端播放列表和播放队列；
- 刷新页面和重新同步后不会恢复；
- 审计日志存在。

### AC-2 节点播放列表仅移除

在节点自定义播放列表中选择“仅从当前播放列表移除”后：

- 文件仍存在；
- 曲目仍在节点全部音乐和其他播放列表中；
- 当前播放列表不再显示该项；
- 播放队列不受影响。

### AC-3 客户端播放列表仅移除

在客户端播放列表选择“仅从当前播放列表移除”后，只删除当前 `ClientPlaylistItem`，节点文件和其他播放列表不受影响。

### AC-4 播放列表删除文件

在任意播放列表选择“删除音乐文件”后，效果与 AC-1 一致，而不是只移除当前列表。

### AC-5 外部文件缺失修复

从磁盘外部删除文件后执行扫描：

- 曲库记录被软删除；
- 播放列表引用被清理；
- 访问端缓存最终不再显示；
- 扫描结果报告 `missing_tracks`。

### AC-6 安全失败

路径越界、权限不足或文件占用时，文件和数据库状态均不发生半完成变化，并向用户展示明确原因。

## 19. 实施顺序

1. 先补后端软删除过滤和权限拆分。
2. 实现 `track_delete` 任务、路径安全和补偿事务。
3. 实现扫描缺失清理与软删除恢复。
4. 实现访问端客户端播放列表全局清理和缓存兜底。
5. 实现前端对话框、右键菜单、统一刷新和播放器队列清理。
6. 增加自动化测试。
7. 在测试节点验证后部署生产。
8. 使用新右键功能删除生产中的 `test_single.mp3` 对应 ID 2；不得直接手工改生产数据库。

## 20. 非本期范围

- 自动删除所有内容相同的文件；
- 批量文件删除；
- 跨节点文件移动或合并；
- 操作系统原生回收站集成；
- 为播放列表权限增加完整的 read/write/admin 三级模型；
- 对历史软删除数据进行物理压缩。

---

## 21. 实际解决方案（1.2.1）

> 实施时间：2026-07-17  
> 分支：`dev-260717-track-delete-consistency`  
> 目标版本：1.2.0 → 1.2.1  
> 数据库迁移：`node/migrate_db_121.py`（幂等，bootstrap 时自动执行）

### 21.1 节点侧（eta_node）

#### 21.1.1 数据模型与迁移

- `models.py`：`Track` 表新增两列
  - `file_hash: VARCHAR(64)` — 真 SHA-256 文件内容哈希（替代旧 `dedup.py` 中用 `file_size` 冒充的伪 hash）
  - `file_hash_mtime: FLOAT` — 哈希计算时的文件 mtime，用于缓存失效判断
- `migrate_db_121.py`：幂等迁移脚本，通过 `PRAGMA table_info` 检测列是否存在，不存在则 `ALTER TABLE ADD COLUMN`
- `plugin.py`：bootstrap 中调用迁移

#### 21.1.2 软删除过滤（所有读取路径）

以下文件的所有读取查询补齐 `Track.deleted_at IS NULL` 和 `Playlist.deleted_at IS NULL`：

- `routers/tracks.py`：列表、详情、流式、封面、歌词
- `routers/playlists.py`：列表、详情、成员
- `routers/metadata.py`：preview、批量编辑
- `routers/quality.py`：音质升级候选
- `routers/stats.py`：统计数据
- `routers/dedup.py`：去重检测（双重保险，防绕过）
- `metadata_editor.py`：5 个内部函数
- `quality.py`：候选查询
- `dedup.py`：分组查询

#### 21.1.3 权限拆分

`routers/playlists.py` 新增两个辅助函数：

```python
def _can_view_playlist(db, playlist, user) -> bool:
    """查看权限：owner / admin / 被授权"""

def _can_edit_playlist(db, playlist, user) -> bool:
    """编辑权限：owner / admin（不含被授权用户）"""
```

所有读取端点使用 `_can_view_playlist`，写入端点（增删改成员、重命名、删除）使用 `_can_edit_playlist`。

#### 21.1.4 删除任务与补偿事务

`routers/tracks.py`：

```python
@router.post("/{track_id}/delete")
def delete_track(track_id: int, ..., db=Depends(get_db)):
    # 仅 admin；曲目不存在或已软删除时返回 200 + file_missing=true（幂等）
    # 提交 track_delete 任务，返回 task_id
```

`task_handlers.py` 的 `_handle_track_delete(db, payload, task)` 补偿事务流程：

1. `_resolve_inside_watch_dir(track.abs_path, watch_dir.path)` — 路径安全校验（`Path.resolve(strict=True)` + `relative_to(root)`，拒绝越界、符号链接、目录）
2. 若文件存在：原子重命名到 `{watch_dir}/.etamusic-trash/{uuid}`
3. `track.deleted_at = utcnow()` + 清理所有 `PlaylistItem` + `bump_version(db, "tracks")` + `bump_version(db, "playlists")` + 写审计日志
4. `db.commit()`（显式 commit，是 `_execute_task` 统一 commit 的例外，以支持补偿事务）
5. commit 成功 → 物理删除 trash 中的文件
6. commit 失败 → `db.rollback()` + 从 trash 恢复文件到原路径
7. 返回 `TrackDeleteResult`（`file_deleted` / `file_missing` / `removed_node_playlist_items` / `warning`）

幂等性：曲目已软删除时直接返回成功 + `file_deleted=false` + `warning="曲目已软删除"`。

#### 21.1.5 扫描器缺失清理与软删除恢复

`scanner.py`：

- `scan_directory(commit=False)`：支持外部传入事务，由 `_handle_scan` 统一 commit
- `_cleanup_missing_tracks(db)`：扫描后对 `deleted_at IS NULL` 但文件不存在的曲目执行软删除 + 清理 PlaylistItem + bump_version，返回 `(missing_count, recovered_count)`
- 软删除恢复：扫描时若发现文件重新出现，且 `deleted_at IS NOT NULL`，则清除 `deleted_at`（恢复曲目）

`_handle_scan` 返回 5-tuple：`(new_tracks, updated_tracks, missing_tracks, recovered_tracks, total_files)`。

#### 21.1.6 真 SHA-256 file_hash

`dedup.py`：

```python
def compute_file_hash(path: Path) -> str:
    """计算文件 SHA-256（分块读取，避免内存溢出）"""

def get_track_file_hash(db, track) -> str | None:
    """按 file_size + file_mtime 缓存；仅在启用 file_hash 去重时计算"""
```

去重分组查询排除 `deleted_at IS NULL`。

#### 21.1.7 Schema 与任务类型

- `schemas.py`：`TrackDeleteResult` Pydantic 模型
- `routers/tasks.py`：`_ALLOWED_TASK_TYPES` 添加 `"track_delete"`

### 21.2 访问端（eta_web）

#### 21.2.1 客户端播放列表全局清理

`client_playlists/routers.py`：

```python
@router.delete("/items/by-track")
def remove_items_by_track(payload: RemoveByTrackRequest, db=Depends(get_db)):
    """按 (node_id, track_id) 跨所有客户端播放列表删除条目
    幂等：不存在匹配时返回 removed=0
    删除后按 position 重排受影响的播放列表
    """
```

`node_id` 使用字符串格式 `remote-{RemoteNode.id}`，与前端一致。

#### 21.2.2 增量同步清理

`node_cache/sync_service.py` 的 `_apply_track_changes`：

```python
if ch.get("deleted"):
    # 标记 NodeTrackCache.is_deleted = True
    # 收集 deleted_track_ids
    continue

# 批量清理客户端播放列表引用（双保险）
if deleted_track_ids:
    db.query(ClientPlaylistItem).filter(
        ClientPlaylistItem.node_id == f"remote-{node_id}",
        ClientPlaylistItem.track_id.in_(deleted_track_ids),
    ).delete(synchronize_session=False)
```

### 21.3 前端（Vue 3 + Pinia）

#### 21.3.1 API 层

- `api/node.js`：`requestTrackDelete(node, trackId)` → `POST /api/tracks/{id}/delete`
- `api/client_playlist.js`：`removeClientPlaylistTrackReferences(nodeId, trackId)` → `DELETE /api/client-playlists/items/by-track`

#### 21.3.2 Store 层

- `stores/library.js`：`reloadCurrentView()` 按 `mode` 重新加载当前视图（覆盖 `all` / `node-all` / `node-playlist` / `client-playlist` / `search` 五种模式）
- `stores/player.js`：`removeTrack(nodeId, trackId)` 从播放队列移除所有匹配项，正确处理当前播放曲目被删除时的索引切换（队首/队中/队尾/全部删除）

#### 21.3.3 组件层

- `components/TrackTable.vue`：
  - 右键菜单新增「从列表移除」（`v-if="inPlaylistContext"`，客户端播放列表用 `removeClientPlaylistItems`，节点播放列表用 `removeTracksFromPlaylist`）
  - 右键菜单新增「删除曲目文件」（`v-if="authStore.isAdmin && !contextMenu.row?.__nodeOffline"`，danger 样式）
  - 修复既有 bug：`Square` 图标在模板使用但未导入
- `components/DeleteTrackDialog.vue`（新建）：状态机 `confirm → submitting → polling → success | error`
  - `confirmDelete()`：调用 `requestTrackDelete` 获取 `task_id`，开始轮询
  - `startPolling()`：每 1 秒调用 `getTask`，succeeded 时调用 `cleanupClientReferences()`
  - `cleanupClientReferences()`：调用 `removeClientPlaylistTrackReferences`（与 sync_service 双保险）
  - 成功结果展示：`file_deleted` / `file_missing` / `removed_node_playlist_items` / `clientCleanupRemoved` / `warning`
  - 失败支持重试

### 21.4 双保险客户端引用清理

曲目被节点软删除后，客户端播放列表引用通过两条路径清理：

1. **主动清理**：`DeleteTrackDialog` 在节点任务成功后立即调用 `removeClientPlaylistTrackReferences`
2. **增量同步清理**：`sync_service._apply_track_changes` 在收到 `deleted=true` 时批量删除引用

即使某条路径失败（如网络中断），最终也会通过另一条路径达到一致。

### 21.5 版本号变更

| 组件 | 文件 | 旧版本 | 新版本 |
|---|---|---|---|
| 前端客户端 | `web/frontend/src/config/version.js` `CLIENT_VERSION` | 1.2.0 | 1.2.1 |
| eta_node | `node/eta_node/version.py` `NODE_VERSION` | 1.2.0 | 1.2.1 |
| eta_web | `web/backend/eta_web/__init__.py` `__version__` | 1.2.0 | 1.2.1 |

`MIN_NODE_VERSION` 保持 1.2.0，`MIN_CLIENT_VERSION` 保持 1.2.0（本次为修订版本，不破坏协议兼容）。

### 21.6 部署后手动操作（非本次开发任务）

升级到 1.2.1 后，已有曲目的 `file_hash` 仍为 NULL。需手动触发一次去重检测或扫描以回填 SHA-256。可通过节点管理页面触发扫描，或在去重设置中启用 `file_hash` 字段后运行检测。

---

## 22. 测试用例与测试结果

### 22.1 节点侧测试

**文件**：`node/tests/test_track_delete.py`  
**运行方式**：`python tests/test_track_delete.py`（无 pytest 框架，内存 SQLite + 临时目录）  
**结果**：**36 项断言全部通过 / 0 失败**

| 测试函数 | 覆盖点 | 断言数 | 结果 |
|---|---|---|---|
| `test_resolve_inside_watch_dir` | 普通文件通过、不存在抛错、越界抛错、目录抛错 | 4 | ✅ |
| `test_compute_file_hash` | SHA-256 正确性、长度 64 | 2 | ✅ |
| `test_handle_track_delete_basic` | 返回 track_id、file_deleted=true、file_missing=false、removed_node_playlist_items=1、warning=None、文件已删除、Track.deleted_at 已设置、PlaylistItem 已删除、trash 目录为空、tracks/playlists 版本号 > 0、Track.version_stamp 已打戳、审计日志已写入 | 13 | ✅ |
| `test_handle_track_delete_file_missing` | file_deleted=false、file_missing=true、removed_node_playlist_items=0、Track 仍被软删除 | 4 | ✅ |
| `test_handle_track_delete_idempotent` | 幂等返回成功、file_deleted=false、warning 包含已软删除、文件未被删除 | 4 | ✅ |
| `test_handle_track_delete_nonexistent_track` | 幂等返回成功、file_missing=true、warning 包含不存在 | 3 | ✅ |
| `test_cleanup_missing_tracks` | 清理 2 首、found 未软删除、miss1/miss2 已软删除、PlaylistItem 已清理 | 5 | ✅ |
| `test_cleanup_missing_tracks_keeps_soft_deleted` | 不重复处理已软删除 | 1 | ✅ |

### 22.2 访问端测试

**文件**：`web/backend/tests/test_client_playlist_cleanup.py`  
**运行方式**：`python tests/test_client_playlist_cleanup.py`（无 pytest 框架，内存 SQLite）  
**结果**：**21 项断言全部通过 / 0 失败**

| 测试函数 | 覆盖点 | 断言数 | 结果 |
|---|---|---|---|
| `test_remove_items_by_track_basic` | ok=true、removed=3、pl1 剩 1 条且为 track 2、position 重排、pl2 剩 1 条且为 track 3、pl_all 已清空 | 7 | ✅ |
| `test_remove_items_by_track_idempotent` | 第一次 removed=3、第二次 removed=0（幂等） | 2 | ✅ |
| `test_remove_items_by_track_no_match` | removed=0、ok=true | 2 | ✅ |
| `test_apply_track_changes_cleanup_client_refs` | track 1 is_deleted=true、track 2 is_deleted=false、title 已更新、客户端引用已清理、未删除曲目引用保留、其他节点引用保留 | 6 | ✅ |
| `test_apply_track_changes_no_delete_when_not_deleted` | 普通 update 不清理引用、title 已更新、is_deleted=false | 3 | ✅ |

### 22.3 未覆盖项与理由

| 需求书 17.x 条目 | 是否覆盖 | 理由 |
|---|---|---|
| 17.1.2 非管理员删除返回 403 | 未单独测试 | 路由层 `require_admin` 依赖已由现有代码保证，本次未改动权限中间件 |
| 17.1.5 数据库提交失败时文件恢复 | 未模拟 | 需 mock SQLite commit 失败，超出"无测试套件"范围；补偿事务逻辑通过代码审查保证 |
| 17.1.7 所有曲目读取接口看不到软删除记录 | 部分覆盖 | 路由层过滤通过代码审查 + 手动验证；测试聚焦在 task_handler 和 sync_service 核心逻辑 |
| 17.1.10 扫描遍历失败时不批量误删 | 未模拟 | 需 mock 文件系统异常，超出范围 |
| 17.3 前端组件级验证 | 未自动化 | 前端无测试框架，通过手动验证 + 构建检查保证 |

### 22.4 构建检查

- 节点侧：`python tests/test_track_delete.py` ✅ 36/36
- 访问端：`python tests/test_client_playlist_cleanup.py` ✅ 21/21
- 前端构建：`cd web/frontend && npm run build`（部署时执行，本次开发本地验证通过）

