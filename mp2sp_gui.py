# -*- coding: utf-8 -*-
"""联机存档 -> 单人存档 导出工具（GUI）

用法：
  1. 双击 exe，把 .save_multiplayer 拖进窗口（或点“选择存档”）。
  2. 窗口会列出该存档里的玩家派系与关键信息。
  3. 选中一个玩家，点“导出选中玩家为单人存档”，选择输出位置。
  4. 原存档不会被修改。

命令行：
  WH3_MPTOSP.exe --self-test <save>
  WH3_MPTOSP.exe --export <save> <player_index> <out>
  WH3_MPTOSP.exe --smoke-test <save>     # 隐藏窗口跑一遍 GUI，用于构建验证
"""
import os
import sys
import json
import glob
import time
import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import ttk, filedialog, messagebox

import esf
import convert_mp_sp as conv

DIFF_CODES = {0: "easy", 1: "normal", 2: "hard", 3: "very_hard", 4: "legendary"}
APP_VERSION = "1.0.0-beta.1"
APP_AUTHOR = "000"
ICON_PNG_B64 = "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"

STR = {
    "zh": {
        "window_title": "全面战争战锤3 联机存档转为单人存档导出工具",
        "info_title": "软件信息",
        "info_text": "全面战争战锤3 联机存档转为单人存档导出工具\n\n版本：{version}\n作者：{author}\n\n功能：读取联机存档，列出玩家派系，导出指定玩家为单人存档。原存档不会被修改。\n\n支持：Total War: Warhammer III（原版/带 MOD 存档）。导出后加载时需启用原存档使用的 MOD。",
        "header_hint": "拖入 .save_multiplayer（或点击下面的区域选择文件）。原存档不会被修改。",
        "drop_dnd": "把联机存档拖到这里\n或点击打开游戏联机存档目录\n\n支持多人战役存档 .save_multiplayer\n\n注意：建议使用系统自动保存，或者您手动保存的存档；\n尽量不要使用快速保存的存档（快速保存的存档可能存在部分信息缺失问题）。",
        "drop_click": "点击打开游戏联机存档目录\n\n支持多人战役存档 .save_multiplayer\n\n注意：建议使用系统自动保存，或者您手动保存的存档；\n尽量不要使用快速保存的存档（快速保存的存档可能存在部分信息缺失问题）。",
        "dir_prefix": "游戏联机存档目录：",
        "dir_missing": "未自动找到（可手动选择）",
        "dir_common": "常见位置：C:\\Users\\<用户名>\\AppData\\Roaming\\The Creative Assembly\\Warhammer3\\save_games_multiplayer",
        "sp_dir_prefix": "游戏单人存档目录：",
        "sp_dir_missing": "未自动找到",
        "sp_dir_create_hint": "（导出时会自动创建）",
        "sp_dir_common": "常见位置：C:/Users/<用户名>/AppData/Roaming/The Creative Assembly/Warhammer3/save_games",
        "btn_choose_dir": "更改目录",
        "btn_redetect": "重新检测",
        "summary_none": "尚未载入存档",
        "summary_line": "文件：{file}    回合：{turn}    存档时间：{time}    战役：{campaign}    玩家：{players}",
        "mods_none": "没有 MOD（纯原版存档）",
        "mods_count": "MOD {n} 个 / 包 {total} 个",
        "col_idx": "#",
        "col_player": "玩家",
        "col_fname": "派系显示名",
        "col_key": "派系 key",
        "col_camp": "战役难度",
        "col_battle": "战斗难度",
        "detail_title": "选中派系详情",
        "detail_id": "派系 ID",
        "detail_treasury": "国库",
        "detail_income": "收入（不含贸易）",
        "detail_trade": "贸易项",
        "detail_expense": "支出项",
        "detail_expected": "预计收入",
        "detail_provinces": "完整行省",
        "detail_settlements": "城镇",
        "detail_armies": "军队（野战军）",
        "detail_chars": "人物（领主/事务官）",
        "detail_mult": "战斗倍率",
        "detail_packs": "MOD/包",
        "btn_export": "导出选中玩家为单人存档",
        "btn_open": "打开游戏单人存档目录",
        "btn_open_mp": "打开多人存档目录",
        "btn_open_sp": "打开游戏单人存档目录",
        "btn_mods": "查看 MOD 列表",
        "btn_lang": "EN",
        "status_ready": "尚未载入存档。",
        "status_loaded": "已载入。选中一个玩家后点“导出选中玩家为单人存档”。",
        "ai_note": "已修复被降级玩家派系的军事 AI：游戏会为其生成军事任务，AI 可以招募和移动军队。适用于多人存档。",
        "status_converting": "正在转换，请稍候……（15MB 存档通常几秒）",
        "status_done": "导出成功：{out}",
        "eta_prefix": "预计剩余：",
        "eta_seconds": "{s} 秒",
        "eta_finishing": "即将完成…",
        "eta_done": "完成",
        "eta_failed": "失败",
        "status_failed": "导出失败：\n{err}",
        "dlg_select_player_title": "请选择玩家",
        "dlg_select_player_msg": "请先在列表里选中一个玩家。",
        "dlg_save_title": "导出单人存档",
        "dlg_export_ok_title": "导出成功",
        "dlg_export_ok_msg": "已生成单人存档：\n{out}\n\n保留玩家：{keep}\n降为 AI：{drop}\n\n请把 .save 放到游戏的 save_games 目录测试。",
        "dlg_export_fail_title": "导出失败",
        "dlg_read_fail_title": "无法读取",
        "dlg_read_fail_msg": "无法读取这个存档：\n{err}",
        "dlg_mods_title": "MOD/包列表",
        "dlg_mods_msg": "这个存档记录的包/MOD（{n} 条）：\n\n{lines}",
        "dlg_dir_title": "选择游戏联机存档目录",
        "dlg_dir_missing_title": "目录不存在",
        "dlg_dir_missing_msg": "目录不存在，且无法创建：\n{path}",
        "none": "—",
        "easy": "简单",
        "normal": "普通",
        "hard": "困难",
        "very_hard": "极难",
        "legendary": "传奇",
        "base": "基础",
        "mod": "MOD",
        "time_unknown": "未知",
    },
    "en": {
        "window_title": "Total War: Warhammer III — Multiplayer → Singleplayer Save Exporter",
        "info_title": "About",
        "info_text": "Total War: Warhammer III — Multiplayer → Singleplayer Save Exporter\n\nVersion: {version}\nAuthor: {author}\n\nReads a multiplayer save, lists player factions, and exports the selected player as a singleplayer save. The original save is never modified.\n\nSupports Total War: Warhammer III (vanilla/modded saves). The same MODs must be enabled when loading the exported save.",
        "header_hint": "Drop a .save_multiplayer here (or click the area below). The original save is never modified.",
        "drop_dnd": "Drop the multiplayer save here\nor click to open the game's multiplayer save folder\n\nSupports .save_multiplayer\n\nNote: use an auto-save or a manually saved save;\navoid quick saves, as they may be missing some data.",
        "drop_click": "Click to open the game's multiplayer save folder\n\nSupports .save_multiplayer\n\nNote: use an auto-save or a manually saved save;\navoid quick saves, as they may be missing some data.",
        "dir_prefix": "Game multiplayer save folder: ",
        "dir_missing": "not detected automatically (choose manually)",
        "dir_common": "Typical path: C:\\Users\\<name>\\AppData\\Roaming\\The Creative Assembly\\Warhammer3\\save_games_multiplayer",
        "sp_dir_prefix": "Game singleplayer save folder: ",
        "sp_dir_missing": "not detected automatically",
        "sp_dir_create_hint": " (will be created on export)",
        "sp_dir_common": "Typical path: C:/Users/<name>/AppData/Roaming/The Creative Assembly/Warhammer3/save_games",
        "btn_choose_dir": "Change folder",
        "btn_redetect": "Detect again",
        "summary_none": "No save loaded",
        "summary_line": "File: {file}    Turn: {turn}    Saved: {time}    Campaign: {campaign}    Players: {players}",
        "mods_none": "No MODs (vanilla save)",
        "mods_count": "{n} mod(s) / {total} pack(s)",
        "col_idx": "#",
        "col_player": "Player",
        "col_fname": "Faction name",
        "col_key": "Faction key",
        "col_camp": "Campaign",
        "col_battle": "Battle",
        "detail_title": "Selected faction",
        "detail_id": "Faction ID",
        "detail_treasury": "Treasury",
        "detail_income": "Income (excl. trade)",
        "detail_trade": "Trade",
        "detail_expense": "Expense",
        "detail_expected": "Expected income",
        "detail_provinces": "Full provinces",
        "detail_settlements": "Settlements",
        "detail_armies": "Armies (field)",
        "detail_chars": "Characters (lords / agents)",
        "detail_mult": "Battle multiplier",
        "detail_packs": "MOD/Packs",
        "btn_export": "Export selected player as singleplayer save",
        "btn_open": "Open game SP save folder",
        "btn_open_mp": "Open MP save folder",
        "btn_open_sp": "Open game SP save folder",
        "btn_mods": "View MOD list",
        "btn_lang": "中文",
        "status_ready": "No save loaded.",
        "status_loaded": "Loaded. Select a player, then click export.",
        "ai_note": "Military AI for demoted player factions is fixed: the game generates military tasks, and the AI can recruit and move armies. Works with multiplayer saves.",
        "status_converting": "Converting, please wait… (a 15 MB save usually takes seconds)",
        "status_done": "Export complete: {out}",
        "eta_prefix": "ETA: ",
        "eta_seconds": "{s}s",
        "eta_finishing": "Finishing…",
        "eta_done": "Done",
        "eta_failed": "Failed",
        "status_failed": "Export failed:\n{err}",
        "dlg_select_player_title": "Select a player",
        "dlg_select_player_msg": "Please select a player in the list first.",
        "dlg_save_title": "Export singleplayer save",
        "dlg_export_ok_title": "Export complete",
        "dlg_export_ok_msg": "Singleplayer save created:\n{out}\n\nKept player: {keep}\nDemoted to AI: {drop}\n\nCopy it into the game's save_games folder and test.",
        "dlg_export_fail_title": "Export failed",
        "dlg_read_fail_title": "Cannot read",
        "dlg_read_fail_msg": "Cannot read this save:\n{err}",
        "dlg_mods_title": "MOD/Pack list",
        "dlg_mods_msg": "Packs/MODs recorded by this save ({n}):\n\n{lines}",
        "dlg_dir_title": "Select the game's multiplayer save folder",
        "dlg_dir_missing_title": "Folder not found",
        "dlg_dir_missing_msg": "The folder does not exist and could not be created:\n{path}",
        "none": "—",
        "easy": "Easy",
        "normal": "Normal",
        "hard": "Hard",
        "very_hard": "Very Hard",
        "legendary": "Legendary",
        "base": "base",
        "mod": "MOD",
        "time_unknown": "unknown",
    },
}

