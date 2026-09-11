import discord
from discord import app_commands, ui, Embed, Color, ButtonStyle
from discord.ext import commands
import os
import json
import asyncio
import functools
import uuid
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple

# ======================================================
# 🔧 設定（ここを自分の環境に合わせて編集してください）
# ======================================================
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "ここにBotトークンを貼り付け")
ADMIN_IDS = [123456789012345678]  # 管理者のDiscord ID
JISSEKI_CHANNEL_ID = 1546928125231767633  # 実績チャンネルID

# 価格設定
CLONE_PRICE_DEFAULT = 500
FULL_EDIT_PRICE_DEFAULT = 1500
RECOVERY_PRICE_DEFAULT = 300
CHARA_UNLOCK_PRICE_DEFAULT = 200
CHARA_LVMAX_PRICE_DEFAULT = 300
CHARA_FORM_PRICE_DEFAULT = 300

# ファイル保存先
PAYPAY_DATA_FILE = "paypay_data.json"
ORDER_LOG_FILE = "order_log.json"
SETTINGS_FILE = "bot_settings.json"
PRICE_FILE = "price_overrides.json"

# PayPay連携の有無（paypayu が使えない環境では False に）
PAYPAY_AVAILABLE = False
try:
    import paypayu
    PAYPAY_AVAILABLE = True
except ImportError:
    pass

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
logger = logging.getLogger("bcsfe_bot")

JST = timezone(timedelta(hours=9))

# ======================================================
# 📦 商品・サービス一覧
# ======================================================
ITEM_CONFIG: Dict[str, Dict[str, Any]] = {
    # ━━ リソース系 ━━
    "catfood_50000":       {"label": "ネコ缶 50,000個",           "price": 300},
    "xp_max":              {"label": "経験値 最大",               "price": 200},
    "np_max":              {"label": "NP 9,999個",                "price": 200},
    "nyan_ticket_999":     {"label": "にゃんこチケット 999枚",    "price": 200},
    "rare_tickets_999":    {"label": "レアチケット 999枚",        "price": 300},
    "platinum_29":         {"label": "プラチナチケット +29枚",     "price": 400},
    "legend_29":           {"label": "レジェンドチケット +29枚",   "price": 600},
    "platinum_shard_90":   {"label": "プラチナのかけら +90個",    "price": 300},
    "leadership_999":      {"label": "統率力 999",                "price": 100},
    "battle_items_999":    {"label": "戦闘アイテム 各999個",       "price": 200},
    "matatabi_998":        {"label": "ネコ缶(フルーツ) 各998個",   "price": 300},
    "cats_eye_999":         {"label": "ネコの目 各999個",           "price": 300},
    "nekovitan_999":       {"label": "ネコビタン 各999個",         "price": 300},
    "castle_parts_999":    {"label": "オトート素材 各999個",       "price": 300},
    "event_ticket_999":    {"label": "イベントチケット 各999個",   "price": 300},
    "honnou_99":           {"label": "本能玉 全種Lv99",            "price": 500},
    "dungeon_medal_99":    {"label": "ダンジョンメダル 各99個",    "price": 300},
    # ━━ ステージ全クリア系 ━━
    "main_clear":          {"label": "ストーリー全クリア+お宝金",   "price": 500},
    "zombie_clear":        {"label": "ゾンビステージ全クリア",     "price": 400},
    "old_legend_clear":    {"label": "レジェンドストーリー全クリア", "price": 600},
    "true_legend_clear":   {"label": "真レジェンド全クリア",       "price": 600},
    "zero_legend_clear":   {"label": "ゼロレジェンド全クリア",     "price": 400},
    "makai_clear":         {"label": "魔界編全クリア",             "price": 400},
    "event_clear":         {"label": "イベントステージ全クリア",   "price": 600},
    # ━━ キャラクター系 ━━
    "all_char_unlock":      {"label": "全キャラ開放",               "price": 800},
    "error_char_delete":    {"label": "エラーキャラ削除",           "price": 0},
    "all_char_lv_max":      {"label": "全キャラLvMAX",             "price": 800},
    "all_char_max_form":    {"label": "全キャラ最高形態",           "price": 800},
    "all_honnou_max":       {"label": "全キャラ本能全開放LvMAX",    "price": 1000},
    # ━━ その他 ━━
    "telop_delete":        {"label": "開放テロップ削除",           "price": 0},
    "slot_max":             {"label": "編成スロット数最大拡張",     "price": 50},
    "medal_all":            {"label": "にゃんこメダル全開放",       "price": 100},
    "enemy_book_all":       {"label": "敵キャラ図鑑全開放",         "price": 100},
    "user_rank_all":        {"label": "ユーザーランク報酬全受取",   "price": 50},
    "playtime_max":         {"label": "プレイ時間カンスト",         "price": 200},
    "gold_pass":            {"label": "ゴールド会員化",             "price": 200},
    "facility_max":         {"label": "施設LvMAX",                 "price": 100},
    "gamatoto_max":         {"label": "ガマトトLvMAX",              "price": 200},
    "gamatoto_legend":      {"label": "ガマトト助手全員レジェンド", "price": 200},
    "ad_free":              {"label": "広告非表示（β）",            "price": 50},
    "ototo_max":            {"label": "オトート全城強化LvMAX",      "price": 200},
    "shrine_max":           {"label": "にゃんこ神社LvMAX",         "price": 100},
}

