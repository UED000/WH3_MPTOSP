# -*- coding: utf-8 -*-
"""MP -> SP save conversion (experimental).

usage: python convert_mp_sp.py <mp_save> <player_index 0|1> <out_path> <save_name>
"""
import lzma
import struct
import sys

from esf import (SaveFile, EsfFile, Record, RecordBlock, Value, ValueArray,
                 write_varint, LZMA_FILTER)
import tables
from faction_portraits import FACTION_PORTRAITS


def name_idx(esf, name):
    if name in esf.names:
        return esf.names.index(name)
    esf.names.append(name)
    return len(esf.names) - 1


def enc_ascii(esf, s):
    return b"\x0f" + struct.pack("<I", esf.intern_ascii(s))


def enc_utf16(esf, s):
    return b"\x0e" + struct.pack("<I", esf.intern_utf16(s))


def enc_u32(v):
    return b"\x08" + struct.pack("<I", v)


def rec_header(nidx, version, content_len):
    return (bytes([0xA0]) + struct.pack("<H", nidx) + bytes([version])
            + write_varint(content_len))


def copy_node(esf, node):
    return esf.data[node.start:node.cend]


PROFILE = None      # utf16 profilový string vlastníka (z jeho SP savu)


PLAYER_BASE = 17        # první hráčský blok v MP hlavičce
PLAYER_SIZE = 10        # polí na hráče


def player_count(mp_hdr):
    return mp_hdr.children[16].value


def player_block(mp_hdr, i):
    """(name, faction_key, flags_path, faction_name, u64) hráče i."""
    k = mp_hdr.children
    b = PLAYER_BASE + PLAYER_SIZE * i
    return (str(k[b].value), str(k[b + 1].value), str(k[b + 2].value),
            str(k[b + 3].value), k[b + 4].value)


def build_gpsi(esf, mp_hdr, keep):
    """SP-style GAME_PERSISTENT_SESSION_ID: only the kept player's identity."""
    g = mp_hdr.child("GAME_PERSISTENT_SESSION_ID")
    kids = g.children                       # [utf16, u64[], TIMESTAMP]
    u64_keep = player_block(mp_hdr, keep)[4]
    ident = (enc_utf16(esf, PROFILE) if PROFILE
             else copy_node(esf, kids[0]))
    content = (ident
               + b"\x49" + write_varint(8) + struct.pack("<Q", u64_keep)
               + copy_node(esf, kids[2]))
    return rec_header(name_idx(esf, "GAME_PERSISTENT_SESSION_ID"),
                      g.version, len(content)) + content


def group_node(esf, mp_hdr, block_name, index, empty_code):
    """Copy the kept player's per-player region/force array node from the MP header.

    MP stores REGION_OWNERSHIP_KEYS / REGION_OWNERSHIP_PALETTES / FORCE_LOCATIONS as
    RecordBlocks with one entry per player. SP stores them as flat arrays in
    SAVE_GAME_HEADER[16..18]. Copying the kept player's group preserves the
    region-ownership palette cache that would otherwise be empty.
    """
    blk = mp_hdr.child(block_name)
    if isinstance(blk, RecordBlock) and len(blk.entries) > index:
        arr = next((c for c in blk.entries[index].children if isinstance(c, ValueArray)), None)
        if arr is not None:
            return copy_node(esf, arr)
    return bytes([empty_code]) + bytes([0])


def _faction_leader_id(rec):
    gov = rec.child("GOVERNMENT")
    if gov is None:
        return None
    block = next((c for c in gov.children if isinstance(c, RecordBlock)), None)
    if block is None:
        return None
    for entry in block.entries:
        for node in entry.children:
            if isinstance(node, Record) and node.name == "CHARACTER_POST":
                vals = [c.value for c in node.children if isinstance(c, Value)]
                if len(vals) >= 3 and vals[1] == "faction_leader" and isinstance(vals[2], int):
                    return vals[2]
    return None


