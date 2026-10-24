# 全面战争战锤3 联机存档转为单人存档导出工具

## [⬇ 此处下载](https://github.com/UED000/WH3_MPTOSP/releases/latest)

**英文名 / exe：** `WH3_MPTOSP`（Warhammer III Multiplayer to Singleplayer）  
**版本：** 0.1.0  
**作者：** 000  
**图标：** 顶部 `WH3`、下方双卡片 MP→SP 图标（exe 与窗口共用）

双击 `WH3_MPTOSP.exe` 使用。原存档不会被修改，只会生成一个新的 `.save`。

## 界面与用法

1. 下载 `WH3_MPTOSP.exe`，放到任意文件夹后双击运行，无需安装。
2. 将联机存档 `.save_multiplayer` 拖进窗口；也可以点击窗口上方的提示区域选择文件。
3. 在玩家列表中选择你要继续游玩的玩家。
4. 点击“导出选中玩家为单人存档”。
5. 在保存对话框中选择输出位置，等待导出完成。建议直接保存到游戏单人存档目录。
6. 启动游戏，进入“加载战役”，选择刚导出的 `.save`。

建议导出前备份原联机存档；工具不会修改原文件。

## 更多人存档可用？

可用。2 人、3 人及更多玩家的联机存档都可以尝试；选择任意一名玩家导出后，该玩家成为单人战役主角，其他玩家派系由 AI 接管。2 人和合成 3 人存档已测试；真实 3 人以上存档建议先在副本上验证。

## 界面上能看什么

- 文件名、当前回合、存档时间、战役和玩家数；
- 玩家列表：玩家名、派系显示名、派系 key、战役难度、战斗难度；
- 选中玩家后：派系 ID、国库、预计收入、完整行省、城镇、军队（野战军）、人物（领主/事务官）、战斗倍率；
- “查看 MOD 列表”可以查看该存档使用的 MOD。

### 数据说明

- 预计收入 = 收入 + 贸易 - 支出 + 存档基础收入项。
- 完整行省 = 该派系拥有全部地区的行省数量。
- 城镇 = 当前归属该派系的地区数量。
- 军队（野战军）= 领主统率的野战军，不含驻军。
- 人物（领主/事务官）= 领主数 / 事务官数，不含驻军指挥官。

## MOD

如果原存档带 MOD，导出后加载时请启用同一组 MOD；工具会保留存档记录的 MOD 列表。

## 从源码构建

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
mp2sp_gui.py              # 程序入口
convert_mp_sp.py          # MP→SP 转换核心
esf.py / tables.py        # 存档读写与派系表
faction_portraits.py      # 派系领袖头像路径
i18n.py / locdb.py        # 空桩
README.md
```

## 许可证

Apache License 2.0，见 `LICENSE`。

## 免责声明

非官方粉丝工具，未获 SEGA、Creative Assembly 或 Games Workshop 背书。Total War: WARHAMMER 及相关名称、资源归其各自权利人所有。本工具不包含游戏本体资源。
