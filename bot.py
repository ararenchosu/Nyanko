import discord
from discord import app_commands, ui, Embed, Color, ButtonStyle
from discord.ext import commands
import os
import json
import logging
from datetime import datetime, timedelta, timezone

# ======================================================
# ✅ 設定
# ======================================================
ADMIN_IDS = [1256574550901133377]  # ← 自分のDiscord ID
PAYPAY_DATA_FILE = "paypay_data.json"
ORDER_LOG_FILE = "order_log.json"
SETTINGS_FILE = "settings.json"
PRICE_FILE = "price_overrides.json"
PAYPAY_AVAILABLE = False
JST = timezone(timedelta(hours=9))

CLONE_PRICE_DEFAULT    = 500
FULL_EDIT_PRICE_DEFAULT = 300
RECOVERY_PRICE_DEFAULT  = 300
CHARA_UNLOCK_PRICE_DEFAULT = 100
CHARA_LVMAX_PRICE_DEFAULT  = 150
CHARA_FORM_PRICE_DEFAULT   = 100

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("bcsfe_bot")

# ======================================================
# ✅ アイテム価格設定
# ======================================================
ITEM_CONFIG = {
    "catfood_50000":        {"label": "ネコ缶 50,000個",           "price": 100},
    "xp_max":               {"label": "XP 9999万",                 "price": 100},
    "np_max":               {"label": "にゃんこポイント 9999",      "price": 100},
    "nyan_ticket_999":      {"label": "にゃんこチケット 999枚",     "price": 150},
    "rare_tickets_999":     {"label": "レアチケット 999枚",        "price": 200},
    "platinum_29":          {"label": "プラチナチケット +29枚",    "price": 300},
    "legend_29":            {"label": "レジェンドチケット +29枚",   "price": 400},
    "platinum_shard_90":    {"label": "プラチナのかけら +90個",    "price": 200},
    "leadership_999":       {"label": "統率力 999",                "price": 100},
    "battle_items_999":      {"label": "アイテム各999個",            "price": 150},
    "matatabi_998":          {"label": "ネコみかん 998個",           "price": 150},
    "cats_eye_999":          {"label": "ネコのめ 999個",            "price": 150},
    "nekovitan_999":         {"label": "ネコビタン 999個",           "price": 150},
    "castle_parts_999":      {"label": "城素材各999個",              "price": 200},
    "event_ticket_999":      {"label": "イベントチケット各999",      "price": 200},
    "honnou_99":             {"label": "本能玉 全属性Lv99",          "price": 300},
    "dungeon_medal_99":      {"label": "ダンジョンメダル 99枚",      "price": 150},
    "main_clear":            {"label": "第1章～第3章 全クリア",       "price": 300},
    "zombie_clear":          {"label": "ゾンビ襲来 全クリア",         "price": 200},
    "old_legend_clear":      {"label": "旧レジェンド 全クリア",       "price": 300},
    "true_legend_clear":     {"label": "真レジェンド 全クリア",       "price": 500},
    "zero_legend_clear":     {"label": "零レジェンド 全クリア",       "price": 500},
    "makai_clear":           {"label": "魔界編 全クリア",             "price": 300},
    "event_clear":           {"label": "イベントステージ全クリア",    "price": 400},
    "all_char_unlock":       {"label": "全キャラ開放",               "price": 500},
    "error_char_delete":     {"label": "エラーキャラ削除",           "price": 0},
    "all_char_lv_max":       {"label": "所持キャラ全員LvMAX",         "price": 500},
    "all_char_max_form":     {"label": "所持キャラ最高形態",          "price": 500},
    "all_honnou_max":        {"label": "全キャラ本能解放LvMAX",       "price": 800},
    "telop_delete":          {"label": "開放テロップ削除",           "price": 0},
    "slot_max":              {"label": "編成スロット数最大拡張",     "price": 50},
    "medal_all":             {"label": "にゃんこメダル全開放",       "price": 100},
    "enemy_book_all":        {"label": "敵キャラ図鑑全開放",         "price": 100},
    "user_rank_all":         {"label": "ユーザーランク報酬全受取",   "price": 50},
    "playtime_max":          {"label": "プレイ時間カンスト",         "price": 200},
    "gold_pass":             {"label": "ゴールド会員化",             "price": 200},
    "facility_max":          {"label": "施設LvMAX",                 "price": 100},
    "gamatoto_max":          {"label": "ガマトトLvMAX",              "price": 200},
    "gamatoto_legend":       {"label": "ガマトト助手全員レジェンド", "price": 200},
    "ad_free":               {"label": "広告非表示（β）",            "price": 50},
    "ototo_max":             {"label": "オトート全城強化LvMAX",      "price": 200},
    "shrine_max":            {"label": "にゃんこ神社LvMAX",         "price": 100},
}