# ======================================================
# 💾 データ管理
# ======================================================
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
    cutoff = datetime.now(JST) - timedelta(days=1)
    log = [e for e in log if datetime.fromisoformat(e["timestamp"]).astimezone(JST) > cutoff]
    return log

def log_order(user_id: int, username: str, items: list, amount: int, status: str):
    log = load_order_log()
    log.append({
        "timestamp": datetime.now(JST).isoformat(),
        "user_id": str(user_id),
        "username": username,
        "items": items,
        "amount": amount,
        "status": status,
    })
    with open(ORDER_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=4, ensure_ascii=False)
    logger.info(f"[ORDER] {username}({user_id}) {items} {amount}円 [{status}]")

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

def get_jisseki_channel_id(guild_id: int) -> Optional[int]:
    settings = load_settings(guild_id)
    val = settings.get("jisseki_channel_id")
    return int(val) if val else JISSEKI_CHANNEL_ID

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

# ======================================================
# 🔧 bcsfe 編集ヘルパー（インポートできない環境向け）
# ======================================================
try:
    from bcsfe import core
    BCSFE_AVAILABLE = True
except ImportError:
    BCSFE_AVAILABLE = False
    logger.warning("bcsfe がインストールされていないため、代行処理は実行できません")

def _sv(save_file, attr: str, value: int):
    try:
        obj = getattr(save_file, attr)
        try: obj.value = value; return
        except: pass
        try: setattr(save_file, attr, value); return
        except: pass
        try: obj.set(value)
        except: pass
    except Exception as e:
        logger.warning(f"sv({attr},{value}): {e}")

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
                    try: obj.set(val)
                    except: pass
                except Exception as e:
                    logger.warning(f"sv({attr},{val}): {e}")

            if key == "catfood_50000":
                try: sv("catfood", min(int(sf.catfood) + 50000, 9999999))
                except: sv("catfood", min(int(sf.catfood.value) + 50000, 9999999))
            elif key == "xp_max": sv("xp", 99999999)
            elif key == "np_max": sv("np", 9999)
            elif key == "nyan_ticket_999": sv("normal_tickets", 999)
            elif key == "rare_tickets_999": sv("rare_tickets", 999)
            elif key == "leadership_999": sv("leadership", 999)
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
            else:
                applied.append(f"✅ {ITEM_CONFIG.get(key,{}).get('label',key)}（スキップ:簡易版未実装）")
                continue
            applied.append(ITEM_CONFIG[key]["label"])
        except Exception as e:
            logger.warning(f"[apply_edits] {key} 失敗: {e}")
    return applied

