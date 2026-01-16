# Change: Electron 桌面版 + 离线授权码（机器绑定）+ 内置数据库

## Why
需要将当前的 Web IDE 形态产品交付为 **macOS/Windows 桌面应用**，并提供 **离线授权码机制**（仅授权指定机器可用），同时桌面版应 **自带数据库**，用户无需额外安装 Postgres/Docker。

## What Changes
- 新增 `apps/desktop`：Electron 桌面壳（macOS/Windows），负责启动本地后端并加载 UI。
- 后端新增“桌面模式”启动方式：作为本地 sidecar 进程运行，并提供静态 UI（同源，避免 CORS）。
- 数据库策略调整以支持桌面“自带 DB”：
  - 桌面默认使用本机数据目录下的 **SQLite** 文件库（无需外部服务）。
  - 本地开发仍可继续使用 Postgres（docker compose），但代码需支持至少 SQLite 作为运行时选项。
- 新增离线授权能力：
  - 生成“机器码”（硬件指纹 hash）供用户发给你。
  - 你在本地用私钥生成“授权码/授权文件”（包含机器码、可选过期时间等并签名）。
  - 客户端离线校验签名与机器匹配后启用全部功能。
  - 未授权时，后端 API 默认拒绝（403），UI 提示引导授权。
- 新增“授权/激活”UI 面板与管理入口（查看机器码、粘贴授权码、查看状态、清除授权）。
- 提供你可离线运行的授权码生成工具（CLI），私钥不进入仓库/不打包进客户端。

## Non-Goals / Constraints
- 不追求“不可破解”的 DRM（离线桌面应用无法彻底防篡改，只提升门槛）。
- 离线授权不提供远程吊销；如需吊销，只能靠“有效期 + 重新发码/升级策略”等。
- 初期不做多用户登录；仍为单用户本地应用。

## Impact
- Affected specs (delta): `desktop-app`, `offline-licensing`（新增）
- Affected code:
  - `apps/api`: 启动方式/DB 兼容/授权校验中间件/授权 API
  - `apps/web`: 授权 UI、错误提示（403）、桌面运行时 API base 注入（若需要）
  - `infra`: 桌面版不依赖 compose；本地 dev 仍保留
