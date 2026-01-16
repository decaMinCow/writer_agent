## Context
当前项目为“创作 IDE”：
- 前端：SvelteKit + Tailwind（Web UI）
- 后端：FastAPI + SQLAlchemy + Alembic
- DB：Postgres + pgvector（本地 dev 通过 docker compose）

本变更需要将其交付为 **macOS/Windows 桌面应用**，并满足：
- 桌面用户无需安装 Postgres/Docker（“自带数据库”）
- 离线授权码（机器绑定）限制使用人群

## Goals
- Electron 桌面壳可一键启动：启动本地 API + 打开 UI
- 桌面版默认使用内置 DB（SQLite 文件库），数据持久化在用户数据目录
- 离线授权：机器码 → 授权码 → 本地验证 → 放行
- 授权状态由后端强制执行（避免只靠 UI）

## Non-Goals
- 完全不可破解的 DRM
- 在线激活/在线吊销（可作为后续扩展）
- 一次性解决所有性能优化（先保证可用与交付）

## Architecture

### Desktop runtime topology
Electron Main Process
1) 选择可用端口（默认从 9761 起尝试或随机端口）
2) 启动 API sidecar（PyInstaller 打包后的可执行文件）
   - 通过 env 传入数据目录/DB URL/端口/运行模式
3) 等待 API `/healthz` 可用
4) 打开 BrowserWindow 指向 `http://127.0.0.1:<port>/`（由 API 提供静态 UI）

API sidecar（FastAPI）
- 绑定 `127.0.0.1`（不对外暴露）
- `/api/*`：现有 API
- `/`：静态 UI（SvelteKit 构建产物）

### Embedded database choice
桌面默认：SQLite（`sqlite+aiosqlite`）文件库，位于 Electron `app.getPath('userData')` 目录。

为兼容现有 Postgres 开发模式：
- 运行时由 `DATABASE_URL` 控制（dev 可继续 Postgres，desktop 走 SQLite）
- ORM/查询需要尽量避免 Postgres-only 类型：
  - UUID：使用 SQLAlchemy 通用 `Uuid` 类型
  - embedding：Postgres 可用 pgvector；SQLite 采用 JSON/Blob 存储并在 Python 中做余弦相似度排序（单用户规模可接受）

### Schema / migrations
桌面版不要求用户手动执行 Alembic。
建议：
- API 启动时检测是否需要初始化/升级 DB（自动跑到 `head`）。
- 失败时返回可操作错误（提示用户重启/导出数据/重建）。

### Offline licensing design
#### Machine code
后端提供 `GET /api/license/machine-code` 返回机器码（硬件指纹的 hash，避免暴露原始硬件信息）。
- macOS：IOPlatformUUID（优先）→ hash
- Windows：MachineGuid（优先）→ hash

#### License payload + signature
授权码包含：
- `license_id`（随机 UUID）
- `machine_code`（绑定目标机器）
- `issued_at`
- `expires_at`（可选）
- `features`（可选）
使用 Ed25519（或同等级）签名：
- 客户端内置 **公钥**
- 你本地保留 **私钥**，用 CLI 生成授权码

#### Enforcement
- 允许访问：`/healthz`, `/api/license/*`（用于激活）
- 其他 `/api/*`：未授权返回 403（含中文提示）

### UI
新增“授权”面板：
- 展示机器码
- 输入授权码并激活
- 展示授权状态（已授权/到期时间/绑定信息）
- 清除授权（用于重装/切换授权）

## Open Questions
1) 授权默认是否带有效期（例如 1 年）还是永久？（设计中支持可选过期）
2) 授权是否允许“迁移”（例如清除后重新激活新机器）？需要你人工发码即可。
3) 桌面版是否必须保留 pgvector 级别的检索性能？（初期按单用户规模用 Python 余弦排序）