def run_bcsfe_download(transfer_code: str, confirmation_code: str, cc_str: str):
    if not BCSFE_AVAILABLE:
        return None, "bcsfe がインストールされていません"
    from bcsfe import core
    core.core_data.init_data()
    cc_map = {"jp": "jp", "en": "en", "tw": "tw", "kr": "kr"}
    cc = core.CountryCode(cc_map.get(cc_str.lower(), "jp"))
    gv = core.GameVersion(120200)
    server_handler, result = core.ServerHandler.from_codes(
        transfer_code.strip(), confirmation_code.strip(),
        cc, gv, print=False, save_backup=False
    )
    if server_handler is None:
        if result is not None and result.response is not None:
            return None, f"ダウンロード失敗 (HTTP {result.response.status_code})"
        return None, "ダウンロード失敗（コードを確認）"
    return server_handler, None

def run_bcsfe_upload(server_handler):
    if not BCSFE_AVAILABLE:
        return None
    return server_handler.get_codes(upload_managed_items=False)

# ======================================================
# 📤 実績チャンネル投稿
# ======================================================
async def post_jisseki(bot, user: discord.User, items: list, amount: int, guild_id: int = 0):
    ch_id = get_jisseki_channel_id(guild_id)
    if ch_id is None:
        return
    ch = bot.get_channel(ch_id)
    if ch is None:
        return
    now = datetime.now(JST)
    timestamp_str = now.strftime("%Y/%m %H:%M")
    items_text = "\n".join(f"・{item}" for item in items)
    embed = Embed(title="📝 代行実績", color=0xccff00)
    embed.add_field(name="依頼者", value=user.mention, inline=True)
    embed.add_field(name="金額", value=f"{amount}円", inline=True)
    embed.add_field(name="内容", value=items_text, inline=False)
    embed.set_footer(text=f"24/h稼働中🔥 | {timestamp_str}")
    if user.avatar:
        embed.set_thumbnail(url=user.avatar.url)
    await ch.send(embed=embed)