# =====================
# データ管理
# =====================
def load_paypay_data() -> dict:
    if os.path.exists(PAYPAY_DATA_FILE):
        try:
            with open(PAYPAY_DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def save_paypay_data(data: dict):
    with open(PAYPAY_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_order_log() -> list:
    if os.path.exists(ORDER_LOG_FILE):
        try:
            with open(ORDER_LOG_FILE, "r", encoding="utf-8") as f:
                log = json.load(f)
        except json.JSONDecodeError:
            return []
    else:
        return []
    cutoff = datetime.now() - timedelta(days=1)
    log = [e for e in log if datetime.fromisoformat(e["timestamp"]) > cutoff]
    return log

def log_order(user_id: int, username: str, items: list, amount: int, status: str):
    log = load_order_log()
    log.append({
        "timestamp": datetime.now().isoformat(),
        "user_id": str(user_id),
        "username": username,
        "items": items,
        "amount": amount,
        "status": status,
    })
    with open(ORDER_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)
    logger.info(f"[ORDER] {username}({user_id}) {items} {amount}円 [{status}]")

# =====================
# サーバー別設定管理
# =====================
def _load_all_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def _save_all_settings(data: dict):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_settings(guild_id: int) -> dict:
    return _load_all_settings().get(str(guild_id), {})

def save_settings(guild_id: int, data: dict):
    all_s = _load_all_settings()
    all_s[str(guild_id)] = data
    _save_all_settings(all_s)

# =====================
# 値段オーバーライド
# =====================
def _load_all_price_overrides() -> dict:
    if os.path.exists(PRICE_FILE):
        try:
            with open(PRICE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {}
    return {}

def _save_all_price_overrides(data: dict):
    with open(PRICE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def load_price_overrides(guild_id: int) -> dict:
    return _load_all_price_overrides().get(str(guild_id), {})

def save_price_overrides(guild_id: int, data: dict):
    all_p = _load_all_price_overrides()
    all_p[str(guild_id)] = data
    _save_all_price_overrides(all_p)

def get_price(key: str, guild_id: int) -> int:
    ov = load_price_overrides(guild_id)
    default = ITEM_CONFIG[key]["price"] if key in ITEM_CONFIG else 50
    return ov.get(key, default)

def get_special_price(key: str, default: int, guild_id: int) -> int:
    ov = load_price_overrides(guild_id)
    return ov.get(key, default)

def get_jisseki_channel_id(guild_id: int):
    settings = load_settings(guild_id)
    val = settings.get("jisseki_channel_id")
    return int(val) if val else None

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# =====================
# bcsfe セーブ編集処理
# =====================
_valid_cat_max_cache: int | None = None
def _get_valid_cat_max() -> int:
    HARDCODED_MAX = 674
    try:
        import urllib.request, re
        url = "https://battlecats-db.com/unit/"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8", errors="ignore")
        ids = [int(m) for m in re.findall(r'/unit/(\d+)\.html', html)]
        if ids:
            max_id = max(ids) + 1
            if 500 <= max_id <= 2000:
                _valid_cat_max_cache = max_id
                logger.info(f"battlecats-db 有効キャラID最大値: {max_id}")
                return max_id
    except Exception as e:
        logger.warning(f"battlecats-db取得失敗、fallback={HARDCODED_MAX}: {e}")
    _valid_cat_max_cache = HARDCODED_MAX
    return HARDCODED_MAX

def _sv(save_file, attr: str, value: int):
    try:
        obj = getattr(save_file, attr)
        try:
            obj.value = value
            return
        except (AttributeError, TypeError):
            pass
        try:
            setattr(save_file, attr, value)
            return
        except (TypeError, AttributeError):
            pass
    except Exception as e:
        logger.warning(f"_sv({attr}, {value}) 失敗: {e}")

def _sv_list(save_file, attr: str, value: int):
    try:
        lst = getattr(save_file, attr)
        for i in range(len(lst)):
            try:
                lst[i].value = value
            except (AttributeError, TypeError):
                try:
                    lst[i] = value
                except (TypeError, AttributeError):
                    pass
    except Exception as e:
        logger.warning(f"_sv_list({attr}, {value}) 失敗: {e}")

def _auto_run(func, save_file, inputs: list):
    import sys, io
    fallback = (
        ["1", "10", "y", "999", "4", "0", "1", "10", "y", "999", "4", "0"] * 20
    )
    responses = list(inputs) + fallback
    fake_stdin = io.StringIO("\n".join(str(r) for r in responses) + "\n")
    old_stdin, old_stdout, old_stderr = sys.stdin, sys.stdout, sys.stderr
    sys.stdin  = fake_stdin
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()
    try:
        func(save_file)
    except (EOFError, StopIteration, SystemExit):
        pass
    except Exception as e:
        sys.stdout = old_stdout
        sys.stderr = old_stderr
        logger.warning(f"[_auto_run] エラー: {e}")
        return
    finally:
        sys.stdin  = old_stdin
        sys.stdout = old_stdout
        sys.stderr = old_stderr

def _clear_chapters(sf, chapters, name, logger):
    try:
        if hasattr(chapters, "clear_stage"):
            total_maps = len(chapters.chapters)
            cleared = 0
            for mid in range(total_maps):
                try: total_stars = chapters.get_total_stars(mid)
                except: total_stars = 1
                for star in range(total_stars):
                    try: total_stages = chapters.get_total_stages(mid, star)
                    except: total_stages = 48
                    try: chapters.set_total_stages(mid, star, total_stages)
                    except: pass
                    for stage in range(total_stages):
                        try: chapters.clear_stage(mid, star, stage, 1, True)
                        except: pass
                cleared += 1
            logger.info(f"{name}: {cleared}ch 完了")
            return cleared
        if hasattr(chapters, "stages") and not hasattr(chapters, "chapters"):
            cleared = 0
            try:
                ch_list = chapters.chapters
            except:
                ch_list = []
            for ch in ch_list:
                try:
                    stages = ch.stages
                    for st in stages:
                        try: st.clear_amount = 1
                        except: pass
                    cleared += 1
                except: pass
            logger.info(f"{name}: {cleared}ch 完了")
            return cleared
        logger.warning(f"{name}: 未知の型")
        return 0
    except Exception as e:
        logger.warning(f"{name} 失敗: {e}")
        return 0

def apply_chara_edits(save_file, service_label: str, chara_ids_str: str) -> list:
    try:
        raw_ids = [int(x.strip()) for x in chara_ids_str.replace("、", ",").split(",") if x.strip().isdigit()]
        ids = [i - 1 for i in raw_ids]
    except Exception:
        ids = []
    if not ids:
        return []
    applied = []
    for cat_id, display_id in zip(ids, raw_ids):
        try:
            cat = None
            for candidate in save_file.cats.get_all_cats():
                try: cid = int(candidate.id) if not hasattr(candidate.id, 'value') else int(candidate.id.value)
                except: continue
                if cid == cat_id:
                    cat = candidate
                    break
            if cat is None:
                logger.warning(f"[apply_chara_edits] 表示ID:{display_id} キャラが見つからない")
                continue
            if "開放" in service_label:
                cat.unlock(save_file)
            elif "LvMAX" in service_label:
                try:
                    from bcsfe import core as _c
                    pu = _c.PowerUpHelper(cat, save_file)
                    cat.upgrade.base = pu.get_max_possible_base() - 1
                    cat.upgrade.plus = pu.get_max_possible_plus()
                except:
                    cat.upgrade.base = 29
                    cat.upgrade.plus = 0
            elif "形態" in service_label:
                for fattr in ("current_form", "form", "cat_form", "evolve"):
                    try:
                        obj = getattr(cat, fattr, None)
                        if obj is None: continue
                        try: obj.value = 2
                        except: setattr(cat, fattr, 2)
                        break
                    except: pass
            applied.append(f"{service_label}[ID:{display_id}]")
            logger.info(f"[apply_chara_edits] ID:{display_id} 完了")
        except Exception as e:
            logger.warning(f"[apply_chara_edits] ID:{display_id} 失敗: {e}")
    return applied

def apply_edits(save_file, item_keys: list) -> list:
    applied = []
    for key in item_keys:
        try:
            sf = save_file
            def sv(attr, val):
                try:
                    obj = getattr(sf, attr)
                    try: obj.value = val; return
                    except: pass
                    try: setattr(sf, attr, val); return
                    except: pass
                except Exception as e:
                    logger.warning(f"sv({attr},{val}): {e}")
            def sv_list_multi(attrs, val):
                for attr in attrs:
                    try:
                        lst = getattr(sf, attr, None)
                        if lst is None: continue
                        if hasattr(lst, 'items'): lst = lst.items
                        elif hasattr(lst, 'data'): lst = lst.data
                        for i in range(len(lst)):
                            try: lst[i].value = val
                            except:
                                try: lst[i] = val
                                except: pass
                        return True
                    except: pass
                return False

            if key == "catfood_50000":
                try: sv("catfood", min(int(sf.catfood) + 50000, 9999999))
                except: sv("catfood", min(int(sf.catfood.value) + 50000, 9999999))
            elif key == "xp_max": sv("xp", 99999999)
            elif key == "np_max": sv("np", 9999)
            elif key == "nyan_ticket_999": sv("normal_tickets", 999)
            elif key == "rare_tickets_999": sv("rare_tickets", 999)
            elif key == "platinum_29":
                for attr in ("platinum_tickets", "platinum_ticket"):
                    try:
                        obj = getattr(sf, attr, None)
                        if obj is None: continue
                        try: cur = int(obj.value)
                        except: cur = int(obj)
                        try: obj.value = cur + 29
                        except: setattr(sf, attr, cur + 29)
                        break
                    except: pass
            elif key == "legend_29":
                for attr in ("legend_tickets", "legend_ticket"):
                    try:
                        obj = getattr(sf, attr, None)
                        if obj is None: continue
                        try: cur = int(obj.value)
                        except: cur = int(obj)
                        try: obj.value = cur + 29
                        except: setattr(sf, attr, cur + 29)
                        break
                    except: pass
            elif key == "platinum_shard_90":
                for attr in ("platinum_shards", "platinum_shard"):
                    try:
                        obj = getattr(sf, attr, None)
                        if obj is None: continue
                        try: cur = int(obj.value)
                        except: cur = int(obj)
                        try: obj.value = cur + 90
                        except: setattr(sf, attr, cur + 90)
                        break
                    except: pass
            elif key == "leadership_999": sv("leadership", 999)
            elif key == "battle_items_999":
                try:
                    for item in sf.battle_items.items:
                        try: item.amount = 999
                        except:
                            try: item.amount.value = 999
                            except: pass
                except Exception as e:
                    logger.warning(f"battle_items_999 失敗: {e}")
            elif key == "matatabi_998": sv_list_multi(["catfruit", "cat_fruit"], 998)
            elif key == "cats_eye_999":
                try:
                    for i in range(len(sf.catseyes)): sf.catseyes[i] = 999
                except Exception as e: logger.warning(f"cats_eye_999 失敗: {e}")
            elif key == "nekovitan_999":
                try:
                    for i in range(len(sf.catamins)): sf.catamins[i] = 999
                except Exception as e: logger.warning(f"nekovitan_999 失敗: {e}")
            elif key == "castle_parts_999":
                try:
                    for m in sf.ototo.base_materials.materials:
                        try: m.amount = 999
                        except:
                            try: m.amount.value = 999
                            except: pass
                except Exception as e: logger.warning(f"castle_parts_999 失敗: {e}")
            elif key == "event_ticket_999":
                try:
                    for _attr in ("event_capsules", "lucky_tickets", "event_capsules_2"):
                        try:
                            _lst = getattr(sf, _attr, None)
                            if _lst is None: continue
                            for _i in range(len(_lst)):
                                try: _lst[_i] = 999
                                except:
                                    try: _lst[_i].value = 999
                                    except: pass
                        except: pass
                except Exception as e: logger.warning(f"event_ticket_999 失敗: {e}")
            elif key == "honnou_99":
                try:
                    _orbs = sf.talent_orbs.orbs
                    for _orb in _orbs:
                        try: _orb.value = 99
                        except: pass
                except Exception as e: logger.warning(f"honnou_99 失敗: {e}")
            elif key == "dungeon_medal_99":
                try:
                    for i in range(len(sf.labyrinth_medals)): sf.labyrinth_medals[i] = 99
                except Exception as e: logger.warning(f"dungeon_medal_99 失敗: {e}")
            elif key == "main_clear":
                try:
                    from bcsfe import core as _c
                    _auto_run(_c.game.map.story.StoryChapters.clear_story, sf, ["10"])
                except Exception as _e: logger.warning(f"main_clear 失敗: {_e}")
            elif key == "zombie_clear":
                try:
                    from bcsfe import core as _c
                    _auto_run(_c.game.map.outbreaks.Outbreak, sf, [])
                except Exception as _e: logger.warning(f"zombie_clear 失敗: {_e}")
            elif key == "old_legend_clear":
                try:
                    for _tl_attr in ("gauntlets", "collab_gauntlets"):
                        _ga = getattr(sf, _tl_attr)
                        for _cs in _ga.chapters:
                            for _ch in _cs.chapters:
                                _ch.chapter_unlock_state = 3
                                if _ch.stages:
                                    for _st in _ch.stages: _st.clear_times = 1
                                    _ch.clear_progress = len(_ch.stages)
                except Exception as _e: logger.warning(f"old_legend_clear 失敗: {_e}")
            elif key == "true_legend_clear":
                _clear_chapters(sf, sf.uncanny.chapters, "true_legend_clear", logger)
            elif key == "zero_legend_clear":
                _clear_chapters(sf, sf.zero_legends, "zero_legend_clear", logger)
            elif key == "makai_clear":
                _clear_chapters(sf, sf.aku, "makai_clear", logger)
            elif key == "event_clear":
                try:
                    from bcsfe import core as _c
                    cleared = []
                    for _fn, _lbl in [
                        (_c.game.map.event.EventChapters.edit_sol_chapters,   "sol"),
                        (_c.game.map.event.EventChapters.edit_event_chapters,  "event"),
                        (_c.game.map.event.EventChapters.edit_collab_chapters, "collab"),
                    ]:
                        try: _auto_run(_fn, sf, ["10"]); cleared.append(_lbl)
                        except: pass
                except Exception as _e: logger.warning(f"event_clear 失敗: {_e}")
            elif key == "all_char_unlock":
                try:
                    ERROR_IDS = {155,182,285,320,339,353,432,433,465,492,497,498,499,500,673,740,741,742,743,744,745,788}
                    unlocked = guide_set = 0
                    try: _all = list(sf.cats.get_all_cats())
                    except Exception: _all = list(sf.cats.cats)
                    for _cat in _all:
                        try: _cid = int(_cat.id.value) if hasattr(_cat.id,"value") else int(_cat.id)
                        except: continue
                        if _cid < 0 or _cid in ERROR_IDS: continue
                        try: _cat.unlock(sf); unlocked +=1
                        except: pass
                        for _gattr in ("catguide_collected","guide_collected"):
                            try: setattr(_cat, _gattr, True); guide_set +=1; break
                            except: pass
                    logger.info(f"all_char_unlock: {unlocked}体開放 / 図鑑{guide_set}体")
                except Exception as e: logger.warning(f"all_char_unlock 失敗: {e}")
            elif key == "error_char_delete":
                try:
                    FORCE_DELETE = {155,182,285,320,339,353,432,433,465,492,497,498,499,500,673,740,741,742,743,744,745,788}
                    cat_list = list(sf.cats.cats)
                    removed = 0
                    for _cat in cat_list:
                        try: _cid = int(_cat.id) if not hasattr(_cat.id,"value") else int(_cat.id.value)
                        except: continue
                        if _cid not in FORCE_DELETE: continue
                        try: _cat.remove(reset=True, save_file=sf)
                        except:
                            try: setattr(_cat, "unlocked", False)
                            except: pass
                        removed +=1
                    logger.info(f"error_char_delete: {removed}体")
                except Exception as e: logger.warning(f"error_char_delete 失敗: {e}")
            elif key == "all_char_lv_max":
                try:
                    from bcsfe import core as _c
                    for cat in sf.cats.cats:
                        try:
                            pu = _c.PowerUpHelper(cat, sf)
                            cat.upgrade.base.value = pu.get_max_possible_base() - 1
                            cat.upgrade.plus.value = pu.get_max_possible_plus()
                        except: pass
                except Exception as e: logger.warning(f"all_char_lv_max 失敗: {e}")
            elif key == "all_char_max_form":
                try:
                    ERROR_IDS = {155,182,285,320,339,353,432,433,465,492,497,498,499,500,673,740,741,742,743,744,745,788}
                    for _cat in sf.cats.cats:
                        try:
                            _cid = int(_cat.id.value) if hasattr(_cat.id,"value") else int(_cat.id)
                            if _cid <0 or _cid in ERROR_IDS: continue
                            for _fa in ("current_form","form","cat_form","evolve"):
                                try:
                                    _obj = getattr(_cat, _fa, None)
                                    if _obj is None: continue
                                    try: _obj.value = 2
                                    except: setattr(_cat, _fa, 2)
                                    break
                                except: pass
                        except: pass
                except Exception as e: logger.warning(f"all_char_max_form 失敗: {e}")
            elif key == "all_honnou_max":
                try:
                    from bcsfe import core as _c
                    _td = sf.cats.read_talent_data(sf)
                    for _cat in sf.cats.cats:
                        try:
                            _data = _td.get_cat_talents(_cat)
                            if _data is None: continue
                            _, _maxlvs, _, _ids = _data
                            if not _ids: continue
                            for _ti, _tid in enumerate(_ids):
                                try:
                                    _t = _cat.get_talent_from_id(_tid)
                                    if _t: _t.level = _maxlvs[_ti]
                                except: pass
                        except: pass
                except Exception as e: logger.warning(f"all_honnou_max 失敗: {e}")
            elif key == "telop_delete":
                try:
                    from bcsfe import core as _c
                    _c.StoryChapters.clear_tutorial(sf)
                except Exception as e: logger.warning(f"telop_delete 失敗: {e}")
            elif key == "slot_max":
                try:
                    from bcsfe.cli.edits.basic_items import BasicItems as _BI
                    _auto_run(_BI.edit_unlocked_slots, sf, ["19"])
                except Exception as e: logger.warning(f"slot_max 失敗: {e}")
            elif key == "medal_all":
                try:
                    sf.medals.medal_data_1 = list(range(128))
                except Exception as e: logger.warning(f"medal_all 失敗: {e}")
            elif key == "enemy_book_all":
                try:
                    from bcsfe import core as _c
                    for _i in range(len(sf.enemy_guide)):
                        _c.Enemy(_i).unlock_enemy_guide(sf)
                except Exception as e: logger.warning(f"enemy_book_all 失敗: {e}")
            elif key == "user_rank_all":
                try:
                    try: sf.user_rank = 40000
                    except: sf.user_rank.value = 40000
                except: pass
                try:
                    for _r in sf.user_rank_rewards.rewards:
                        for _a in ("claimed","received","unlocked"):
                            try: setattr(_r, _a, True); break
                            except: pass
                except Exception as e: logger.warning(f"user_rank_all 失敗: {e}")
            elif key == "playtime_max":
                try: sf.play_time.value = 99999999
                except: pass
            elif key == "gold_pass":
                try:
                    from bcsfe import core as _c
                    _auto_run(sf.officer_pass.gold_pass.edit_gold_pass, sf, ["1"])
                except Exception as e: logger.warning(f"gold_pass 失敗: {e}")
            elif key == "facility_max":
                try:
                    try: sf.ototo.engineers.value = 10
                    except: pass
                    try:
                        for m in sf.ototo.base_materials.materials:
                            try: m.amount.value = 999
                            except: pass
                    except: pass
                    try:
                        for _cannon in sf.ototo.cannons.cannons:
                            try: _cannon.development.value = 999
                            except: pass
                    except: pass
                except Exception as e: logger.warning(f"facility_max 失敗: {e}")
            elif key == "gamatoto_max":
                try: sf.gamatoto.xp.value = 99999999
                except: pass
            elif key == "gamatoto_legend":
                try:
                    for _h in sf.gamatoto.helpers.helpers:
                        try: _h.id.value = 5
                        except: pass
                except Exception as e: logger.warning(f"gamatoto_legend 失敗: {e}")
            elif key == "ad_free":
                try: sf.ad_free.value = True
                except: pass
            elif key == "ototo_max":
                try:
                    for _cannon in sf.ototo.cannons.cannons:
                        try: _cannon.development.value = 999
                        except: pass
                except Exception as e: logger.warning(f"ototo_max 失敗: {e}")
            elif key == "shrine_max":
                try: sf.cat_shrine.level.value = 50
                except: pass

            applied.append(ITEM_CONFIG[key]["label"])
        except Exception as e:
            logger.warning(f"[apply_edits] {key} 適用失敗: {e}")
    return applied

def run_bcsfe_download(transfer_code: str, confirmation_code: str, cc_str: str):
    from bcsfe import core
    core.core_data.init_data()
    cc_map = {"jp": "jp", "en": "en", "tw": "tw", "kr": "kr"}
    cc = core.CountryCode(cc_map.get(cc_str.lower(), "jp"))
    gv = core.GameVersion(120200)
    server_handler, result = core.ServerHandler.from_codes(
        transfer_code.strip(),
        confirmation_code.strip(),
        cc,
        gv,
        print=False,
        save_backup=False,
    )
    if server_handler is None:
        if result is not None and result.response is not None:
            return None, f"ダウンロード失敗 (HTTP {result.response.status_code})"
        return None, "ダウンロード失敗（コードまたはネット接続を確認）"
    return server_handler, None

def run_bcsfe_download_clone(transfer_code: str, confirmation_code: str, cc_str: str):
    from bcsfe import core
    core.core_data.init_data()
    cc_map = {"jp": "jp", "en": "en", "tw": "tw", "kr": "kr"}
    cc = core.CountryCode(cc_map.get(cc_str.lower(), "jp"))
    gv = core.GameVersion(120200)
    server_handler, result = core.ServerHandler.from_codes(
        transfer_code.strip(),
        confirmation_code.strip(),
        cc,
        gv,
        print=False,
        save_backup=False,
    )
    if server_handler is None:
        if result is not None and result.response is not None:
            return None, f"ダウンロード失敗 (HTTP {result.response.status_code})"
        return None, "ダウンロード失敗（コードまたはネット接続を確認）"
    try:
        new_inquiry = core.Random.get_hex_string(32)
        save = server_handler.save_file
        for attr in ("inquiry_code", "inquiry", "nyanko_inquiry_code"):
            try:
                obj = getattr(save, attr, None)
                if obj is None: continue
                try: obj.value = new_inquiry
                except: setattr(save, attr, new_inquiry)
                break
            except Exception: pass
    except Exception as e:
        logger.warning(f"inquiry_code生成失敗: {e}")
    return server_handler, None

def run_bcsfe_upload(server_handler):
    return server_handler.get_codes(upload_managed_items=False)

# =====================
# 実績チャンネルに投稿
# =====================
async def post_jisseki(bot_instance, user: discord.User, items: list, amount: int, guild_id: int = 0):
    ch_id = get_jisseki_channel_id(guild_id)
    if ch_id is None:
        return
    ch = bot_instance.get_channel(ch_id)
    if ch is None:
        return
    now = datetime.now()
    timestamp_str = now.strftime("%Y/%m %H:%M")
    items_text = "\n".join(f"・{item}" for item in items)
    embed = Embed(title="代行実績", color=0xccff00)
    embed.add_field(name="依頼情報", value=f"依頼者: {user.mention}\n```利用金額: {amount}円```", inline=False)
    embed.add_field(name="代行内容", value=f"```{items_text}```", inline=False)
    embed.set_footer(text=f"24/h稼働中🔥 | {timestamp_str}")
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    await ch.send(embed=embed)

# =====================
# ✅ 共通処理
# =====================
async def confirm_and_process(interaction: discord.Interaction, t_code: str, a_code: str,
                               item_keys: list, label_list: list, total: int,
                               is_clone: bool = False, chara_ids: str = ""):
    await interaction.response.defer(ephemeral=True)
    await interaction.followup.send(
        embed=Embed(title="⏳ 処理中...", description="セーブデータを取得しています。しばらくお待ちください。", color=0xffaa00),
        ephemeral=True
    )
    log_order(interaction.user.id, str(interaction.user), label_list, total, "PAID_SKIP")
    import asyncio, functools
    loop = asyncio.get_event_loop()
    dl_func = run_bcsfe_download_clone if is_clone else run_bcsfe_download
    try:
        server_handler, err = await loop.run_in_executor(
            None, functools.partial(dl_func, t_code, a_code, "jp")
        )
        if server_handler is None:
            await interaction.followup.send(
                embed=Embed(title="❌ ダウンロード失敗",
                            description=f"{err}\n\n引き継ぎコード・認証番号を確認してください。",
                            color=0xff3333),
                ephemeral=True
            )
            log_order(interaction.user.id, str(interaction.user), label_list, 0, f"DL_FAIL:{err}")
            return
        if chara_ids:
            applied = apply_chara_edits(server_handler.save_file, label_list[0], chara_ids)
        elif item_keys:
            applied = apply_edits(server_handler.save_file, item_keys)
        else:
            applied = label_list
        codes = await loop.run_in_executor(None, functools.partial(run_bcsfe_upload, server_handler))
        if codes is None:
            await interaction.followup.send(
                embed=Embed(title="❌ アップロード失敗", description="サーバーへのアップロードに失敗しました。", color=0xff3333),
                ephemeral=True
            )
            log_order(interaction.user.id, str(interaction.user), label_list, 0, "UL_FAIL")
            return
        transfer_code, confirmation_code = codes
        items_text = "\n".join(f"✅ {i}" for i in applied) or "なし"
        embed = Embed(title="🎉 代行完了", description="以下の新しい引き継ぎコードでゲームにログインしてください。", color=0x00cc88)
        embed.add_field(name="適用内容", value=items_text, inline=False)
        embed.add_field(name="新しい引き継ぎ情報",
                        value=f"引き継ぎコード: `{transfer_code}`\n認証番号: `{confirmation_code}`",
                        inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)
        try:
            await interaction.user.send(embed=embed)
        except discord.Forbidden:
            pass
        log_order(interaction.user.id, str(interaction.user), label_list, total, "SUCCESS")
        await post_jisseki(interaction.client, interaction.user, applied, total, interaction.guild_id)
    except ImportError:
        await interaction.followup.send("bcsfe がインストールされていません。管理者にお問い合わせください。", ephemeral=True)
    except Exception as e:
        logger.error(f"代行処理エラー: {e}", exc_info=True)
        await interaction.followup.send(
            embed=Embed(title="❌ 予期しないエラー", description=f"管理者にお問い合わせください。\n```{str(e)[:300]}```", color=0xff3333),
            ephemeral=True
        )
        log_order(interaction.user.id, str(interaction.user), label_list, total, f"ERROR:{e}")

# =====================
# ✅ 入力フォーム
# =====================
class ServiceModal(ui.Modal, title="引き継ぎ情報入力"):
    t_code = ui.TextInput(label="引き継ぎコード", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)
    def __init__(self, service_label: str, total: int, item_keys: list = None, is_clone: bool = False):
        super().__init__(title=f"{service_label} 情報入力", timeout=300)
        self.service_label = service_label
        self.total = total
        self.item_keys = item_keys or []
        self.is_clone = is_clone
    async def on_submit(self, interaction: discord.Interaction):
        await confirm_and_process(interaction, self.t_code.value, self.a_code.value,
                                  self.item_keys, [self.service_label], self.total,
                                  is_clone=self.is_clone)

class CharaModal(ui.Modal, title="指定キャラ 情報入力"):
    t_code = ui.TextInput(label="引き継ぎコード", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)
    chara_ids = ui.TextInput(label="キャラクターID（カンマ区切り）", placeholder="例: 1,5,12", required=True, style=discord.TextStyle.short)
    def __init__(self, service_label: str, total: int):
        super().__init__(title=f"{service_label} 情報入力", timeout=300)
        self.service_label = service_label
        self.total = total
    async def on_submit(self, interaction: discord.Interaction):
        await confirm_and_process(interaction, self.t_code.value, self.a_code.value,
                                  [], [f"{self.service_label}[ID:{self.chara_ids.value}]"],
                                  self.total, chara_ids=self.chara_ids.value)

class PurchaseModal(ui.Modal, title="購入情報入力"):
    t_code = ui.TextInput(label="引き継ぎコード", placeholder="例: ABCDEF1234567890", required=True, style=discord.TextStyle.short)
    a_code = ui.TextInput(label="認証番号", placeholder="例: 1234", required=True, max_length=10, style=discord.TextStyle.short)
    def __init__(self, items: list, total: int):
        super().__init__(timeout=300)
        self.items = items
        self.total = total
    async def on_submit(self, interaction: discord.Interaction):
        await confirm_and_process(interaction, self.t_code.value, self.a_code.value,
                                  self.items, self.items, self.total)

# =====================
# ✅ パネルUI
# =====================
class ClonePanelView(ui.View):
    def __init__(self, guild_id: int = 0):
        super().__init__(timeout=None)
        self.add_item(CloneSelectMenu(guild_id))

class CloneSelectMenu(ui.Select):
    def __init__(self, guild_id: int = 0):
        options = [
            discord.SelectOption(label="✅ アカウント複製", value="clone", description="データを丸ごと複製・新規ID発行", emoji="🔄"),
            discord.SelectOption(label="🎫 セーブデータ編集（単品）", value="edit_single", description="アイテム・ステータスを個別編集", emoji="✏️"),
            discord.SelectOption(label="📦 セット購入（お得）", value="edit_set", description="複数機能をまとめて適用", emoji="🎁"),
            discord.SelectOption(label="👤 キャラクター指定編集", value="edit_chara", description="開放/LvMAX/形態変更をID指定", emoji="🦊"),
            discord.SelectOption(label="🔧 管理者用メニュー", value="admin_menu", description="価格設定・実績チャンネル設定", emoji="⚙️"),
        ]
        super().__init__(
            custom_id="clone_service_select",
            placeholder="▼ サービス種別を選択してください",
            options=options,
            min_values=1,
            max_values=1
        )
        self.guild_id = guild_id

    async def callback(self, interaction: discord.Interaction):
        selected = self.values
        if selected[0] == "admin_menu":
            if not is_admin(interaction.user.id):
                await interaction.response.send_message("❌ 管理者専用メニューです。", ephemeral=True)
                return
            await interaction.response.send_message(
                embed=Embed(title="🔧 管理者メニュー", description="以下から選択してください。", color=0x9999ff),
                view=AdminMenuView(self.guild_id),
                ephemeral=True
            )
            return
        if selected[0] == "clone":

            price = get_special_price("clone", CLONE_PRICE_DEFAULT, self.guild_id)
            label = "✅ アカウント複製"
            await interaction.response.send_modal(
                ServiceModal(label, price, is_clone=True)
            )
            return
        if selected[0] == "edit_chara":
            price = get_special_price("chara_edit", CHARA_UNLOCK_PRICE_DEFAULT, self.guild_id)
            label = "👤 キャラクター編集"
            await interaction.response.send_modal(CharaModal(label, price))
            return
        if selected[0] == "edit_single":
            view = SingleItemView(self.guild_id)
            embed = Embed(title="🎫 単品編集", description="編集したい項目を選んでください。", color=0xffcc00)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return
        if selected[0] == "edit_set":
            view = SetItemView(self.guild_id)
            embed = Embed(title="📦 セット購入", description="まとめて適用するセットを選んでください。", color=0x00cc88)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

# =====================
# ✅ 単品編集ビュー
# =====================
class SingleItemSelect(ui.Select):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.item_keys = list(ITEM_CONFIG.keys())
        options = [
            discord.SelectOption(label=v["label"], value=k)
            for k, v in ITEM_CONFIG.items()
        ]
        super().__init__(
            custom_id="single_item_select",
            placeholder="編集する項目を選択（複数可）",
            min_values=1,
            max_values=min(8, len(options)),
            options=options
        )
    async def callback(self, interaction: discord.Interaction):
        items_selected = self.values
        total = sum(get_price(k, self.guild_id) for k in items_selected)
        labels = [ITEM_CONFIG[k]["label"] for k in items_selected]
        embed = Embed(title="✅ 選択内容確認", color=0xffcc00)
        embed.add_field(name="選択項目", value="\n".join(f"・{l}" for l in labels), inline=False)
        embed.add_field(name="合計金額", value=f"```{total}円```", inline=False)
        await interaction.response.edit_message(
            embed=embed,
            view=ConfirmPurchaseView(items_selected, labels, total)
        )

class SingleItemView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.add_item(SingleItemSelect(guild_id))

class ConfirmPurchaseView(ui.View):
    def __init__(self, item_keys: list, label_list: list, total: int):
        super().__init__(timeout=120)
        self.item_keys = item_keys
        self.label_list = label_list
        self.total = total

    @ui.Button(label="✅ 購入・編集実行", style=ButtonStyle.success, custom_id="confirm_purchase")
    async def confirm_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_modal(
            PurchaseModal(self.item_keys, self.total)
        )

    @ui.Button(label="❌ キャンセル", style=ButtonStyle.secondary, custom_id="cancel_purchase")
    async def cancel_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(
            embed=Embed(title="❌ キャンセル", description="購入をキャンセルしました。", color=0x888888),
            view=None
        )

# =====================
# ✅ セット購入ビュー
# =====================
class SetItemSelect(ui.Select):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        options = [
            discord.SelectOption(label="💰 資材MAXセット", value="set_money", description="ネコ缶・XP・チケット類 全MAX", emoji="💰"),
            discord.SelectOption(label="🗺️ ストーリー全開放セット", value="set_map", description="第1～3章/レジェンド/魔界 全クリア", emoji="🗺️"),
            discord.SelectOption(label="🦊 キャラ極みセット", value="set_char", description="全キャラ開放+LvMAX+最高形態+本能MAX", emoji="🦊"),
            discord.SelectOption(label="🏗️ 施設完備セット", value="set_facility", description="施設/ガマトト/神社 全MAX", emoji="🏗️"),
        ]
        super().__init__(
            custom_id="set_item_select",
            placeholder="セットを選択してください",
            options=options
        )
    async def callback(self, interaction: discord.Interaction):
        set_key = self.values[0]
        set_defs = {
            "set_money": {
                "items": ["catfood_50000","xp_max","np_max","nyan_ticket_999","rare_tickets_999","platinum_29","legend_29","platinum_shard_90","battle_items_999","matatabi_998","cats_eye_999","nekovitan_999","castle_parts_999","event_ticket_999"],
                "label": "💰 資材MAXセット"
            },
            "set_map": {
                "items": ["main_clear","zombie_clear","old_legend_clear","true_legend_clear","zero_legend_clear","makai_clear","event_clear"],
                "label": "🗺️ ストーリー全開放セット"
            },
            "set_char": {
                "items": ["all_char_unlock","all_char_lv_max","all_char_max_form","all_honnou_max"],
                "label": "🦊 キャラ極みセット"
            },
            "set_facility": {
                "items": ["facility_max","gamatoto_max","gamatoto_legend","ototo_max","shrine_max","medal_all","enemy_book_all","user_rank_all","playtime_max","gold_pass","ad_free","slot_max","telop_delete"],
                "label": "🏗️ 施設完備セット"
            },
        }
        definition = set_defs[set_key]
        total = sum(get_price(k, self.guild_id) for k in definition["items"])
        embed = Embed(title=definition["label"], color=0x00cc88)
        embed.add_field(name="含まれる機能", value="\n".join(f"・{ITEM_CONFIG[k]['label']}" for k in definition["items"]), inline=False)
        embed.add_field(name="合計金額", value=f"```{total}円```", inline=False)
        await interaction.response.edit_message(
            embed=embed,
            view=ConfirmPurchaseView(definition["items"], [definition["label"]], total)
        )

class SetItemView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.add_item(SetItemSelect(guild_id))

# =====================
# ✅ 管理者メニュー
# =====================
class AdminMenuView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    @ui.Button(label="💰 価格を変更", style=ButtonStyle.primary, custom_id="admin_price")
    async def price_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            embed=Embed(title="💰 価格設定", description="`/setprice 項目キー 金額` で変更\n例: `/setprice catfood_50000 150`", color=0x99ccff),
            ephemeral=True
        )

    @ui.Button(label="📝 実績チャンネル設定", style=ButtonStyle.primary, custom_id="admin_jisseki_ch")
    async def ch_btn(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.send_message(
            embed=Embed(title="📝 実績チャンネル設定", description="`/setjisseki チャンネルID` で設定\n例: `/setjisseki 1546928125231767633`", color=0x99ccff),
            ephemeral=True
        )

    @ui.Button(label="📋 全項目キー一覧", style=ButtonStyle.secondary, custom_id="admin_list")
    async def list_btn(self, interaction: discord.Interaction, button: ui.Button):
        text = "\n".join(f"`{k}` — {v['label']} ({v['price']}円)" for k,v in ITEM_CONFIG.items())
        await interaction.response.send_message(
            embed=Embed(title="📋 全項目キー一覧", description=text[:4000], color=0xcccccc),
            ephemeral=True
        )

# =====================
# ✅ コマンド定義
# =====================
@app_commands.command(name="panel", description="代行サービスパネルを表示")
async def panel_cmd(interaction: discord.Interaction):
    embed = Embed(
        title="🐱 にゃんこ大戦争 代行サービス",
        description="下のメニューから希望のサービスを選択してください。\n✅ 引き継ぎコードと認証番号だけで完了！アカウント情報不要",
        color=0xffaa00
    )
    embed.set_footer(text="24時間稼働中🔥 | bcsfe 利用")
    await interaction.response.send_message(embed=embed, view=ClonePanelView(interaction.guild_id))

@app_commands.command(name="setprice", description="項目別価格を設定（管理者のみ）")
async def setprice_cmd(interaction: discord.Interaction, key: str, price: int):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者専用コマンドです。", ephemeral=True)
        return
    if key not in ITEM_CONFIG:
        await interaction.response.send_message(
            f"❌ 項目キー `{key}` は存在しません。`/admin_list` で確認してください。",
            ephemeral=True
        )
        return
    ov = load_price_overrides(interaction.guild_id)
    ov[key] = price
    save_price_overrides(interaction.guild_id, ov)
    await interaction.response.send_message(
        f"✅ `{ITEM_CONFIG[key]['label']}` の価格を **{price}円** に変更しました。",
        ephemeral=True
    )

@app_commands.command(name="setjisseki", description="実績チャンネルを設定（管理者のみ）")
async def setjisseki_cmd(interaction: discord.Interaction, channel_id: str):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者専用コマンドです。", ephemeral=True)
        return
    settings = load_settings(interaction.guild_id)
    settings["jisseki_channel_id"] = channel_id
    save_settings(interaction.guild_id, settings)
    await interaction.response.send_message(
        f"✅ 実績チャンネルを `{channel_id}` に設定しました。",
        ephemeral=True
    )

@app_commands.command(name="admin_list", description="全項目キー一覧を表示（管理者のみ）")
async def admin_list_cmd(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者専用コマンドです。", ephemeral=True)
        return
    text = "\n".join(f"`{k}` — {v['label']} ({v['price']}円)" for k,v in ITEM_CONFIG.items())
    await interaction.response.send_message(
        embed=Embed(title="📋 全項目キー一覧", description=text[:4000], color=0xcccccc),
        ephemeral=True
    )

# =====================
# ✅ Bot起動
# =====================
async def setup_hook():
    bot.tree.add_command(panel_cmd)
    bot.tree.add_command(setprice_cmd)
    bot.tree.add_command(setjisseki_cmd)
    bot.tree.add_command(admin_list_cmd)
    await bot.tree.sync()

bot.setup_hook = setup_hook

@bot.event
async def on_ready():
    print(f"✅ ログイン完了: {bot.user}")
    logger.info(f"Logged in as {bot.user}")

if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN")
    if not TOKEN:
        logger.error("❌ DISCORD_TOKEN が設定されていません！環境変数を確認してください。")
        exit(1)
    bot.run(TOKEN)