def _leader_unit_key(rec, leader_id):
    aa = rec.child("ARMY_ARRAY")
    if aa is None or leader_id is None:
        return None
    for entry in aa.entries:
        force = entry.children[0] if entry.children else None
        if force is None:
            continue
        vals = [c.value for c in force.children if isinstance(c, Value)]
        if len(vals) < 2 or vals[1] != leader_id:
            continue
        uc = force.child("UNIT_CONTAINER")
        block = next((c for c in uc.children if isinstance(c, RecordBlock)), None) if uc else None
        if block is None or not block.entries:
            continue
        unit = block.entries[0].children[0]
        key = unit.child("UNIT_RECORD_KEY")
        if key is not None and key.children:
            return str(key.children[0].value)
    return None


def faction_portrait(faction_key, rec):
    """Pick the faction leader portrait path stored in the SP header."""
    options = FACTION_PORTRAITS.get(faction_key, [])
    if not options:
        return ""
    leader_id = _faction_leader_id(rec)
    unit_key = _leader_unit_key(rec, leader_id)
    if unit_key:
        for subtype, image in options:
            if unit_key == subtype + "_0" or unit_key.startswith(subtype + "_"):
                return image
    images = {image for _subtype, image in options}
    if len(images) == 1:
        return next(iter(images))
    return options[0][1]


def build_sp_header(esf, mp_hdr, keep, save_name, portrait=""):
    """Assemble SAVE_GAME_HEADER (v3) bytes from MP header data."""
    k = mp_hdr.children
    _, faction_key, flags_path, faction_name, _ = player_block(mp_hdr, keep)
    # MP stores [turn_index, current_turn] (0-based index / 1-based current).
    # Native SP stores the SAME 1-based current turn in both header fields.
    turn_a = turn_b = k[4].value
    season = str(k[5].value)
    parts = [
        enc_ascii(esf, faction_key),        # 0 faction key
        enc_ascii(esf, portrait),           # 1 faction leader portrait
        enc_u32(turn_a),                    # 2
        enc_u32(turn_b),                    # 3
        enc_utf16(esf, season),             # 4
        enc_ascii(esf, flags_path),         # 5
        copy_node(esf, k[7]),               # 6 DATE
        enc_utf16(esf, faction_name),       # 7 faction screen name
        build_gpsi(esf, mp_hdr, keep),      # 8 GPSI (jen náš u64)
        copy_node(esf, k[9]),               # 9 unk25
        copy_node(esf, k[10]),              # 10 TIMESTAMP
        enc_utf16(esf, save_name),          # 11 save name
        copy_node(esf, k[12]),              # 12 campaign key
        copy_node(esf, k[13]),              # 13 ''
        copy_node(esf, k[14]),              # 14 build version
        copy_node(esf, mp_hdr.child("MAPS")),           # 15 MAPS
        group_node(esf, mp_hdr, "REGION_OWNERSHIP_KEYS", keep, 0x4F),     # 16
        group_node(esf, mp_hdr, "REGION_OWNERSHIP_PALETTES", keep, 0x48), # 17
        group_node(esf, mp_hdr, "FORCE_LOCATIONS", keep, 0x4C),           # 18
        copy_node(esf, mp_hdr.child("mod_history_block_name")),  # 19 mod_history
    ]
    content = b"".join(parts)
    return rec_header(name_idx(esf, "SAVE_GAME_HEADER"), 3, len(content)) + content


