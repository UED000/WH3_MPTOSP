# 全面战争战锤3 联机存档转为单人存档导出工具

**英文名 / exe：** `WH3_MPTOSP`（Warhammer III Multiplayer to Singleplayer）  
**版本：** 0.1.0  
**作者：** 000  
**图标：** 顶部 `WH3`、下方双卡片 MP→SP 图标（exe 与窗口共用）

左上角 **`!`** 按钮可查看版本、作者、功能与说明。


双击 `WH3_MPTOSP.exe` 使用。**原存档不会被修改**，只会生成一个新的 `.save`。

## 界面与用法

1. 双击 exe。工具会自动尝试定位游戏联机存档目录：
   ```
   %APPDATA%\The Creative Assembly\Warhammer3\save_games_multiplayer
   ```
   它会检查 `%APPDATA%`、当前用户目录、以及其他盘的 `Users\*\AppData\Roaming`；找到多个时优先选“最近有联机存档”的那个。找不到时可以点 **“更改目录”** 手动指定。
2. 把 `.save_multiplayer` 拖进窗口（或点窗口里的选择区域，文件框会直接打开在上面的目录，并预选最新的联机存档）。
   也可以直接把存档拖到 exe 图标上。
3. 窗口列出所有玩家：
   - 玩家名、派系显示名、派系 key、战役难度、战斗难度；
   - 选中玩家后，下方“选中派系详情”显示：派系 ID、国库、预计收入、完整行省、城镇、军队（野战军）、人物（领主/事务官）、战斗倍率；
   - “查看 MOD 列表”会排除基础战役包 `wh3_main_combi.pack`，只显示实际 MOD；纯原版会提示“没有 MOD”。
4. 右上角的 **EN / 中文** 按钮切换界面语言（会记住选择）。
5. 选中一个玩家，点 **“导出选中玩家为单人存档”**。保存对话框会**直接打开游戏单人存档目录** `...\Warhammer3\save_games`。
6. 几秒后完成；右下角会显示**逐步增长的进度条**和**预计剩余时间倒计时**（估算），完成后显示“完成”；工具同时显示保留/降为 AI 的派系和校验结果。

**目录行为**：

- 点击拖入框/提示区 → 打开游戏**联机**存档目录 `save_games_multiplayer`；
- 点“导出选中玩家” → 保存对话框打开游戏**单人**存档目录 `save_games`；
- 上方新增两个按钮：**“打开多人存档目录”** 和 **“打开游戏单人存档目录”**；**两个都在右侧，多人紧挨在单人左侧**（不是最左侧），分别直接打开两个目录；
- 如果检测/配置/手动选择得到的是 `Warhammer3` 父目录，工具会自动归一化到 `save_games_multiplayer` / `save_games`；
- 两个目录都会显示在主界面上；找不到时可点“更改目录”手动指定，单人目录会自动取同级的 `save_games`。

输出文件放到：

```
%APPDATA%\The Creative Assembly\Warhammer3\save_games\
```

然后进游戏“加载战役”。建议先在副本存档上测试，确认能进、过回合不卡。

## 支持几名玩家？

- 按存档头里的玩家数量循环读取，**不限于 2 人**；列表显示全部玩家，任选一个导出。
- 已实测 2 人存档，以及合成 3 人存档：3 人都能列出；保留其中 1 人后，另外 2 人都进入 AI 组，人类组只剩保留者，三处人类标记各 1 个 `FULL_HUMAN`。
- 3 人以上会额外处理：把所有被降级玩家从**任何**人类回合组里移除，再统一并入纯 AI 组，避免“另一个玩家还留在人类组导致过回合卡住”。
- 注意：合成 3 人测试不是真实 3 人游戏进程；如果你有真实的 3+ 人存档，建议先测试一次。

## 导出时具体改了什么

**外层 ESF**
- 根记录 `MULTIPLAYER_CAMPAIGN_SAVE_GAME` → `CAMPAIGN_SAVE_GAME`
- `SAVE_GAME_HEADER_MULTIPLAYER` → `SAVE_GAME_HEADER`（v3）
- 删除 `multiplayer` 记录和 MP 头专用的地区/部队位置记录
- 头部地区归属 key / 调色板数组改为保留玩家在 MP 头里的那一组

**战役数据**
- 人类标记三处统一：`CAMPAIGN_SETUP/CAMPAIGN_PLAYERS_SETUP`、`FACTION/CAMPAIGN_PLAYER_SETUP`、`FACTION` 直接子节点；只有保留者是 `FULL_HUMAN`
- `HUMAN_FACTIONS` 只保留保留者
- `TURN_CONTROL`：人类组只保留保留者；被降级玩家从所有组移除并并入纯 AI 组
- `CAMPAIGN_SETUP_OPTIONS`：`MP_NORMAL → SP_NORMAL`，MP-only 开关关闭
- `CAMPAIGN_MODEL` 联机布尔 → False
- 难度：把保留者的 `[战役难度, 战斗难度, 战斗倍率]` 写成 SP 形式，并同步到 560 个派系的难度记录、`CAMPAIGN_SETUP` 汇总和 `CAMPAIGN_ENV` 的难度字符串
- `GAME_PERSISTENT_SESSION_ID` 只保留保留者的身份
- 被降级玩家的部队如果当前行动力为 0，导出时补满到该单位的上限；源 MP 存档里非当前玩家的部队常以 0 行动力保存，不补的话转成 AI 后可能原地不动

## 文件信息里显示什么

顶部摘要显示：文件名、当前回合（1 基，如 `44`）、存档时间、战役 key、玩家数。

