# 并发整改报告（Docker 化前最后一轮）

范围：仅两项——① 业务流水号生成并发冲突，② 会议室预约审批并发冲突。不涉及权限矩阵、Docker/Nginx/Kylin V10、B2 功能。

---

## 一、业务流水号并发问题

### 1. 原问题

`app/utils/serial_no.py::generate_daily_serial` 原实现是"查询当日同前缀最大编号 → +1"：

```python
rows = db.query(column).filter(column.like(f"{full_prefix}%")).all()
max_seq = max(...)
return f"{full_prefix}{max_seq + 1:04d}"
```

这是"查询-计算-写入"三段式，中间没有任何数据库级互斥。在多 Uvicorn worker / 多容器场景下，两个并发请求可以同时查到相同的 `max_seq`，各自生成同一个编号，最终两条业务记录（Appeal/MeetingRoomBooking/GovMeetingApply）拿到完全相同的 `appeal_no`/`booking_no`/`apply_no`，第二个 INSERT 时才会因 `unique=True` 报 `IntegrityError`，且不保证一定报错在这一层被正确处理。确认调用点：`appeal_repo.generate_appeal_no`、`meeting_room_repo.generate_booking_no`、`gov_meeting_repo.generate_apply_no`，共 3 处，分别在 `submit_appeal`、`submit_booking`、`submit_apply` 内被调用。

### 2. 最终方案

新增 `sys_daily_serial` 计数表（`business_type`, `business_date`, `current_value`，唯一约束 `(business_type, business_date)`），编号生成拆成两步：