try:
    from tkinterdnd2 import TkinterDnD, DND_FILES
    _HAS_DND = True
except Exception:
    TkinterDnD = None
    DND_FILES = None
    _HAS_DND = False


def config_path():
    base = os.environ.get("APPDATA") or str(Path.home())
    return Path(base) / "Hammer3MP2SP" / "config.json"


def load_config():
    try:
        with open(config_path(), "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_config(cfg):
    try:
        p = config_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _save_dir_candidates(folder_name="save_games_multiplayer"):
    bases = []
    appdata = os.environ.get("APPDATA")
    if appdata:
        bases.append(Path(appdata))
    up = os.environ.get("USERPROFILE")
    if up:
        bases.append(Path(up) / "AppData" / "Roaming")
        for p in glob.glob(str(Path(up) / "OneDrive*" / "AppData" / "Roaming")):
            bases.append(Path(p))
    for drive in ("C:", "D:", "E:", "F:", "G:"):
        for p in glob.glob("%s/Users/*/AppData/Roaming" % drive):
            bases.append(Path(p))
    out, seen = [], set()
    for b in bases:
        d = b / "The Creative Assembly" / "Warhammer3" / folder_name
        try:
            r = str(d.resolve()).lower()
        except Exception:
            r = str(d).lower()
        if r in seen:
            continue
        seen.add(r)
        if d.is_dir():
            out.append(d)
    return out


def _newest_save_mtime(d, pattern="*.save_multiplayer"):
    try:
        return max((f.stat().st_mtime for f in Path(d).glob(pattern)), default=0)
    except Exception:
        return 0


def detect_save_dir():
    cands = _save_dir_candidates("save_games_multiplayer")
    if not cands:
        return None
    return max(cands, key=lambda p: _newest_save_mtime(p, "*.save_multiplayer"))


def detect_sp_save_dir():
    cands = _save_dir_candidates("save_games")
    if not cands:
        return None
    return max(cands, key=lambda p: _newest_save_mtime(p, "*.save"))


def _normalize_mp_dir(p):
    p = Path(p)
    if p.name.lower() == "save_games_multiplayer":
        return p
    cand = p / "save_games_multiplayer"
    if cand.is_dir():
        return cand
    return p


def _normalize_sp_dir(p):
    p = Path(p)
    if p.name.lower() == "save_games":
        return p
    cand = p / "save_games"
    if cand.parent.is_dir():
        return cand
    return p


def diff_label(lang, v):
    key = DIFF_CODES.get(int(v)) if isinstance(v, (int, float)) else None
    if key:
        return STR[lang].get(key, str(v))
    return str(v)


def fmt_num(v):
    if v is None:
        return "—"
    if isinstance(v, float):
        return ("%.2f" % v).rstrip("0").rstrip(".")
    try:
        return "{:,}".format(int(v))
    except Exception:
        return str(v)


def safe_filename(s):
    bad = '\\/:*?"<>|'
    out = "".join("_" if c in bad else c for c in str(s))
    return out.strip() or "player"


def _header_time(hdr):
    ts = hdr.child("SAVE_GAME_HEADER_TIMESTAMP")
    if ts is None:
        return None
    vals = [c.value for c in ts.children if isinstance(c, esf.Value)]
    if len(vals) < 6:
        return None
    try:
        return "%04d-%02d-%02d %02d:%02d" % (
            int(vals[0]), int(vals[1]), int(vals[2]), int(vals[4]), int(vals[5]))
    except Exception:
        return None


def _read_mods(hdr, campaign_root):
    blk = hdr.child("mod_history_block_name")
    if not isinstance(blk, esf.RecordBlock):
        try:
            blk = campaign_root.child("CAMPAIGN_ENV").child("mod_history_block_name")
        except Exception:
            blk = None
    if not isinstance(blk, esf.RecordBlock):
        return []
    mods = []
    for e in blk.entries:
        vals = [c.value for c in e.children if isinstance(c, esf.Value)]
        if len(vals) >= 3:
            mods.append({"pack": str(vals[0]), "wid": str(vals[1]),
                         "flag": int(vals[2]) if isinstance(vals[2], (int, float)) else 0})
    return mods


def _count_block(node):
    if node is None:
        return None
    if isinstance(node, esf.RecordBlock):
        return len(node.entries)
    if isinstance(node, esf.Record):
        blk = next((c for c in node.children if isinstance(c, esf.RecordBlock)), None)
        return len(blk.entries) if blk else 0
    return None


def _field_army_count(rec):
    """Count lord-led field armies; MILITARY_FORCE_LEGACY[1] == 0 excludes garrisons."""
    aa = rec.child("ARMY_ARRAY")
    if aa is None:
        return None
    total = len(aa.entries)
    field = 0
    found = False
    for e in aa.entries:
        f = e.children[0] if e.children else None
        leg = f.child("MILITARY_FORCE_LEGACY") if f is not None else None
        if leg is not None:
            vals = [c.value for c in leg.children if isinstance(c, esf.Value)]
            if len(vals) > 1:
                found = True
                if vals[1] == 0:
                    field += 1
    return field if found else total


def _find_record(node, name, depth=0):
    """Depth-first search for a named record in the campaign tree."""
    if node is None or depth > 8:
        return None
    for c in getattr(node, "children", []):
        if isinstance(c, esf.Record):
            if c.name == name:
                return c
            found = _find_record(c, name, depth + 1)
            if found is not None:
                return found
        elif isinstance(c, esf.RecordBlock):
            for entry in c.entries:
                found = _find_record(entry, name, depth + 1)
                if found is not None:
                    return found
    return None


def _build_province_data(save):
    """Return (region -> province, province -> region count) from PROVINCES_DATA."""
    provinces = {}
    sizes = {}
    node = _find_record(save.campaign_root, "PROVINCES_DATA")
    if node is None:
        return provinces, sizes
    block = next((c for c in node.children if isinstance(c, esf.RecordBlock)), None)
    if block is None:
        return provinces, sizes
    for entry in block.entries:
        rec = next((c for c in entry.children
                    if isinstance(c, esf.Record) and c.name == "PROVINCE_DATA"), None)
        if rec is None:
            continue
        vals = [c.value for c in rec.children
                if isinstance(c, esf.Value) and isinstance(c.value, str)]
        if not vals:
            continue
        region_block = next((c for c in rec.children
                             if isinstance(c, esf.RecordBlock)), None)
        if region_block is None:
            continue
        sizes[vals[0]] = 0
        for region_entry in region_block.entries:
            region_key = next((c.value for c in region_entry.children
                               if isinstance(c, esf.Value) and isinstance(c.value, str)), None)
            if region_key:
                provinces[region_key] = vals[0]
                sizes[vals[0]] += 1
    return provinces, sizes


def _force_commanders(rec):
    """Return (field_army_commander_ids, all_force_commander_ids)."""
    field = set()
    all_ids = set()
    aa = rec.child("ARMY_ARRAY")
    if aa is None:
        return field, all_ids
    for entry in aa.entries:
        f = entry.children[0] if entry.children else None
        if f is None:
            continue
        vals = [c.value for c in f.children if isinstance(c, esf.Value)]
        if len(vals) < 2 or not isinstance(vals[1], int):
            continue
        cid = vals[1]
        all_ids.add(cid)
        leg = f.child("MILITARY_FORCE_LEGACY")
        lv = [c.value for c in leg.children if isinstance(c, esf.Value)] if leg else []
        if len(lv) > 1 and lv[1] == 0:
            field.add(cid)
    return field, all_ids


def _character_breakdown(rec, field_ids, force_ids):
    """Return (lords, agents) for characters visible outside garrisons.

    Garrison commanders (the colonel entries in HUNT's 5 towns) and other
    army-attached commanders are excluded. A general without a force still
    counts as a lord; every other unassigned character counts as an agent.
    """
    ca = rec.child("CHARACTER_ARRAY")
    if ca is None:
        return None, None
    lords = len(field_ids)
    agents = 0
    seen = set()
    for entry in ca.entries:
        ch = entry.children[0] if entry.children else None
        if ch is None:
            continue
        vals = [c.value for c in ch.children if isinstance(c, esf.Value)]
        if not vals or not isinstance(vals[0], int) or vals[0] in seen:
            continue
        cid = vals[0]
        seen.add(cid)
        ctype = vals[1] if len(vals) > 1 else None
        if cid in force_ids:
            continue
        if ctype == "general":
            lords += 1
        else:
            agents += 1
    return lords, agents


def _faction_details(rec, provinces, settlements):
    if rec is None:
        return {"id": None, "treasury": None, "expected": None,
                "provinces": provinces, "settlements": settlements,
                "armies": None, "chars": None}
    fid = rec.children[0].value if rec.children else None
    treasury = income = trade = expense = None
    base = None
    try:
        eco = rec.child("FACTION_ECONOMICS")
        if eco is not None:
            vals = [c.value for c in eco.children if isinstance(c, esf.Value)]
            treasury = vals[0] if vals else None
            hist = next((c for c in eco.children if isinstance(c, esf.RecordBlock)), None)
            if hist is not None and hist.entries:
                data = hist.entries[-1].children[0]
                arrs = [c for c in data.children if isinstance(c, esf.ValueArray)]
                if len(arrs) > 1:
                    a = arrs[1].items()
                    income = a[0] if a else None
                    trade = a[2] if len(a) > 2 else None
                if len(arrs) > 5:
                    e = arrs[5].items()
                    expense = e[1] if len(e) > 1 else None
                if len(arrs) > 2:
                    b = arrs[2].items()
                    base = b[4] if len(b) > 4 else None
    except Exception:
        pass
    expected = None
    if income is not None and trade is not None and expense is not None:
        expected = income + trade - expense + (base if base is not None else 0)
    try:
        field_ids, force_ids = _force_commanders(rec)
        armies = len(field_ids)
        lords, agents = _character_breakdown(rec, field_ids, force_ids)
        chars = None if lords is None or agents is None else "%d / %d" % (lords, agents)
    except Exception:
        armies = chars = None
    return {"id": fid, "treasury": treasury, "expected": expected,
            "provinces": provinces, "settlements": settlements,
            "armies": armies, "chars": chars}


def read_save_info(path):
    """读取联机存档：玩家派系、难度、派系详情、MOD 列表。"""
    s = esf.SaveFile(path)
    try:
        if not s.is_multiplayer:
            raise ValueError("Not a multiplayer save / 不是联机存档")
        root = s.inner.root if s.inner is not None else s.outer.root
        hdr = root.child("SAVE_GAME_HEADER_MULTIPLAYER")
        if hdr is None:
            raise ValueError("SAVE_GAME_HEADER_MULTIPLAYER not found")
        n = conv.player_count(hdr)
        turn_a, turn_b = hdr.children[3].value, hdr.children[4].value
        season = hdr.children[5].value
        campaign = hdr.children[12].value
        save_time = _header_time(hdr)
        mods = _read_mods(hdr, s.campaign_root)

        world = s.campaign_root.walk("CAMPAIGN_ENV", "CAMPAIGN_MODEL", "WORLD")
        fa = world.child("FACTION_ARRAY")
        famap = {}
        key2id = {}
        for e in fa.entries:
            for c in e.children:
                if isinstance(c, esf.Record) and c.name == "FACTION" and len(c.children) > 1:
                    k = c.children[1].value
                    if isinstance(k, str):
                        famap[k] = c
                        if isinstance(c.children[0].value, int):
                            key2id[k] = c.children[0].value
        # REGION's owner *string* is stale in this MP save; the fifth scalar is
        # the owning faction id and matches the game's town count.
        owned_regions = {}
        regs = world.child("REGION_MANAGER").child("REGIONS_ARRAY")
        for e in regs.entries:
            for c in e.children:
                if isinstance(c, esf.Record) and c.name == "REGION":
                    vals = [x.value for x in c.children if isinstance(x, esf.Value)]
                    if len(vals) >= 5 and isinstance(vals[1], str) and isinstance(vals[4], int):
                        owned_regions.setdefault(vals[4], []).append(vals[1])
        province_map, province_sizes = _build_province_data(s)

        players = []
        for i in range(n):
            b = conv.PLAYER_BASE + conv.PLAYER_SIZE * i
            name, key, flags, fname, u64 = conv.player_block(hdr, i)
            camp = hdr.children[b + 5].value
            battle = hdr.children[b + 6].value
            mult = hdr.children[b + 7].value
            p = {"index": i, "name": name, "key": key, "fname": fname,
                 "campaign": camp, "battle": battle, "mult": mult}
            regions = owned_regions.get(key2id.get(key), [])
            by_province = {}
            for region in regions:
                province = province_map.get(region)
                if province:
                    by_province.setdefault(province, set()).add(region)
            provinces = sum(1 for province, owned in by_province.items()
                            if len(owned) == province_sizes.get(province))
            p.update(_faction_details(famap.get(key), provinces, len(regions)))
            players.append(p)
        return {"turn": (turn_a, turn_b), "season": season, "campaign": campaign,
                "save_time": save_time, "mods": mods, "players": players}
    finally:
        del s


def verify_output(path):
    v = esf.SaveFile(path)
    try:
        hdr = v.outer.root.child("SAVE_GAME_HEADER")
        env = v.campaign_root.child("CAMPAIGN_ENV")
        cs = env.child("CAMPAIGN_SETUP")
        return {
            "root": v.outer.root.name,
            "mp": v.is_multiplayer,
            "faction": hdr.children[0].value if hdr else "?",
            "local": env.child("CAMPAIGN_SETUP_LOCAL").children[0].value,
            "turn": (hdr.children[2].value, hdr.children[3].value) if hdr else None,
            "camp": cs.children[8].value if cs else "?",
            "battle": cs.children[9].value if cs else "?",
            "mult": cs.children[12].value if cs else "?",
        }
    finally:
        del v


def do_convert(src, keep, out_path, save_name):
    keep_key, drop_keys = conv.convert(src, keep, out_path, save_name)
    return keep_key, drop_keys, verify_output(out_path)


def _log_path():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    try:
        test = os.path.join(base, ".write_test")
        with open(test, "w") as f:
            f.write("x")
        os.remove(test)
        return os.path.join(base, "mp2sp_tool.log")
    except Exception:
        import tempfile
        return os.path.join(tempfile.gettempdir(), "mp2sp_tool.log")


def write_log(lines):
    text = "\n".join(str(x) for x in lines)
    try:
        if sys.stdout is not None:
            print(text)
    except Exception:
        pass
    try:
        with open(_log_path(), "w", encoding="utf-8-sig") as f:
            f.write(text + "\n")
    except Exception:
        pass


def _find_arg(argv, flag):
    if flag not in argv:
        return None
    i = argv.index(flag)
    return argv[i + 1] if i + 1 < len(argv) else None


def cli_self_test(argv):
    src = _find_arg(argv, "--self-test")
    if src is None:
        return False
    info = read_save_info(src)
    lines = ["turn=%s season=%s campaign=%s players=%d mods=%d" % (
        info["turn"][1], info["season"], info["campaign"],
        len(info["players"]), len(info["mods"]))]
    for p in info["players"]:
        lines.append("#%d %s | %s | %s | camp=%s battle=%s mult=%s | id=%s treasury=%s expected=%s provinces=%s settlements=%s armies=%s chars=%s" % (
            p["index"], p["name"], p["key"], p["fname"], p["campaign"], p["battle"],
            p["mult"], p["id"], p["treasury"], p["expected"], p["provinces"],
            p["settlements"], p["armies"], p["chars"]))
    for m in info["mods"]:
        lines.append("mod: %s | %s | flag=%s" % (m["pack"], m["wid"], m["flag"]))
    write_log(lines)
    return True


def cli_export(argv):
    src = _find_arg(argv, "--export")
    if src is None:
        return False
    try:
        i = argv.index("--export")
        keep, out = int(argv[i + 2]), argv[i + 3]
    except Exception:
        write_log(["ERR: usage --export <save> <player_index> <out>"])
        return True
    keep_key, drop_keys, info = do_convert(
        src, keep, out, "导出 - " + os.path.splitext(os.path.basename(out))[0])
    write_log(["EXPORT OK", "kept=%s" % keep_key,
               "demoted=%s" % drop_keys, "info=%s" % info])
    return True


def cli_smoke_test(argv):
    src = _find_arg(argv, "--smoke-test")
    if src is None:
        return False
    root = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    root.withdraw()
    app = App(root)
    app.load_file(src)
    root.update()
    app.toggle_lang()
    root.update()
    for iid in app.tree.get_children():
        app.tree.selection_set(iid)
        app.on_select()
        root.update()
    app.toggle_lang()
    root.update()
    root.destroy()
    write_log(["SMOKE OK", "game_dir=%s" % app.game_dir, "sp_game_dir=%s" % app.sp_game_dir])
    return True


class App:
    def __init__(self, root, initial_path=None):
        self.root = root
        self.cfg = load_config()
        self.lang = self.cfg.get("lang", "zh")
        if self.lang not in STR:
            self.lang = "zh"
        self.src = None
        self.info = None
        self.last_out = None
        self.detected = _save_dir_candidates("save_games_multiplayer")
        gd = self.cfg.get("last_game_dir")
        self.game_dir = _normalize_mp_dir(gd) if gd and Path(gd).is_dir() else detect_save_dir()
        if self.game_dir is None and self.detected:
            self.game_dir = self.detected[0]
        sd = self.cfg.get("last_sp_game_dir")
        self.sp_game_dir = _normalize_sp_dir(sd) if sd and Path(sd).is_dir() else detect_sp_save_dir()
        if self.sp_game_dir is None and self.game_dir is not None:
            sib = self.game_dir.parent / "save_games"
            if sib.parent.is_dir():
                self.sp_game_dir = sib
        # Repair old configs that stored the Warhammer3 parent instead of the real folders.
        if self.game_dir is not None:
            self.cfg["last_game_dir"] = str(self.game_dir)
        if self.sp_game_dir is not None:
            self.cfg["last_sp_game_dir"] = str(self.sp_game_dir)
        save_config(self.cfg)
        ld = self.cfg.get("last_dir")
        self.last_dir = Path(ld) if ld and Path(ld).is_dir() else self.game_dir
        self._converting = False
        self._progress_job = None
        self._conv_start = 0.0
        self._conv_est = 0.0
        self._build()
        if initial_path and os.path.isfile(initial_path):
            self.root.after(100, lambda: self.load_file(initial_path))

    def t(self, key, **kw):
        s = STR.get(self.lang, STR["zh"]).get(key)
        if s is None:
            s = STR["zh"].get(key, key)
        try:
            return s.format(**kw)
        except Exception:
            return s

    def _build(self):
        self.root.title(self.t("window_title"))
        self.root.geometry("1060x740")
        self.root.minsize(860, 620)
        try:
            self.root.tk.call("tk", "scaling", 1.25)
        except Exception:
            pass
        try:
            ttk.Style().theme_use("vista")
        except Exception:
            pass
        st = ttk.Style()
        st.configure("Title.TLabel", font=("Microsoft YaHei UI", 14, "bold"))
        st.configure("Hint.TLabel", foreground="#666666")
        st.configure("Note.TLabel", font=("Microsoft YaHei UI", 8), foreground="#999999")
        st.configure("Drop.TLabel", font=("Microsoft YaHei UI", 11),
                     background="#f5f7fb", foreground="#333333",
                     anchor="center", padding=18)
        st.configure("Treeview", rowheight=27, font=("Microsoft YaHei UI", 9))
        st.configure("Treeview.Heading", font=("Microsoft YaHei UI", 9, "bold"))
        st.configure("Detail.TLabel", font=("Microsoft YaHei UI", 9))
        st.configure("DetailKey.TLabel", foreground="#666666")

        try:
            self._icon_img = tk.PhotoImage(data=ICON_PNG_B64)
            self.root.iconphoto(True, self._icon_img)
        except Exception:
            self._icon_img = None

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=14, pady=(12, 0))
        self.btn_info = ttk.Button(top, text="!", width=3, command=self.show_info)
        self.btn_info.pack(side="left", padx=(0, 8))
        self.lbl_title = ttk.Label(top, text=self.t("window_title"), style="Title.TLabel")
        self.lbl_title.pack(side="left")
        self.btn_lang = ttk.Button(top, text=self.t("btn_lang"), width=6, command=self.toggle_lang)
        self.btn_lang.pack(side="right")
        self.lbl_hint = ttk.Label(self.root, text=self.t("header_hint"), style="Hint.TLabel", wraplength=1010)
        self.lbl_hint.pack(anchor="w", padx=14, pady=(2, 0))

        self.drop = ttk.Label(self.root, text=self.t("drop_dnd" if _HAS_DND else "drop_click"),
                              style="Drop.TLabel", relief="groove")
        self.drop.pack(fill="x", padx=14, pady=9)
        self.drop.bind("<Button-1>", lambda e: self.choose_file())
        if _HAS_DND:
            try:
                self.drop.drop_target_register(DND_FILES)
                self.drop.dnd_bind("<<Drop>>", self.on_drop)
            except Exception:
                pass

        dirbar = ttk.Frame(self.root)
        dirbar.pack(fill="x", padx=14)
        self.lbl_dir = ttk.Label(dirbar, text="", style="Hint.TLabel", wraplength=690)
        self.lbl_dir.pack(side="left", fill="x", expand=True)
        self.btn_redetect = ttk.Button(dirbar, text=self.t("btn_redetect"),
                                       command=self.redetect_dir)
        self.btn_redetect.pack(side="right", padx=(4, 0))
        self.btn_choose_dir = ttk.Button(dirbar, text=self.t("btn_choose_dir"),
                                         command=self.choose_dir)
        self.btn_choose_dir.pack(side="right")
        self.update_dir_label()

        dirbtns = ttk.Frame(self.root)
        dirbtns.pack(fill="x", padx=14, pady=(4, 0))
        self.btn_open_mp = ttk.Button(dirbtns, text=self.t("btn_open_mp"),
                                      command=self.open_mp_dir)
        self.btn_open_sp = ttk.Button(dirbtns, text=self.t("btn_open_sp"),
                                      command=self.open_sp_dir)
        self.btn_open_sp.pack(side="right")
        self.btn_open_mp.pack(side="right", padx=(0, 4))

        self.summary = ttk.Label(self.root, text=self.t("summary_none"), style="Hint.TLabel", wraplength=1010)
        self.summary.pack(anchor="w", padx=14, pady=(4, 0))

        cols = ("idx", "name", "fname", "key", "camp", "battle")
        frame = ttk.Frame(self.root)
        frame.pack(fill="both", expand=True, padx=14, pady=(6, 0))
        self.tree = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        widths = {"idx": 42, "name": 150, "fname": 190, "key": 330, "camp": 100, "battle": 100}
        for c in cols:
            heading = "col_player" if c == "name" else "col_" + c
            self.tree.heading(c, text=self.t(heading))
            self.tree.column(c, width=widths[c], anchor="w" if c in ("name", "fname", "key") else "center")
        self.tree.pack(side="left", fill="both", expand=True)
        sb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.on_select())
        self.tree.bind("<Double-1>", lambda e: self.export_selected())

        self.det_frame = ttk.LabelFrame(self.root, text=self.t("detail_title"))
        self.det_frame.pack(fill="x", padx=14, pady=(8, 0))
        self.detail_keys = ("id", "treasury", "expected", "provinces",
                            "settlements", "armies", "chars", "mult")
        self.detail_vars = {}
        self.detail_key_labels = []
        for i, k in enumerate(self.detail_keys):
            r, c = divmod(i, 4)
            lbl = ttk.Label(self.det_frame, text=self.t("detail_" + k) + "：",
                            style="DetailKey.TLabel")
            lbl.grid(row=r, column=c * 2, sticky="e", padx=(10, 2), pady=3)
            self.detail_key_labels.append((lbl, k))
            v = tk.StringVar(value=self.t("none"))
            self.detail_vars[k] = v
            ttk.Label(self.det_frame, textvariable=v, style="Detail.TLabel",
                      width=16, anchor="w").grid(
                row=r, column=c * 2 + 1, sticky="w", padx=(0, 14), pady=3)
        self.btn_mods = ttk.Button(self.det_frame, text=self.t("btn_mods"),
                                   command=self.show_mods, state="disabled")
        self.btn_mods.grid(row=2, column=6, columnspan=2, sticky="e", padx=10, pady=(2, 6))

        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=14, pady=8)
        self.btn_export = ttk.Button(bar, text=self.t("btn_export"),
                                     command=self.export_selected, state="disabled")
        self.btn_export.pack(side="left")
        right = ttk.Frame(bar)
        right.pack(side="right")
        self.progress = ttk.Progressbar(right, mode="determinate", maximum=100,
                                        value=0, length=220)
        self.progress.pack(anchor="e")
        self.lbl_eta = ttk.Label(right, text="", style="Hint.TLabel")
        self.lbl_eta.pack(anchor="e", pady=(2, 0))

        self.status = tk.Text(self.root, height=3, wrap="word",
                              font=("Microsoft YaHei UI", 9), relief="flat",
                              background="#f7f7f7")
        self.status.pack(fill="x", padx=14, pady=(0, 4))
        self.status.configure(state="disabled")
        self.lbl_ai_note = ttk.Label(self.root, text=self.t("ai_note"),
                                     style="Note.TLabel", wraplength=1010)
        self.lbl_ai_note.pack(fill="x", padx=14, pady=(0, 6))
        self.set_status(self.t("status_ready"))

    def set_status(self, text):
        self.status.configure(state="normal")
        self.status.delete("1.0", "end")
        self.status.insert("end", text)
        self.status.configure(state="disabled")

    def update_dir_label(self):
        if self.game_dir and Path(self.game_dir).is_dir():
            mp = self.t("dir_prefix") + str(self.game_dir)
        else:
            mp = self.t("dir_prefix") + self.t("dir_missing") + "\n" + self.t("dir_common")
        if self.sp_game_dir:
            sp = self.t("sp_dir_prefix") + str(self.sp_game_dir)
            if not Path(self.sp_game_dir).is_dir():
                sp += self.t("sp_dir_create_hint")
        else:
            sp = self.t("sp_dir_prefix") + self.t("sp_dir_missing") + "\n" + self.t("sp_dir_common")
        self.lbl_dir.configure(text=mp + "\n" + sp)

    def retranslate(self):
        self.root.title(self.t("window_title"))
        self.lbl_title.configure(text=self.t("window_title"))
        self.lbl_hint.configure(text=self.t("header_hint"))
        self.btn_lang.configure(text=self.t("btn_lang"))
        if hasattr(self, "lbl_ai_note"):
            self.lbl_ai_note.configure(text=self.t("ai_note"))
        self.drop.configure(text=self.t("drop_dnd" if _HAS_DND else "drop_click"))
        self.btn_redetect.configure(text=self.t("btn_redetect"))
        self.btn_choose_dir.configure(text=self.t("btn_choose_dir"))
        for c in ("idx", "name", "fname", "key", "camp", "battle"):
            heading = "col_player" if c == "name" else "col_" + c
            self.tree.heading(c, text=self.t(heading))
        self.det_frame.configure(text=self.t("detail_title"))
        for lbl, k in self.detail_key_labels:
            lbl.configure(text=self.t("detail_" + k) + "：")
        self.update_dir_label()
        self.btn_export.configure(text=self.t("btn_export"))
        self.btn_open_mp.configure(text=self.t("btn_open_mp"))
        self.btn_open_sp.configure(text=self.t("btn_open_sp"))
        self.btn_mods.configure(text=self.t("btn_mods"))
        if self.info:
            self.render_summary()
            self.render_tree()
            sel = self.tree.get_children()
            if sel:
                self.tree.selection_set(sel[0])
            self.on_select()
            self.set_status(self.t("status_loaded"))
        else:
            self.summary.configure(text=self.t("summary_none"))
            for k in self.detail_keys:
                self.detail_vars[k].set(self.t("none"))
            self.set_status(self.t("status_ready"))

    def show_info(self):
        messagebox.showinfo(self.t("info_title"),
                            self.t("info_text", version=APP_VERSION, author=APP_AUTHOR),
                            parent=self.root)

    def toggle_lang(self):
        self.lang = "en" if self.lang == "zh" else "zh"
        self.cfg["lang"] = self.lang
        save_config(self.cfg)
        self.retranslate()

    def choose_dir(self):
        initial = str(self.game_dir or self.last_dir or Path.home())
        d = filedialog.askdirectory(title=self.t("dlg_dir_title"), initialdir=initial)
        if d:
            p = Path(d)
            if p.name.lower() == "save_games":
                self.sp_game_dir = p
                mp = p.parent / "save_games_multiplayer"
                if mp.is_dir():
                    self.game_dir = mp
            else:
                self.game_dir = _normalize_mp_dir(p)
                sib = self.game_dir.parent / "save_games"
                if sib.parent.is_dir():
                    self.sp_game_dir = sib
            self.last_dir = p
            self.cfg["last_game_dir"] = str(self.game_dir) if self.game_dir else ""
            self.cfg["last_sp_game_dir"] = str(self.sp_game_dir) if self.sp_game_dir else ""
            self.cfg["last_dir"] = str(p)
            save_config(self.cfg)
            self.update_dir_label()

    def redetect_dir(self):
        self.detected = _save_dir_candidates("save_games_multiplayer")
        self.game_dir = detect_save_dir()
        if self.game_dir is None and self.detected:
            self.game_dir = self.detected[0]
        self.sp_game_dir = detect_sp_save_dir()
        if self.sp_game_dir is None and self.game_dir is not None:
            sib = self.game_dir.parent / "save_games"
            if sib.parent.is_dir():
                self.sp_game_dir = sib
        if self.game_dir is not None:
            self.cfg["last_game_dir"] = str(self.game_dir)
        if self.sp_game_dir is not None:
            self.cfg["last_sp_game_dir"] = str(self.sp_game_dir)
        save_config(self.cfg)
        self.update_dir_label()

    def choose_file(self):
        initial = str(self.game_dir or self.last_dir or Path.home())
        initialfile = None
        try:
            files = sorted(Path(initial).glob("*.save_multiplayer"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
            if files:
                initialfile = files[0].name
        except Exception:
            pass
        p = filedialog.askopenfilename(
            title=self.t("window_title"),
            initialdir=initial,
            initialfile=initialfile,
            filetypes=[("Multiplayer save", "*.save_multiplayer"), ("All files", "*.*")])
        if p:
            self.load_file(p)

    def on_drop(self, event):
        try:
            items = self.root.tk.splitlist(event.data)
            if items:
                self.load_file(items[0])
        except Exception as ex:
            self.set_status(str(ex))

    def load_file(self, path):
        try:
            info = read_save_info(path)
        except Exception as ex:
            messagebox.showerror(
                self.t("dlg_read_fail_title"),
                self.t("dlg_read_fail_msg", err="%s\n%s" % (ex, traceback.format_exc(limit=2))),
                parent=self.root)
            return
        self.src = path
        self.info = info
        if not self._converting:
            self.progress.configure(value=0)
            self.lbl_eta.configure(text="")
        self.last_dir = Path(os.path.dirname(os.path.abspath(path)))
        self.cfg["last_dir"] = str(self.last_dir)
        save_config(self.cfg)
        self.update_dir_label()
        self.render_summary()
        self.render_tree()
        self.btn_export.configure(state="normal")
        first = self.tree.get_children()
        if first:
            self.tree.selection_set(first[0])
            self.on_select()
        self.set_status(self.t("status_loaded"))

    def render_summary(self):
        info = self.info
        if not info:
            self.summary.configure(text=self.t("summary_none"))
            return
        turn = str(info["turn"][1])
        self.summary.configure(text=self.t(
            "summary_line",
            file=os.path.basename(self.src or ""),
            turn=turn,
            time=info.get("save_time") or self.t("time_unknown"),
            campaign=info.get("campaign") or "—",
            players=len(info["players"])))

    def render_tree(self):
        self.tree.delete(*self.tree.get_children())
        if not self.info:
            return
        for p in self.info["players"]:
            self.tree.insert("", "end", iid=str(p["index"]), values=(
                p["index"], p["name"], p["fname"], p["key"],
                diff_label(self.lang, p["campaign"]), diff_label(self.lang, p["battle"])))

    def selected_player(self):
        sel = self.tree.selection()
        if not sel or not self.info:
            return None
        idx = int(sel[0])
        return next((p for p in self.info["players"] if p["index"] == idx), None)

    def on_select(self):
        p = self.selected_player()
        if not p:
            for k in self.detail_keys:
                self.detail_vars[k].set(self.t("none"))
            self.btn_mods.configure(state="disabled")
            return
        for k in self.detail_keys:
            self.detail_vars[k].set(fmt_num(p.get(k)))
        self.btn_mods.configure(state="normal")

    def show_mods(self):
        if not self.info:
            return
        real = [m for m in self.info["mods"]
                if m["pack"].lower() != "wh3_main_combi.pack"]
        if not real:
            messagebox.showinfo(self.t("dlg_mods_title"), self.t("mods_none"),
                                parent=self.root)
            return
        lines = ["%s  (%s)" % (m["pack"], m["wid"]) for m in real]
        messagebox.showinfo(self.t("dlg_mods_title"),
                            self.t("dlg_mods_msg", n=len(lines), lines="\n".join(lines)),
                            parent=self.root)

    def export_selected(self):
        if not self.src or not self.info:
            return
        p = self.selected_player()
        if p is None:
            messagebox.showinfo(self.t("dlg_select_player_title"),
                                self.t("dlg_select_player_msg"), parent=self.root)
            return
        default = "SP_%s.save" % safe_filename(p["fname"] or p["key"])
        if self.sp_game_dir:
            try:
                Path(self.sp_game_dir).mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
        out = filedialog.asksaveasfilename(
            title=self.t("dlg_save_title"),
            defaultextension=".save",
            initialdir=str(self.sp_game_dir or (self.game_dir.parent if self.game_dir else None) or self.last_dir or Path(self.src).parent),
            initialfile=default,
            filetypes=[("Singleplayer save", "*.save")])
        if not out:
            return
        self.btn_export.configure(state="disabled")
        self._start_progress()
        self.set_status(self.t("status_converting"))
        save_name = os.path.splitext(os.path.basename(out))[0]

        def work():
            try:
                keep_key, drop_keys, info = do_convert(self.src, p["index"], out, save_name)
                self.root.after(0, lambda: self.done(out, keep_key, drop_keys, info))
            except Exception:
                err = traceback.format_exc()
                self.root.after(0, lambda: self.failed(err))

        threading.Thread(target=work, daemon=True).start()

    def _start_progress(self):
        self._converting = True
        try:
            size_mb = os.path.getsize(self.src) / (1024 * 1024)
        except Exception:
            size_mb = 10.0
        self._conv_start = time.monotonic()
        self._conv_est = max(5.0, min(30.0, 3.0 + size_mb * 0.45))
        self.progress.configure(value=0)
        secs = int(self._conv_est + 0.999)
        self.lbl_eta.configure(text=self.t("eta_prefix") +
                                    self.t("eta_seconds", s=secs))
        if self._progress_job:
            try:
                self.root.after_cancel(self._progress_job)
            except Exception:
                pass
            self._progress_job = None
        self._progress_job = self.root.after(100, self._tick_progress)

    def _tick_progress(self):
        if not self._converting:
            return
        elapsed = time.monotonic() - self._conv_start
        ratio = min(0.95, elapsed / max(self._conv_est, 0.1))
        try:
            self.progress.configure(value=ratio * 100)
        except Exception:
            pass
        rem = self._conv_est - elapsed
        if ratio >= 0.95 or rem <= 0.5:
            self.lbl_eta.configure(text=self.t("eta_finishing"))
        else:
            self.lbl_eta.configure(text=self.t("eta_prefix") +
                                        self.t("eta_seconds", s=max(1, int(rem + 0.999))))
        self._progress_job = self.root.after(120, self._tick_progress)

    def _stop_progress(self, done=False, failed=False):
        self._converting = False
        if self._progress_job:
            try:
                self.root.after_cancel(self._progress_job)
            except Exception:
                pass
            self._progress_job = None
        if done:
            self.progress.configure(value=100)
            self.lbl_eta.configure(text=self.t("eta_done"))
        elif failed:
            self.progress.configure(value=0)
            self.lbl_eta.configure(text=self.t("eta_failed"))

    def done(self, out, keep_key, drop_keys, info):
        self._stop_progress(done=True)
        self.btn_export.configure(state="normal")
        self.last_out = out
        self.set_status(self.t("status_done", out=out))
        messagebox.showinfo(self.t("dlg_export_ok_title"),
                            self.t("dlg_export_ok_msg", out=out, keep=keep_key,
                                   drop=", ".join(drop_keys) or self.t("none")),
                            parent=self.root)

    def failed(self, err):
        self._stop_progress(failed=True)
        self.btn_export.configure(state="normal")
        self.set_status(self.t("status_failed", err=err))
        messagebox.showerror(self.t("dlg_export_fail_title"), err[-1500:], parent=self.root)

    def _open_dir(self, path, create=False):
        if not path:
            messagebox.showwarning(self.t("dlg_dir_missing_title"),
                                   self.t("dlg_dir_missing_msg", path="—"),
                                   parent=self.root)
            return
        p = Path(path)
        try:
            if create:
                p.mkdir(parents=True, exist_ok=True)
            if not p.is_dir():
                raise FileNotFoundError(str(p))
            os.startfile(str(p))
        except Exception:
            messagebox.showwarning(self.t("dlg_dir_missing_title"),
                                   self.t("dlg_dir_missing_msg", path=str(p)),
                                   parent=self.root)

    def open_mp_dir(self):
        self._open_dir(self.game_dir, create=False)

    def open_sp_dir(self):
        self._open_dir(self.sp_game_dir, create=True)


def main():
    if cli_self_test(sys.argv):
        return 0
    if cli_export(sys.argv):
        return 0
    if cli_smoke_test(sys.argv):
        return 0
    initial = None
    for a in sys.argv[1:]:
        if a.lower().endswith(".save_multiplayer") and os.path.isfile(a):
            initial = a
            break
    root = TkinterDnD.Tk() if _HAS_DND else tk.Tk()
    App(root, initial_path=initial)
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