**不再显示季节**：原版存档头里的“春/夏/秋/冬”是战役季节，只用于游戏内日历显示，对转换没有作用，所以从文件信息里移除了（内部仍会解析，不展示）。

选中玩家后显示的关键派系信息：

- 派系 ID
- 国库
- 预计收入
- 完整行省
- 城镇
- 军队（野战军）
- 人物（领主/事务官）
- 战斗倍率
- “查看 MOD 列表”按钮

### 数据口径

- **国库**：`FACTION_ECONOMICS` 的第一个标量。
- **预计收入**：最后一条经济历史里的 `收入 + 贸易 - 支出`，再加上存档固定项 `faction_gdp_other`（实测为 `3000`）。这是按游戏内“预计收入”的口径计算的；一次性招募/建造仍可能让国库变化略有不同。
  - 如果源存档存在已知的贸易值异常，预计收入也会被相应放大；工具只负责忠实读取，不会自动修正。
- **完整行省**：该派系拥有该行省**全部地区**的行省数量；用 `PROVINCES_DATA` 的地区→行省映射逐行省比较。
- **城镇**：`REGION` 记录第 5 个标量（当前归属派系 ID）等于该派系 ID 的数量。**不能用记录里的 owner 字符串**：部分 MP 存档的 owner 字符串是旧数据，会少算，必须以归属派系 ID 为准。
- **军队（野战军）**：`ARMY_ARRAY` 里的 `MILITARY_FORCE`，只算 `MILITARY_FORCE_LEGACY[1] == 0` 的领主统率野战军；驻军（值为 2）不计。
- **人物（领主/事务官）**：显示为 `领主数 / 事务官数`。领主 = 野战军指挥官 + 未带队的 general；事务官 = 没有指挥任何军队的其余角色（spy、wizard 等）。驻军指挥官（例如驻军里的 colonel）不计入。
- **回合**：显示当前回合（1 基）。导出时 SP 头两个回合字段都写当前回合（原生 SP 同值），不会再出现 `0/1`。

## 已知的非玩法差异

导出的不是“与原生单人存档逐字节完全一致”的文件，但战役状态是完整的（记录级 diff 只差联机头）。以下字段可能和原生单人存档不同，均不影响战役：

- 读档界面的 faction leader 肖像路径为空；
- `GAME_PERSISTENT_SESSION_ID` 的 utf16 仍是 MP 会话号（u64 身份已换）；
- 成就试炼数组为空；
- 相机位置仍是 MP 本地玩家的镜头（读档后游戏可能自动回正）；
- 回合字段：SP 头两个字段都写当前回合（如 `44/44`），与原生 SP 一致；
- 地区归属 key/调色板是源存档回合的 MP 快照，游戏可自行重建/扩展。

## MOD 列表

存档里的 `mod_history_block_name` 就是“这个存档需要的包/MOD 列表”，存在三个位置：外层 `SAVE_GAME_HEADER`、内层 `SAVE_GAME_HEADER`、内层 `CAMPAIGN_ENV`。

每条格式是 `[pack 文件名, 创意工坊 id 或 'campaigns', 标志, 序号]`。SP 档案里标志常见 `1=MOD/0=基础`，但 MP 存档可能全部为 0；工具显示 MOD 列表时以 pack 名排除基础包，不依赖这个值。

- 纯原版存档通常只包含 `wh3_main_combi.pack` + `campaigns`；
- 转换会把 MP 存档里的这份列表**原样复制**到导出的单人存档，三个位置保持一致；不会移除、也不会凭空添加 MOD；
- 如果源 MP 存档本身带 MOD，列表里会出现那些 `.pack` 名称/工坊 id；导出后加载时，**这些 MOD 需要保持启用**；

## 已知的存档 bug（工具不修）

部分联机存档可能存在原版贸易路线值异常。转换工具会**忠实保留**源存档里的数值，不会自动修复；如果需要修复版，应另外做定点修改。

## 命令行（自动化/排错）

```bat
WH3_MPTOSP.exe --self-test "存档路径.save_multiplayer"
WH3_MPTOSP.exe --export "存档路径.save_multiplayer" 1 "输出路径.save"
WH3_MPTOSP.exe --smoke-test "存档路径.save_multiplayer"
```

`--self-test` 列出玩家、难度、国库/预计收入/完整行省/城镇/军队/人物和 MOD 列表；`--export` 直接按玩家序号导出（0 = 第一个玩家）；`--smoke-test` 隐藏窗口跑一遍 GUI（构建验证用）。

## 从源码构建（可选）

需要 Python 3.9 + tkinter + PyInstaller：

```bat
python -m pip install pyinstaller tkinterdnd2
python -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "WH3_MPTOSP" --icon app.ico --collect-all tkinterdnd2 mp2sp_gui.py
```

## 文件

```
WH3_MPTOSP.exe    # 成品（双击使用；发布版提供）
app.ico                   # 软件图标（构建时使用）
mp2sp_gui.py              # GUI + 命令行入口
convert_mp_sp.py          # MP→SP 转换核心（含 3+ 玩家加固）
esf.py / tables.py        # ESF 读写与派系表
i18n.py / locdb.py        # 空桩
README.md
```

## 许可证

Apache License 2.0，见 `LICENSE`。

## 免责声明

非官方粉丝工具，未获 SEGA、Creative Assembly 或 Games Workshop 背书。Total War: WARHAMMER 及相关名称、资源归其各自权利人所有。本工具不包含游戏本体资源。