1. **确保计数行存在**（`_ensure_counter_row`）：`INSERT IGNORE INTO sys_daily_serial (...) VALUES (...)`，使用**独立于调用方事务的连接**，语句执行完立即提交。仅当当天该 `business_type` 第一次被使用时才会真正插入新行；此后同一天的所有请求都会命中"已存在，IGNORE 生效"分支。
2. **原子自增并读回**：`UPDATE sys_daily_serial SET current_value = LAST_INSERT_ID(current_value + 1) WHERE business_type=... AND business_date=...`，在调用方自己的事务里执行，随后 `SELECT LAST_INSERT_ID()` 读回新值拼出最终编号。这是 MySQL 官方文档给出的序列表标准写法（[MySQL 8.0 Reference: Example of Sequence Generation](https://dev.mysql.com/doc/refman/8.0/en/example-auto-increment.html)）。

该 UPDATE 对这一行加的排他锁会保持到调用方事务提交/回滚为止——也就是说"生成编号"与"用这个编号写业务行并提交"这两件事被同一把锁串在了一起，杜绝了"编号已生成但业务行还没提交，另一个事务趁机拿到同一个编号"的窗口。

编号格式 `{prefix}{yyyyMMdd}{4位流水}`（如 `SQ202605290001`）完全不变，`prefix`（`SQ`/`HY`/`YJ`）与新增的 `business_type`（`APPEAL`/`MEETING_BOOKING`/`GOV_MEETING`）分开维护，前者决定编号文本，后者只是计数表的分类键。

### 3. 是否新增了表

新增 1 张表：`sys_daily_serial`（`id` BIGINT 主键自增，`business_type` VARCHAR(30)，`business_date` DATE，`current_value` INT，唯一约束 `uq_sys_daily_serial_type_date`）。纯计数用途，不参与任何业务归属/数据权限查询，不做软删除。

### 4. 迁移详情

- 实际执行 `alembic current` 确认当前 head 为 `010_enterprise_identity`（未假设版本号）。
- 新增 `migrations/versions/011_sys_daily_serial.py`，`down_revision = '010_enterprise_identity'`。
- 只有 `create_table`/`drop_table`，未修改任何历史迁移文件，未手工建表、未删数据。
- 已实际执行验证：`upgrade head` 成功 → `downgrade -1` 成功 → 再次 `upgrade head` 成功，`alembic current` 最终显示 `011_sys_daily_serial (head)`。

### 5. 多 worker / 多容器安全性论证

整套方案的互斥完全落在 MySQL InnoDB 的行级锁和 `INSERT IGNORE` 的唯一约束上，不依赖任何进程内状态（无 `threading.Lock`/`asyncio.Lock`/全局变量），因此：

- 同一台机器上的多个 Uvicorn worker 进程、以及不同容器/不同机器上的多个应用实例，看到的都是同一个 MySQL 实例、同一张 `sys_daily_serial` 表，锁的粒度在数据库层面，与"进程在哪里跑"无关。
- 不同 `(business_type, business_date)` 之间用不同行互不阻塞：不同业务模块之间、跨天的请求完全并行，不会因为这一张计数表退化成全局串行瓶颈。

### 6. 历史编号兼容方式

`_ensure_counter_row` 首次为某个 `(business_type, 日期)` 插入行时，起始值取 `_max_existing_suffix`——即扫描对应业务表中当天已有编号（`LIKE 'PREFIX+yyyyMMdd%'`）的最大末四位。这只在本次改造上线当天、且该业务类型当天已有旧逻辑生成的编号时才会生效，用于避免新计数器从 0 开始与已存在的历史编号撞车；此后每天的计数行都是全新的（起始必然是 0），不再需要、也不会触发这条兼容路径。全程不修改、不迁移任何历史业务编号数据。

### 7. 流水号并发测试方法与结果

`tests/test_concurrency.py` 中 3 个测试（Appeal / MeetingRoomBooking / GovMeetingApply 各一个），方法：

- 用 `ThreadPoolExecutor` 起 20 个**真实线程**，每个线程各自开一条独立的 `Session`（独立连接、独立事务），调用 `generate_daily_serial` 生成编号后**立即用该编号插入一条真实业务行并提交**——如果编号重复，第二个线程的 INSERT 会因 `unique=True` 约束触发 `IntegrityError`。
- 断言：生成的 20 个编号去重后仍为 20 个；数据库中实际能查到的对应编号行数也是 20（不是仅在应用层去重，而是数据库唯一约束也认可这 20 条记录合法存在）。
- 测试结束后在 `finally` 块里用生成的行 id 显式清理，不依赖事务回滚（因为真实并发测试必须使用会真正提交的独立事务，无法用单一共享事务模拟）。

结果：3 个测试全部通过，稳定复现（本地连续运行 3 轮均 100% 通过，未出现编号重复或残留死锁）。

实现过程中发现并解决了一个真实的 InnoDB 现象：多个事务并发对同一个**尚不存在**的唯一键做 `INSERT`，即使用 `INSERT IGNORE`，也可能触发 InnoDB 死锁检测（errno 1213）。这不是设计缺陷，而是"当天首次插入"这一步的天然瞬时冲突；由于死锁发生后 InnoDB 会整体回滚受害事务（不是回滚到某个 SAVEPOINT），无法在不影响调用方已有写入的前提下做局部重试，因此把"确保计数行存在"这一步放进一条独立、立即提交的连接中执行——冲突窗口从"整个业务事务"缩小到"一条 INSERT 语句"，并对这一步做了最多 3 次的窄范围重试（只重试这一条独立语句，不涉及调用方事务，也不是通用重试框架）。

---

## 二、会议室预约审批并发问题

### 8. 原问题

`MeetingRoomService.approve_booking` 原实现：查预约 → 查权限 → 查状态 → **查冲突（普通 SELECT，无锁）** → 更新状态为 `APPROVED` → 提交。这是经典的 TOCTOU：两个管理员并发审批同一会议室两个时间重叠的预约时，双方的"查冲突"都可能发生在对方"提交"之前，都查不到冲突，最终两条预约都被置为 `APPROVED`。且这种冲突在"两条预约互相冲突但都还没有被通过"时，锁任何一条已存在的冲突记录都无法预防（因为此时根本不存在"冲突记录"这一行可锁）。

### 9. 最终加锁策略

在 `approve_booking` 里，先对**父级 `MeetingRoom` 行**做 `SELECT ... FOR UPDATE`（`MeetingRoomRepository.lock_room_for_update`），把"同一会议室"的并发审批请求在数据库层面串行化；不同会议室之间锁的是不同的行，互不影响，可以并行审批。拿到房间锁之后，再用 `SELECT ... FOR UPDATE`（主键等值查询）重新读取这条预约本身的最新状态（`get_booking_by_id_for_update`），然后做状态校验、冲突校验，最后更新状态、写审批记录、提交。

同时，把这一次审批**这一个事务**的隔离级别通过 SQLAlchemy 的 `execution_options={"isolation_level": "READ COMMITTED"}` 临时调整为 READ COMMITTED（仅对这一个事务生效，连接归还连接池时自动恢复默认隔离级别，不是修改全局隔离级别）。原因：

- MySQL 默认 REPEATABLE READ 下，一个事务的一致性快照在该事务第一条语句执行时就已固定；即使后面靠 `FOR UPDATE` 等到了房间锁，冲突检查这类"按时间段范围查询"的普通 SELECT 仍可能读到的是锁等待期间早已过期的旧快照，看不到对方刚提交的冲突预约——这本身就是一个正确性漏洞。
- 若为了让冲突检查读到最新数据而给这条按时间范围过滤、走非唯一索引的查询也加 `FOR UPDATE`，会在 REPEATABLE READ 下触发 InnoDB 的 next-key（间隙）锁：在测试数据量较小、索引选择性不高的场景下，这会导致**互不相关的两个会议室**的审批请求相互阻塞，实测甚至复现了跨会议室的死锁（errno 1213）——这与"不同会议室不应互相影响"的要求直接冲突。

改用 READ COMMITTED 后，同一事务内的每条普通 SELECT 都会读到当时最新已提交的数据，冲突检查不再需要额外加锁即可保证正确性，也从根源上避免了间隙锁导致的跨会议室伪冲突/死锁。全程只对两处基于主键的等值查询使用 `FOR UPDATE`（会议室行、预约行本身），主键等值锁不会产生间隙锁。

### 10. 事务边界

加锁（锁会议室行）→ 重新读取预约最新状态 → 状态校验 → 冲突复核 → 更新状态 → 写审批记录/操作日志 → `commit()`，全部在 `approve_booking` 同一个数据库事务内完成，中途没有任何提前提交。若冲突复核抛出异常，整个事务在请求结束时通过 `get_db()` 的 `finally: db.close()`（`Session.close()` 内部会先 `rollback()`）整体回滚，不会留下部分更新。

### 11. 为什么两个时间重叠的冲突预约不可能都变成 APPROVED

两个管理员并发审批同一会议室下两条时间重叠的预约时：

1. 两个事务都会先尝试锁 `MeetingRoom` 行，MySQL 保证只有一个能立刻拿到锁，另一个必须等待。
2. 先拿到锁的事务完成"复核冲突（此时另一条预约还未被通过，查不到冲突）→ 置为 APPROVED → 提交"，随后释放房间锁。
3. 后拿到锁的事务在等待期间被阻塞；一旦前一个事务提交、锁被释放，它才能继续往下走，此时它的冲突复核（READ COMMITTED，读最新已提交数据）**一定能看到**对方刚提交的、时间重叠且状态为 `APPROVED` 的预约，从而在 `_check_booking_conflict` 处抛出 `MeetingRoomConflictException`，整个事务回滚，这条预约的状态维持不变（不会被置为 APPROVED）。

因此结构上不存在"两个都通过锁检查再各自提交"的路径，恰好一个成功、另一个收到清晰的业务冲突异常（而不是原始数据库异常）。

### 12. 不同会议室并发是否受影响

不受影响。房间锁的粒度是单条 `MeetingRoom` 主键行，两个不同会议室的审批请求锁的是两条完全不同的行，MySQL 不会因此互相阻塞；配合 READ COMMITTED 消除了间隙锁，两个不同会议室的并发审批可以真正同时进行、都成功提交（见下方测试结果）。

### 13. 会议室并发测试方法与结果

`tests/test_concurrency.py` 两个测试：

- **同房间时间重叠预约的并发审批**（`test_overlapping_bookings_same_room_only_one_approved`）：真实创建 1 间会议室 + 2 条时间重叠的 `PENDING_AUDIT` 预约，用两个真实线程（各自独立 `Session`）、`threading.Barrier` 对齐起跑时间，并发调用 `approve_booking`。断言：恰好 1 个返回成功且状态为 `APPROVED`，另 1 个抛出 `MeetingRoomConflictException`（而非原始数据库异常）；数据库里最终这两条预约中 `APPROVED` 的数量严格等于 1。重复 5 轮，全部满足。
- **不同房间并发审批都应成功**（`test_different_rooms_concurrent_approval_both_succeed`）：创建 2 间不同会议室各 1 条预约，同样用 `Barrier` 对齐并发审批。断言：两个都返回成功、状态均为 `APPROVED`，证明加锁粒度确实是"按会议室"而不是全局/整表锁。

结果：两个测试均通过，本地连续运行 3 轮 100% 通过。所有测试数据在 `finally` 块中显式清理（预约、审批记录、会议室、相关操作日志），不依赖事务回滚。

---

## 三、验证结果汇总

### 14. 原 35 个回归测试结果

`pytest tests/ --ignore=tests/test_concurrency.py`：**35 passed**，与整改前完全一致，无回归。

### 15. 数据库迁移状态

`alembic current` → `011_sys_daily_serial (head)`。执行过一次完整的 `upgrade head → downgrade -1 → upgrade head` 验证，两个方向均无报错。相关业务表（`sys_daily_serial`、`meeting_room`、`meeting_room_booking`、`appeal_main`、`gov_meeting_apply`）已确认 `ENGINE=InnoDB`。

### 16. 前端构建结果

未修改任何前端代码（本轮问题完全是后端并发正确性问题，且冲突时的错误信息通过已有的统一响应体 `{code, message}` 传递，前端既有的错误提示机制无需改动即可展示新的 `MeetingRoomConflictException` 文案）。仍按要求执行了构建以确认现状未被破坏：

- `admin-web`：`npm run build` 成功（`vite build`，产物正常输出到 `dist/`，仅有一条与本次改动无关的 chunk 体积告警）。
- `enterprise-h5`：`npm run build` 成功。

### 17. 新增并发测试与组合测试结果

- 新增 5 个并发测试（3 个流水号 + 2 个会议室），单独运行、连续 3 轮均 **5 passed**。
- 与原 35 个测试合并运行（`pytest tests/`）：**40 passed**，连续多轮运行结果一致，无 flaky。

### 18. 当前已知剩余问题

- 无新增 P0/P1 级问题。
- `approve_booking` 对这一个事务临时切到 READ COMMITTED，属于本次为解决间隙锁/跨房间死锁问题而引入的、有明确必要性的局部改动，作用范围严格限定在这一个方法的这一次事务内，不影响其他接口。
- `sys_daily_serial` 计数表不参与任何清理/归档策略（历史 AUTO_INCREMENT 式计数器本就没有必要清理），后续若需要按日期归档旧计数行，可另行评估，非本轮阻塞项。
- 测试基础设施：`tests/conftest.py` 中 `test_db_engine` 的连接池从默认 `pool_size=5,max_overflow=10` 调大到 `pool_size=20,max_overflow=40`，仅用于支撑本轮新增的真实并发测试（20 线程 × 每线程最多 2 条连接），不影响生产环境连接池配置（生产配置在 `app/core/database.py`，未改动）。

### 19. 范围确认

`git diff` 复核：本轮实际改动文件仅限于 `app/models/system.py`、`app/models/__init__.py`、`app/utils/serial_no.py`、`app/repositories/{appeal_repo,gov_meeting_repo,meeting_room_repo}.py`、`app/services/meeting_room_service.py`、新增迁移 `migrations/versions/011_sys_daily_serial.py`、新增测试 `tests/test_concurrency.py`、以及 `tests/conftest.py` 的连接池参数调整。未触碰 `app/core/permission.py`、`app/constants/permission.py`、`docs/ADMIN_PERMISSION_MATRIX.md`（PLATFORM_ADMIN / CITY_ADMIN 权限矩阵原样保持人工确认后的现状）；仓库内不存在 Dockerfile / docker-compose / Nginx / Kylin V10 相关文件；未涉及任何 B2 功能。

### 20. 结论

**READY FOR DOCKERIZATION: YES**

两个并发问题均已在数据库事务/锁层面解决，不依赖任何进程内锁或"生产负载低所以不会发生"的假设；原有 35 个回归测试与新增 5 个并发测试合计 40 个全部通过；数据库迁移可正常升级/回滚；两个前端构建均正常；未修改人工确认的权限矩阵；未涉及 Docker 化或 B2 范围之外的任何内容。