# ======================================================
# 💳 PayPay 受取処理
# ======================================================
async def paypay_receive(interaction: discord.Interaction, link_raw: str, total: int, label: str) -> bool:
    if not PAYPAY_AVAILABLE:
        await interaction.followup.send(embed=Embed(title="⚠️ 確認", description="テストモード: 支払確認をスキップします", color=0xffaa00), ephemeral=True)
        return True
    admin_id = str(ADMIN_IDS[0])
    user_paypay = load_paypay_data().get(admin_id)
    if not user_paypay:
        await interaction.followup.send(embed=Embed(title="❌ PayPay未登録", description="管理者に連絡してください。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "ADMIN_NO_PAYPAY")
        return False
    link_code = link_raw.strip()
    if "pay.paypay.ne.jp/" in link_code:
        link_code = link_code.split("pay.paypay.ne.jp/")[-1].split("?")[0]
    link_info = await paypayu.check_link(link_code)
    if not link_info:
        await interaction.followup.send(embed=Embed(title="❌ リンク無効", description="送金リンクが無効または使用済みです。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "INVALID_LINK")
        return False
    try:
        link_amount = int(link_info["payload"]["pendingP2PInfo"]["amount"])
        if link_amount < total:
            await interaction.followup.send(embed=Embed(title="❌ 金額不足", description=f"必要:{total}円 / 受信:{link_amount}円", color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), [label], total, f"SHORT:{link_amount}")
            return False
    except (KeyError, TypeError, ValueError):
        pass
    result = await paypayu.link_rev(link_code, user_paypay["phone"], user_paypay["password"], user_paypay["uuid"])
    if result == "LOGINERR":
        await interaction.followup.send(embed=Embed(title="❌ PayPayログインエラー", description="管理者に連絡してください。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "LOGIN_ERR")
        return False
    elif result is not True:
        await interaction.followup.send(embed=Embed(title="❌ 受取失敗", description="管理者にお問い合わせください。", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), [label], total, "RECEIVE_FAIL")
        return False
    return True

# ======================================================
# ⚙️ 共通 ダウンロード→編集→アップロード
# ======================================================
async def bcsfe_process(interaction: discord.Interaction, t_code: str, a_code: str,
                        item_keys: list, label_list: list, total: int, no_edit: bool = False):
    loop = asyncio.get_event_loop()
    try:
        server_handler, err = await loop.run_in_executor(
            None, functools.partial(run_bcsfe_download, t_code, a_code, "jp")
        )
        if server_handler is None:
            await interaction.followup.send(
                embed=Embed(title="❌ ダウンロード失敗",
                            description=f"{err}\n\n⚠️ 支払い済みの場合は管理者へ連絡を",
                            color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), label_list, 0, f"DL_FAIL:{err}")
            return
        applied = [] if no_edit else apply_edits(server_handler.save_file, item_keys)
        codes = await loop.run_in_executor(None, functools.partial(run_bcsfe_upload, server_handler))
        if codes is None:
            await interaction.followup.send(
                embed=Embed(title="❌ アップロード失敗",
                            description="⚠️ 支払い済みの場合は管理者へ連絡を", color=0xff3333), ephemeral=True)
            log_order(interaction.user.id, str(interaction.user), label_list, 0, "UL_FAIL")
            return
        transfer_code, confirmation_code = codes
        items_text = "\n".join(f"✅ {i}" for i in applied) or "なし"
        embed = Embed(title="🎉 代行完了", description="新しい引き継ぎコードでログインしてください", color=0x00cc88)
        embed.add_field(name="適用内容", value=items_text, inline=False)
        embed.add_field(name="📋 引き継ぎコード", value=f"`{transfer_code}`", inline=False)
        embed.add_field(name="🔢 認証番号", value=f"`{confirmation_code}`", inline=False)
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
            embed=Embed(title="❌ 予期しないエラー", description=f"```{str(e)[:300]}```", color=0xff3333), ephemeral=True)
        log_order(interaction.user.id, str(interaction.user), label_list, 0, f"ERROR:{e}")

# ======================================================
# 📝 モーダル：購入情報入力
# ======================================================
class PurchaseModal(ui.Modal, title="購入情報入力"):
    paypay_link = ui.TextInput(
        label="PayPay 送金リンク",
        placeholder="https://pay.paypay.ne.jp/xxxx",
        required=True, style=discord.TextStyle.short
    )
    t_code = ui.TextInput(
        label="引き継ぎコード",
        placeholder="例: ABCDEF1234567890",
        required=True, style=discord.TextStyle.short
    )
    a_code = ui.TextInput(
        label="認証番号",
        placeholder="例: 1234",
        required=True, max_length=10, style=discord.TextStyle.short
    )
    def __init__(self, items: list, total: int):
        super().__init__(timeout=300)
        self.items = items
        self.total = total

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send(
            embed=Embed(title="⏳ 処理中...", description="確認中です。しばらくお待ちください。", color=0xffaa00),
            ephemeral=True
        )
        ok = await paypay_receive(interaction, self.paypay_link.value, self.total, "・".join(self.items))
        if not ok:
            return
        log_order(interaction.user.id, str(interaction.user), self.items, self.total, "PAID")
        await bcsfe_process(interaction, self.t_code.value, self.a_code.value, self.items, self.items, self.total)

# ======================================================
# 🖥️ パネル表示
# ======================================================
_ITEM_KEYS = list(ITEM_CONFIG.keys())
_ITEMS_A = _ITEM_KEYS[:21]
_ITEMS_B = _ITEM_KEYS[21:]

async def _show_confirm(interaction: discord.Interaction, selected: list):
    total = sum(get_price(v, interaction.guild_id) for v in selected)
    items_text = "\n".join(f"{ITEM_CONFIG[v]['label']} │ {get_price(v, interaction.guild_id)}円" for v in selected)
    await interaction.message.edit(view=PanelView(interaction.guild_id or 0))
    embed = Embed(title="🛒 注文確認", color=0x00cc88)
    embed.add_field(name="選択内容", value=items_text, inline=False)
    embed.add_field(name="💰 合計金額", value=f"**{total}円**", inline=False)
    confirm_view = ui.View(timeout=300)
    class ConfirmBtn(ui.Button):
        def __init__(self_btn):
            super().__init__(label="🛒 購入する", style=ButtonStyle.green)
        async def callback(self_btn, bi: discord.Interaction):
            await bi.response.send_modal(PurchaseModal(selected, total))
    confirm_view.add_item(ConfirmBtn())
    await interaction.response.send_message(embed=embed, view=confirm_view, ephemeral=True)

class PanelView(ui.View):
    def __init__(self, guild_id: int = 0):
        super().__init__(timeout=None)
        self._gid = guild_id
        self.add_item(PanelSelectA(guild_id))
        self.add_item(PanelSelectB(guild_id))

class PanelSelectA(ui.Select):
    def __init__(self, gid: int):
        opts = [discord.SelectOption(label=ITEM_CONFIG[k]["label"], value=k, description=f"{get_price(k,gid)}円") for k in _ITEMS_A]
        super().__init__(placeholder="① リソース・チケット・ステージ系", min_values=1, max_values=len(opts), options=opts, row=0)
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.edit(view=PanelView(interaction.guild_id or 0))
        await _show_confirm(interaction, self.values)

class PanelSelectB(ui.Select):
    def __init__(self, gid: int):
        opts = [discord.SelectOption(label=ITEM_CONFIG[k]["label"], value=k, description=f"{get_price(k,gid)}円") for k in _ITEMS_B]
        super().__init__(placeholder="② キャラ・施設・その他系", min_values=1, max_values=len(opts), options=opts, row=1)
    async def callback(self, interaction: discord.Interaction):
        await interaction.message.edit(view=PanelView(interaction.guild_id or 0))
        await _show_confirm(interaction, self.values)

# ======================================================
# 🤖 Bot 本体
# ======================================================
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

@bot.event
async def on_ready():
    logger.info(f"✅ Bot起動: {bot.user} (ID: {bot.user.id})")
    bot.add_view(PanelView())
    try:
        synced = await tree.sync()
        logger.info(f"✅ コマンド同期: {len(synced)}個")
    except Exception as e:
        logger.error(f"❌ 同期エラー: {e}")
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="にゃんこ大戦争"))

@tree.command(name="にゃんこパネル設置", description="代行パネルを表示（管理者専用）")
async def panel_cmd(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者のみ使用可", ephemeral=True)
        return
    embed = Embed(title="🐱 にゃんこ大戦争 代行自販機",
                  description="下のメニューから項目を選択してください\n複数選択可 → 合計金額が表示されます",
                  color=0x5865F2)
    embed.set_footer(text="⚠️ 自己責任でご利用ください")
    await interaction.channel.send(embed=embed, view=PanelView(interaction.guild_id))
    await interaction.response.send_message("✅ パネルを設置しました", ephemeral=True)

@tree.command(name="実績チャンネル設置", description="実績を投稿するチャンネルを設定（管理者専用）")
async def set_jisseki_cmd(interaction: discord.Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者のみ使用可", ephemeral=True)
        return
    settings = load_settings(interaction.guild_id)
    settings["jisseki_channel_id"] = str(interaction.channel_id)
    save_settings(interaction.guild_id, settings)
    await interaction.response.send_message(f"✅ 実績チャンネルを {interaction.channel.mention} に設定", ephemeral=True)

@tree.command(name="注文履歴", description="注文履歴を表示（管理者専用）")
async def history_cmd(interaction: discord.Interaction, limit: int = 10):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者のみ使用可", ephemeral=True)
        return
    log = load_order_log()
    if not log:
        await interaction.response.send_message("📭 履歴なし", ephemeral=True)
        return
    recent = log[-limit:][::-1]
    lines = [f"`{e['timestamp'][5:16]}` **{e['username']}** {', '.join(e['items'])} │ {e['amount']}円 `[{e['status']}]`" for e in recent]
    embed = Embed(title=f"📋 直近{len(recent)}件の注文履歴", description="\n".join(lines), color=0x5865F2)
    await interaction.response.send_message(embed=embed, ephemeral=True)

if __name__ == "__main__":
    if BOT_TOKEN == "ここにBotトークンを貼り付け":
        print("⚠️ BOT_TOKEN を設定してください")
        exit(1)
    if not ADMIN_IDS or ADMIN_IDS == [123456789012345678]:
        print("⚠️ ADMIN_IDS に自分のDiscord IDを設定してください")
        exit(1)
    bot.run(BOT_TOKEN)