def esf_file_bytes(esf, body):
    out = bytearray()
    out += struct.pack("<IIII", esf.magic, esf.unknown, esf.timestamp,
                       16 + len(body))
    out += body
    out += struct.pack("<H", len(esf.names))
    for nm in esf.names:
        b = nm.encode("ascii")
        out += struct.pack("<H", len(b)) + b
    wide = esf._wide            # ABCB: u32 délky stringů, ABCA: u16
    out += struct.pack("<I", len(esf.utf16))
    for idx, s in esf.utf16.items():
        b = s.encode("utf-16-le")
        out += (struct.pack("<I", len(b) // 2) if wide
                else struct.pack("<H", len(b) // 2)) + b + struct.pack("<I", idx)
    out += struct.pack("<I", len(esf.ascii))
    for idx, s in esf.ascii.items():
        b = s.encode("latin-1")
        out += (struct.pack("<I", len(b)) if wide
                else struct.pack("<H", len(b))) + b + struct.pack("<I", idx)
    return bytes(out)


# stav hráče u frakce — enum ve hře (Warhammer3.exe): FULL_HUMAN=0, IDLE_HUMAN=1, NON_HUMAN=2
HUMAN_STATES = ("FULL_HUMAN", "IDLE_HUMAN", "NON_HUMAN")


def _u32_array_items(arr):
    """Pole u32 id (HUMAN_FACTIONS, TURN_GROUP): hra ho ukládá nejmenším kódováním, do kterého se
    vejdou všechny prvky — 0x16 = 1 B, 0x17 = 2 B LE, 0x18 = 3 B BE, 0x08 = raw 4 B LE
    (ověřeno v optimizeru Warhammer3.exe). "arr16" vs "arr17" tedy není struktura, jen hodnoty."""
    c, d = arr.base_code, bytes(arr.raw)
    if c == 0x16:
        return list(d)
    if c == 0x17:
        return list(struct.unpack("<%dH" % (len(d) // 2), d))
    if c == 0x18:
        return [(d[i] << 16) | (d[i + 1] << 8) | d[i + 2] for i in range(0, len(d) - 2, 3)]
    if c == 0x08:
        return list(struct.unpack("<%dI" % (len(d) // 4), d))
    raise ValueError("unexpected faction-id array type 0x%02X" % c)


def _set_u32_array(arr, ids):
    """Přepíše pole u32 id a zvolí typ pole stejně jako hra (viz _u32_array_items)."""
    m = max(ids, default=0)
    if m < 0x100:
        code, payload = 0x16, bytes(ids)
    elif m < 0x10000:
        code, payload = 0x17, b"".join(struct.pack("<H", v) for v in ids)
    elif m < 0x1000000:
        code, payload = 0x18, b"".join(bytes([(v >> 16) & 0xFF, (v >> 8) & 0xFF, v & 0xFF]) for v in ids)
    else:
        code, payload = 0x08, b"".join(struct.pack("<I", v) for v in ids)
    arr.code = code | 0x40
    arr._new = payload
    arr.mark_dirty()


def _turn_group_order(ids):
    """Native SP keeps AI faction ids sorted, with faction id 1 last."""
    out = sorted(set(ids))
    if 1 in out:
        out.remove(1)
        out.append(1)
    return out


def _human_flag_node(rec):
    return next((c for c in rec.children if isinstance(c, Value) and c.type_name == "ascii"
                 and str(c.value) in HUMAN_STATES), None)


def local_faction_key(save):
    env = save.campaign_root.child("CAMPAIGN_ENV")
    loc = env.child("CAMPAIGN_SETUP_LOCAL") if env is not None else None
    return str(loc.children[0].value) if loc is not None and loc.children else None


def stale_human_factions(save):
    """[(id, key)] frakcí, které mají v CAMPAIGN_PLAYER_SETUP „NON_HUMAN", ale na záznamu
    FACTION ještě lidský příznak — pozůstatek převodu verzí 1.2–1.2.2 (GitHub issue #1).
    Hra si takovou frakci při načtení zařadí do lidské skupiny tahu a na konci tahu
    čeká na její tah, který nikdy nepřijde (ověřeno na převedeném savu)."""
    local = local_faction_key(save)
    out = []
    for f in tables.factions(save):
        if f["key"] == local:
            continue
        rec = f["record"]
        ps = rec.child("CAMPAIGN_PLAYER_SETUP")
        a = _human_flag_node(ps) if ps is not None else None
        b = _human_flag_node(rec)
        if a is not None and b is not None and str(a.value) == "NON_HUMAN" \
                and str(b.value) != "NON_HUMAN":
            out.append((f["id"], f["key"]))
    return out


def repair_converted(save):
    """Opraví zaseknutý převedený singleplayer save (viz stale_human_factions): FACTION příznak
    → NON_HUMAN, HUMAN_FACTIONS = jen lokální frakce, lidská TURN_GROUP = jen lokální frakce,
    vše ostatní do největší AI skupiny. Vrací (opravené [(id, key)], přesunutá id)."""
    if save.is_multiplayer:
        raise ValueError("multiplayer save")
    local = local_faction_key(save)
    fac_ids = {f["key"]: f["id"] for f in tables.factions(save)}
    if local not in fac_ids:
        raise ValueError("local faction %r not found" % local)
    keep_id = fac_ids[local]
    fixed = stale_human_factions(save)
    facs = {f["id"]: f["record"] for f in tables.factions(save)}
    for fid, _key in fixed:
        _human_flag_node(facs[fid]).value = "NON_HUMAN"
    model = save.campaign_root.walk("CAMPAIGN_ENV", "CAMPAIGN_MODEL")
    hf_arr = next(c for c in model.child("HUMAN_FACTIONS").children if isinstance(c, ValueArray))
    if _u32_array_items(hf_arr) != [keep_id]:
        _set_u32_array(hf_arr, [keep_id])
    tc = model.child("WORLD").child("TURN_CONTROL")
    tg_blk = next(c for c in tc.children if isinstance(c, RecordBlock))
    groups = []
    for e in tg_blk.entries:
        arrs = [c for c in e.children if isinstance(c, ValueArray)]
        if arrs:
            groups.append((e, arrs[0], _u32_array_items(arrs[0])))
    human = [g for g in groups if keep_id in g[2]]
    moved = []
    if len(human) == 1:
        e, head, ids = human[0]
        moved = [i for i in ids if i != keep_id]
        if moved:
            _set_u32_array(head, [keep_id])
            others = [g for g in groups if g is not human[0]]
            if others:
                e2, head2, ids2 = max(others, key=lambda g: len(g[2]))
                _set_u32_array(head2, _turn_group_order(ids2 + moved))
    return fixed, moved


def _enable_ai_managers(model, index_by_key, keys):
    """Switch CAI faction managers from the human value (6) to AI (7).

    A faction that was human in the MP save keeps CAI_FACTION_MANAGER state 6.
    With state 6 the game may still run settlement construction, but military
    and character AI stays inactive. Native AI factions use 7.
    """
    cai = model.child("CAI_INTERFACE")
    manager = cai.child("CAI_FACTION_MANAGER_MANAGER") if cai is not None else None
    if manager is None:
        return 0
    block = next((c for c in manager.children if isinstance(c, RecordBlock)), None)
    if block is None:
        return 0
    changed = 0
    for key in keys:
        idx = index_by_key.get(key)
        if idx is None or idx < 0 or idx >= len(block.entries):
            continue
        entry = block.entries[idx]
        rec = next((c for c in entry.children
                    if isinstance(c, Record) and c.name == "CAI_FACTION_MANAGER"), None)
        if rec is None:
            continue
        vals = [c for c in rec.children if isinstance(c, Value)]
        if len(vals) > 1 and vals[1].value == 6:
            vals[1].value = 7
            changed += 1
    return changed


def convert(mp_path, keep, out_path, save_name):
    s = SaveFile(mp_path)
    drop_key = None

    # --- 1) campaign body: switch all OTHER players' factions to AI ---------
    hdr_in = s.inner.root.child("SAVE_GAME_HEADER_MULTIPLAYER")
    n_players = player_count(hdr_in)
    keep_key = player_block(hdr_in, keep)[1]
    drop_keys = [player_block(hdr_in, i)[1] for i in range(n_players)
                 if i != keep]
    rows = tables.factions(s)
    facs = {f["key"]: f["record"] for f in rows}
    index_by_key = {f["key"]: f["index"] for f in rows}
    portrait_path = faction_portrait(keep_key, facs[keep_key])

    # --- 1a) setup block: exactly one human + normalise difficulty ---------
    # The MP save stores each player's difficulty twice:
    #   CAMPAIGN_SETUP/CAMPAIGN_PLAYERS_SETUP/<entry>/CAMPAIGN_PLAYER_SETUP_INGAME_MODIFIABLES
    #   FACTION/CAMPAIGN_PLAYER_SETUP/CAMPAIGN_PLAYER_SETUP_INGAME_MODIFIABLES
    # Vector = [campaign_difficulty, battle_difficulty, slot2_battle_difficulty, bool, battle_multiplier].
    # Native SP writes the SAME vector to every faction, with slot2 == battle_difficulty.
    env = s.inner.root.child("CAMPAIGN_ENV")
    cs = env.child("CAMPAIGN_SETUP")
    ps_root = cs.child("CAMPAIGN_PLAYERS_SETUP")
    ps_block = next(c for c in ps_root.children if isinstance(c, RecordBlock))

    def entry_key(entry):
        for c in entry.children:
            if isinstance(c, Value) and c.type_name == "ascii" and str(c.value).startswith("wh"):
                return str(c.value)
        return None

    def entry_human(entry):
        return next((c for c in entry.children
                     if isinstance(c, Value) and c.type_name == "ascii"
                     and str(c.value) in HUMAN_STATES), None)

    def entry_mods(entry):
        return next((c for c in entry.children
                     if isinstance(c, Record) and c.name == "CAMPAIGN_PLAYER_SETUP_INGAME_MODIFIABLES"), None)

    keep_entry = next(e for e in ps_block.entries if entry_key(e) == keep_key)
    keep_mods = entry_mods(keep_entry)
    if keep_mods is None:
        raise RuntimeError("kept player difficulty vector not found")
    kv = [c.value for c in keep_mods.children if isinstance(c, Value)]
    campaign_diff, battle_diff, slot2, _flag, battle_mult = kv[:5]
    desired = [campaign_diff, battle_diff, battle_diff, False, battle_mult]

    # setup block entries (used by the load/setup screen)
    for e in ps_block.entries:
        key = entry_key(e)
        hn = entry_human(e)
        if hn is not None:
            hn.value = "FULL_HUMAN" if key == keep_key else "NON_HUMAN"
        em = entry_mods(e)
        if em is not None:
            for node, val in zip([c for c in em.children if isinstance(c, Value)], desired):
                if node.value != val:
                    node.value = val

    # runtime FACTION copy of the same record. The human flag exists TWICE:
    # inside FACTION/CAMPAIGN_PLAYER_SETUP and as a direct child of FACTION.
    # Switching only one leaves the faction in a "third state" (stuck end turn).
    for key, rec in facs.items():
        is_keep = key == keep_key
        ps = rec.child("CAMPAIGN_PLAYER_SETUP")
        for node in (ps, rec):
            if node is None:
                continue
            hn = entry_human(node)
            if hn is not None:
                hn.value = "FULL_HUMAN" if is_keep else "NON_HUMAN"
        if ps is None:
            continue
        em = entry_mods(ps)
        if em is not None:
            for node, val in zip([c for c in em.children if isinstance(c, Value)], desired):
                if node.value != val:
                    node.value = val

    # CAMPAIGN_SETUP summary (native SP: c9 == c10 == battle; c12 == battle multiplier)
    if cs.children[8].value != campaign_diff:
        cs.children[8].value = campaign_diff
    if cs.children[9].value != battle_diff:
        cs.children[9].value = battle_diff
    if cs.children[10].value != battle_diff:
        cs.children[10].value = battle_diff
    if cs.children[12].value != battle_mult:
        cs.children[12].value = battle_mult

    # CAMPAIGN_ENV campaign-difficulty string (0 easy .. 4 legendary)
    diff_names = {0: "EASY", 1: "NORMAL", 2: "HARD", 3: "VERY_HARD", 4: "LEGENDARY"}
    new_diff_name = diff_names.get(int(campaign_diff))
    if new_diff_name:
        for c in env.children:
            if isinstance(c, Value) and c.type_name == "ascii" and str(c.value) in diff_names.values():
                if c.value != new_diff_name:
                    c.value = new_diff_name
                break

    # CAMPAIGN_SETUP_LOCAL: faction of the LOCAL player = the kept one
    env.child("CAMPAIGN_SETUP_LOCAL").children[0].value = keep_key

    # CAMPAIGN_SETUP_OPTIONS: režim kampaně MP_NORMAL -> SP_NORMAL.
    # Tohle je HLAVNÍ přepínač — s MP_* hra po načtení nahodí síťovou
    # vrstvu, nenajde klienty a kopne "Klient opustil hru".
    opts = env.child("CAMPAIGN_SETUP").child("CAMPAIGN_SETUP_OPTIONS")
    mode = opts.children[0]
    if str(mode.value).startswith("MP"):
        mode.value = "SP" + str(mode.value)[2:]
    if opts.children[4].type_name == "unk23" and opts.children[4].value:
        opts.children[4].value = 0              # v SP 0
    ing = opts.child("CAMPAIGN_SETUP_INGAME_MODIFIABLES")
    for idx in (5, 6, 9):                       # MP-only bool volby (SP: False)
        b = ing.children[idx]
        if isinstance(b, Value) and b.type_name == "bool" and b.value:
            b.value = False

    # --- 1c) turn control: jediný člověk --------------------------------
    # HUMAN_FACTIONS + lidská TURN_GROUP jinak drží OBA hráče a hra na
    # konci kola čeká na tah druhého "klienta" -> timeout -> kick.
    fac_ids = {f["key"]: f["id"] for f in tables.factions(s)}
    keep_id = fac_ids[keep_key]
    drop_ids = [fac_ids[k] for k in drop_keys]
    model = env.child("CAMPAIGN_MODEL")
    _enable_ai_managers(model, index_by_key, drop_keys)
    hf_arr = next(c for c in model.child("HUMAN_FACTIONS").children
                  if isinstance(c, ValueArray))
    _set_u32_array(hf_arr, [keep_id])
    # TURN_CONTROL = pole TURN_GROUP + u32 index aktuální skupiny; skupina = [pole id A, pole id B,
    # leader u32, byte 0x23, (pole id C)] (ověřeno v Warhammer3.exe). Lidskou skupinu poznáme podle
    # obsahu (obsahuje ponechanou frakci), ne podle typu pole — ten závisí jen na velikosti id.
    tc = model.child("WORLD").child("TURN_CONTROL")
    tg_blk = next(c for c in tc.children if isinstance(c, RecordBlock))
    groups = []
    for e in tg_blk.entries:
        arrs = [c for c in e.children if isinstance(c, ValueArray)]
        if arrs:
            groups.append((e, arrs[0], _u32_array_items(arrs[0])))
    human = [g for g in groups if keep_id in g[2]]
    if len(human) != 1:
        raise RuntimeError("TURN_CONTROL: expected exactly one turn group containing faction id %d, "
                           "found %d (groups: %s)" % (keep_id, len(human), [g[2] for g in groups]))
    e, head, _ = human[0]
    human_ids = [keep_id] + drop_ids
    _set_u32_array(head, [keep_id])
    # The human turn group can hold a second id array (e.g. [101]) describing
    # its human factions. Native SP has [keep_id] or []; never leave a demoted
    # player id in there.
    for arr in [c for c in e.children if isinstance(c, ValueArray)]:
        ids = _u32_array_items(arr)
        if any(d in ids for d in drop_ids):
            _set_u32_array(arr, [keep_id])
    for c in e.children:                    # leader id + unk23 jako v SP
        if isinstance(c, Value) and c.type_name == "u32":
            c.value = keep_id
            break
    for c in e.children:
        if isinstance(c, Value) and c.type_name == "unk23" and c.value:
            c.value = 0
            break

    # 3+ players (or players split across several turn groups): remove every
    # kept/demoted human id from ALL other groups first, then put the demoted
    # players into a pure-AI group. Otherwise a demoted player sitting in a
    # second human group keeps that group alive and the turn never advances.
    stripped = []
    for g, g_head, g_ids in groups:
        if g is e:
            continue
        stripped.append((g, g_head, g_ids))
        for arr in [c for c in g.children if isinstance(c, ValueArray)]:
            ids = _u32_array_items(arr)
            new_ids = [x for x in ids if x not in human_ids]
            if new_ids != ids:
                _set_u32_array(arr, new_ids)
    pure_ai = [g for g in stripped
               if not any(x in g[2] for x in human_ids)]
    candidates = pure_ai or stripped
    if not candidates:
        raise RuntimeError("TURN_CONTROL: no AI turn group found to move %s into" % drop_ids)
    e2, head2, ids2 = max(candidates, key=lambda g: len(g[2]))  # AI skupina
    cur = _u32_array_items(head2)
    _set_u32_array(head2, _turn_group_order(cur + drop_ids))
    # If the fallback picked a former human group, clear its human-type markers.
    for c in e2.children:
        if isinstance(c, Value) and c.type_name == "u32":
            c.value = cur[0] if cur else 0
            break
    for c in e2.children:
        if isinstance(c, Value) and c.type_name == "unk23" and c.value:
            c.value = 0
            break

    # ENV-level GAME_PERSISTENT_SESSION_ID: keep only the owner's identity
    u64_keep = player_block(hdr_in, keep)[4]
    env_gpsi = s.inner.root.child("CAMPAIGN_ENV").child("GAME_PERSISTENT_SESSION_ID")
    if PROFILE:
        env_gpsi.children[0].value = PROFILE
    arr = next(c for c in env_gpsi.children if isinstance(c, ValueArray))
    arr._new = struct.pack("<Q", u64_keep)
    arr.mark_dirty()

    # multiplayer flag in CAMPAIGN_MODEL (child 14: True in MP, False in SP)
    model = s.campaign_root.walk("CAMPAIGN_ENV", "CAMPAIGN_MODEL")
    flag = model.children[14]
    assert isinstance(flag, Value) and flag.type_name == "bool" and flag.value
    flag.value = False

    # --- 2) inner file: rebuild root as CAMPAIGN_SAVE_GAME ------------------
    inner = s.inner
    build = inner.root.child("BUILD")
    env = inner.root.child("CAMPAIGN_ENV")
    parts = [copy_node(inner, build),
             build_sp_header(inner, hdr_in, keep, save_name, portrait_path),
             inner._serialize(env)]                    # env is dirty (AI flag)
    content = b"".join(parts)
    root_idx = name_idx(inner, "CAMPAIGN_SAVE_GAME")
    body = (bytes([0x80]) + struct.pack("<H", root_idx)
            + bytes([inner.root.version]) + write_varint(len(content))
            + content)
    inner_bytes = esf_file_bytes(inner, body)

    # --- 3) compress + rebuild outer ----------------------------------------
    comp = lzma.compress(inner_bytes, format=lzma.FORMAT_ALONE,
                         filters=LZMA_FILTER)
    props, stream = comp[:5], comp[13:]
    outer = s.outer
    hdr_out = outer.root.child("SAVE_GAME_HEADER_MULTIPLAYER")
    info_content = (enc_u32(len(inner_bytes))
                    + b"\x46" + write_varint(5) + props)
    info_bytes = rec_header(name_idx(outer, "COMPRESSED_DATA_INFO"), 0,
                            len(info_content)) + info_content
    cd_content = (b"\x46" + write_varint(len(stream)) + stream + info_bytes)
    cd_bytes = rec_header(name_idx(outer, "COMPRESSED_DATA"), 0,
                          len(cd_content)) + cd_content
    parts = [copy_node(outer, outer.root.child("BUILD")),
             build_sp_header(outer, hdr_out, keep, save_name, portrait_path),
             cd_bytes]
    content = b"".join(parts)
    root_idx = name_idx(outer, "CAMPAIGN_SAVE_GAME")
    body = (bytes([0x80]) + struct.pack("<H", root_idx)
            + bytes([outer.root.version]) + write_varint(len(content))
            + content)
    with open(out_path, "wb") as f:
        f.write(esf_file_bytes(outer, body))
    return keep_key, drop_keys


if __name__ == "__main__":
    mp, keep, out, name = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    if len(sys.argv) > 5:
        PROFILE = sys.argv[5]
    keep_key, drop_keys = convert(mp, keep, out, name)
    print("kept %s (human), demoted %s -> %s" % (keep_key, drop_keys, out))
    # verify
    v = SaveFile(out)
    hdr = v.outer.root.child("SAVE_GAME_HEADER")
    env = v.campaign_root.child("CAMPAIGN_ENV")
    print("verify: root=%s, mp=%s, faction=%s, local=%s" % (
        v.outer.root.name, v.is_multiplayer, hdr.children[0].value,
        env.child("CAMPAIGN_SETUP_LOCAL").children[0].value))
    facs = {f["key"]: f["record"] for f in tables.factions(v)}
    get = lambda r: next((str(c.value) for c in r.children
                          if isinstance(c, Value) and c.type_name == "ascii"
                          and str(c.value) in HUMAN_STATES), "?")
    for key in [keep_key] + drop_keys:
        print("verify: %s = %s" % (
            key, get(facs[key].child("CAMPAIGN_PLAYER_SETUP"))))
