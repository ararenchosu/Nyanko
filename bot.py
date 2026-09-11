import discord
from discord import ui, Embed, Color, ButtonStyle, Interaction
from discord.ext import commands
import os
import json
from typing import Dict, List, Optional

# ======================================================
# ✅ 基本設定
# ======================================================
BOT_TOKEN = os.getenv("DISCORD_TOKEN", "")
ADMIN_USER_IDS = [123456789012345678]  # 👈 管理者のユーザーIDを入力
JISSEKI_CHANNEL_ID = 1546928125231767633  # 実績チャンネルID

# 価格デフォルト値
CLONE_PRICE_DEFAULT = 500
CHARA_UNLOCK_PRICE_DEFAULT = 300

# 商品定義
ITEM_CONFIG: Dict[str, Dict] = {
    "catfood_50000":     {"label": "ネコ缶 50,000個", "price": 150},
    "xp_max":            {"label": "XP 999,999", "price": 150},
    "np_max":            {"label": "にゃんこP 999,999", "price": 150},
    "nyan_ticket_999":   {"label": "にゃんこチケット ×999", "price": 300},
    "rare_tickets_999":  {"label": "レアチケット ×999", "price": 300},
    "platinum_29":       {"label": "プラチナチケット ×29", "price": 300},
    "legend_29":         {"label": "レジェンドチケット ×29", "price": 300},
    "platinum_shard_90": {"label": "プラチナのかけら ×90", "price": 150},
    "battle_items_999":  {"label": "アイテム各種 ×999", "price": 150},
    "matatabi_998":      {"label": "マタタビ ×998", "price": 150},
    "cats_eye_999":      {"label": "ネコ目チケット ×999", "price": 150},
    "nekovitan_999":     {"label": "ネコビタン ×999", "price": 150},
    "castle_parts_999":  {"label": "城ドレス/パーツ ×999", "price": 150},
    "event_ticket_999":  {"label": "イベントチケット ×999", "price": 150},
    "main_clear":        {"label": "第1～3章 全クリア", "price": 500},
    "zombie_clear":      {"label": "未来編 全クリア", "price": 500},
    "old_legend_clear":  {"label": "レジェンドストーリー 全クリア", "price": 500},
    "true_legend_clear": {"label": "真レジェンドストーリー 全クリア", "price": 800},
    "zero_legend_clear": {"label": "0章 全クリア", "price": 800},
    "makai_clear":       {"label": "魔界編 全クリア", "price": 500},
    "event_clear":       {"label": "イベントステージ 全クリア", "price": 500},
    "all_char_unlock":   {"label": "全キャラクター開放", "price": 1500},
    "all_char_lv_max":   {"label": "全キャラ Lv.MAX", "price": 1500},
    "all_char_max_form": {"label": "全キャラ 最高形態", "price": 1500},
    "all_honnou_max":    {"label": "全キャラ 本能全開放", "price": 1500},
    "facility_max":      {"label": "施設/研究 全MAX", "price": 800},
    "gamatoto_max":      {"label": "ガマトト探検隊 全開放", "price": 500},
    "gamatoto_legend":   {"label": "ガマトト レジェンド", "price": 500},
    "ototo_max":         {"label": "オトート開発隊 全MAX", "price": 500},
    "shrine_max":        {"label": "神社/にゃんこの祈り 全MAX", "price": 500},
    "medal_all":         {"label": "勲章/メダル 全開放", "price": 300},
    "enemy_book_all":    {"label": "図鑑 全開放", "price": 300},
    "user_rank_all":     {"label": "ユーザーランク 最大", "price": 300},
    "playtime_max":      {"label": "プレイ時間 最大", "price": 150},
    "gold_pass":         {"label": "ゴールドパス適用", "price": 300},
    "ad_free":           {"label": "広告解除", "price": 150},
    "slot_max":          {"label": "スロット/枠 全開放", "price": 300},
    "telop_delete":      {"label": "テロップ削除", "price": 150},
}

# ======================================================
# ✅ データ保存用
# ======================================================
def load_json(path: str, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_price_overrides(guild_id: int) -> Dict:
    return load_json(f"price_{guild_id}.json", {})

def save_price_overrides(guild_id: int, data: Dict):
    save_json(f"price_{guild_id}.json", data)

def load_settings(guild_id: int) -> Dict:
    return load_json(f"settings_{guild_id}.json", {"jisseki_channel_id": JISSEKI_CHANNEL_ID, "jisseki_count": 0})

def save_settings(guild_id: int, data: Dict):
    save_json(f"settings_{guild_id}.json", data)

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_USER_IDS

def get_price(key: str, guild_id: int) -> int:
    ov = load_price_overrides(guild_id)
    return ov.get(key, ITEM_CONFIG[key]["price"])

def get_special_price(key: str, default: int, guild_id: int) -> int:
    ov = load_price_overrides(guild_id)
    return ov.get(key, default)

async def post_jisseki(bot, guild_id: int, buyer_name: str, items: List[str], total: int):
    st = load_settings(guild_id)
    ch_id = int(st.get("jisseki_channel_id", JISSEKI_CHANNEL_ID))
    st["jisseki_count"] = st.get("jisseki_count", 0) + 1
    save_settings(guild_id, st)

    ch = bot.get_channel(ch_id)
    if not ch:
        return

    embed = Embed(title=f"📝 実績 {st['jisseki_count']:02d}", color=0x00ff88)
    embed.add_field(name="購入者", value=buyer_name, inline=False)
    embed.add_field(name="内容", value="\n".join(f"・{ITEM_CONFIG[k]['label']}" for k in items), inline=False)
    embed.add_field(name="金額", value=f"```{total}円```", inline=False)
    await ch.send(embed=embed)

# ======================================================
# ✅ Bot初期化
# ======================================================
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
tree = bot.tree

# ======================================================
# ✅ モーダル（入力フォーム）
# ======================================================
class ServiceModal(ui.Modal, title="📋 ご依頼情報入力"):
    def __init__(self, service_name: str, price: int, is_clone=False):
        super().__init__()
        self.service_name = service_name
        self.price = price
        self.is_clone = is_clone
        self.add_item(ui.TextInput(
            label="📱 引き継ぎコード",
            placeholder="XXXX-XXXX-XXXX-XXXX",
            required=True,
            min_length=12,
            max_length=19
        ))
        self.add_item(ui.TextInput(
            label="🔑 認証番号",
            placeholder="12345678",
            required=True,
            min_length=4,
            max_length=16
        ))
        if is_clone:
            self.add_item(ui.TextInput(
                label="📝 備考（任意）",
                placeholder="何かあれば記入",
                required=False,
                style=discord.TextStyle.long
            ))

    async def on_submit(self, interaction: Interaction):
        code = str(self.children[0])
        auth = str(self.children[1])
        embed = Embed(title="✅ ご依頼を受け付けました", color=0x00ff00)
        embed.add_field(name="サービス", value=self.service_name, inline=False)
        embed.add_field(name="金額", value=f"```{self.price}円```", inline=False)
        embed.add_field(name="引き継ぎコード", value=f"`{code}`", inline=False)
        embed.add_field(name="認証番号", value=f"`{auth}`", inline=False)
        embed.set_footer(text="24時間以内に対応します🔥")
        await interaction.response.send_message(embed=embed, ephemeral=False)


class CharaModal(ui.Modal, title="👤 キャラクター編集"):
    def __init__(self, title: str, price: int):
        super().__init__()
        self.price = price
        self.add_item(ui.TextInput(label="編集したいキャラ名", required=True))
        self.add_item(ui.TextInput(label="内容/レベルなど", style=discord.TextStyle.long, required=True))

    async def on_submit(self, interaction: Interaction):
        chara = str(self.children[0])
        detail = str(self.children[1])
        embed = Embed(title="👤 キャラクター編集 受付", color=0xffcc00)
        embed.add_field(name="キャラ名", value=chara, inline=False)
        embed.add_field(name="詳細", value=detail, inline=False)
        embed.add_field(name="金額", value=f"```{self.price}円```", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=False)


class PurchaseModal(ui.Modal, title="💳 購入情報入力"):
    def __init__(self, item_keys: List[str], total: int):
        super().__init__()
        self.item_keys = item_keys
        self.total = total
        self.add_item(ui.TextInput(
            label="📱 引き継ぎコード",
            placeholder="XXXX-XXXX-XXXX-XXXX",
            required=True
        ))
        self.add_item(ui.TextInput(
            label="🔑 認証番号",
            placeholder="12345678",
            required=True
        ))

    async def on_submit(self, interaction: Interaction):
        code = str(self.children[0])
        auth = str(self.children[1])
        labels = [ITEM_CONFIG[k]["label"] for k in self.item_keys]
        embed = Embed(title="✅ 購入を受け付けました", color=0x00ff00)
        embed.add_field(name="内容", value="\n".join(f"・{l}" for l in labels), inline=False)
        embed.add_field(name="合計金額", value=f"```{self.total}円```", inline=False)
        embed.add_field(name="引き継ぎコード", value=f"`{code}`", inline=False)
        embed.add_field(name="認証番号", value=f"`{auth}`", inline=False)
        embed.set_footer(text="24時間以内に対応します🔥")
        await interaction.response.send_message(embed=embed)
        await post_jisseki(bot, interaction.guild_id, str(interaction.user), self.item_keys, self.total)

# ======================================================
# ✅ 管理者メニュービュー
# ======================================================
class AdminMenuView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id

    @ui.Button(label="💰 価格を変更", style=ButtonStyle.primary)
    async def price_btn(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            embed=Embed(title="💰 価格設定", description="`/setprice 項目キー 金額` で変更\n例: `/setprice catfood_50000 150`", color=0x99ccff),
            ephemeral=True
        )

    @ui.Button(label="📝 実績チャンネル設定", style=ButtonStyle.primary)
    async def ch_btn(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_message(
            embed=Embed(title="📝 実績チャンネル設定", description="`/setjisseki チャンネルID` で設定", color=0x99ccff),
            ephemeral=True
        )

    @ui.Button(label="📋 全項目キー一覧", style=ButtonStyle.secondary)
    async def list_btn(self, interaction: Interaction, button: ui.Button):
        text = "\n".join(f"`{k}` — {v['label']} ({v['price']}円)" for k,v in ITEM_CONFIG.items())
        await interaction.response.send_message(
            embed=Embed(title="📋 全項目キー一覧", description=text[:4000], color=0xcccccc),
            ephemeral=True
        )

# ======================================================
# ✅ 単品確認ビュー
# ======================================================
class ConfirmPurchaseView(ui.View):
    def __init__(self, item_keys: List[str], label_list: List[str], total: int):
        super().__init__(timeout=120)
        self.item_keys = item_keys
        self.label_list = label_list
        self.total = total

    @ui.Button(label="✅ 購入・編集実行", style=ButtonStyle.success)
    async def confirm_btn(self, interaction: Interaction, button: ui.Button):
        await interaction.response.send_modal(PurchaseModal(self.item_keys, self.total))

    @ui.Button(label="❌ キャンセル", style=ButtonStyle.secondary)
    async def cancel_btn(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(
            embed=Embed(title="❌ キャンセル", description="購入をキャンセルしました。", color=0x888888),
            view=None
        )

# ======================================================
# ✅ メインメニュー選択（Selectエラー修正版）
# ======================================================
class MainMenuSelect(ui.Select):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        super().__init__(
            placeholder="✅ 希望のサービスを選択してください",
            options=[
                discord.SelectOption(label="🔧 管理者メニュー", value="admin_menu", emoji="🔧"),
                discord.SelectOption(label="📋 アカウント複製", value="clone", emoji="📋"),
                discord.SelectOption(label="👤 キャラクター編集", value="edit_chara", emoji="👤"),
                discord.SelectOption(label="🎫 単品編集・購入", value="edit_single", emoji="🎫"),
                discord.SelectOption(label="📦 まとめてセット購入", value="edit_set", emoji="📦"),
            ],
            min_values=1, max_values=1
        )

    async def callback(self, interaction: Interaction):
        selected = self.values[0]
        gid = self.guild_id

        if selected == "admin_menu":
            if not is_admin(interaction.user.id):
                await interaction.response.send_message("❌ 管理者専用メニューです。", ephemeral=True)
                return
            await interaction.response.send_message(
                embed=Embed(title="🔧 管理者メニュー", description="以下から選択してください。", color=0x9999ff),
                view=AdminMenuView(gid),
                ephemeral=True
            )
            return

        if selected == "clone":
            price = get_special_price("clone", CLONE_PRICE_DEFAULT, gid)
            await interaction.response.send_modal(ServiceModal("✅ アカウント複製", price, is_clone=True))
            return

        if selected == "edit_chara":
            price = get_special_price("chara_edit", CHARA_UNLOCK_PRICE_DEFAULT, gid)
            await interaction.response.send_modal(CharaModal("👤 キャラクター編集", price))
            return

        if selected == "edit_single":
            view = SingleItemView(gid)
            embed = Embed(title="🎫 単品編集", description="編集したい項目を選んでください。", color=0xffcc00)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return

        if selected == "edit_set":
            view = SetItemView(gid)
            embed = Embed(title="📦 セット購入", description="まとめて適用するセットを選んでください。", color=0x00cc88)
            await interaction.response.send_message(embed=embed, view=view, ephemeral=True)
            return


class ClonePanelView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=180)
        self.add_item(MainMenuSelect(guild_id))

# ======================================================
# ✅ 単品編集選択（Selectエラー修正版）
# ======================================================
class SingleItemSelect(ui.Select):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        opts = [discord.SelectOption(label=v["label"], value=k) for k,v in ITEM_CONFIG.items()]
        super().__init__(
            placeholder="編集する項目を選択（複数可）",
            min_values=1, max_values=min(8, len(opts)),
            options=opts
        )

    async def callback(self, interaction: Interaction):
        items_selected = self.values
        total = sum(get_price(k, self.guild_id) for k in items_selected)
        labels = [ITEM_CONFIG[k]["label"] for k in items_selected]
        embed = Embed(title="✅ 選択内容確認", color=0xffcc00)
        embed.add_field(name="選択項目", value="\n".join(f"・{l}" for l in labels), inline=False)
        embed.add_field(name="合計金額", value=f"```{total}円```", inline=False)
        await interaction.response.edit_message(embed=embed, view=ConfirmPurchaseView(items_selected, labels, total))


class SingleItemView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.add_item(SingleItemSelect(guild_id))

# ======================================================
# ✅ セット購入選択（Selectエラー修正版）
# ======================================================
class SetItemSelect(ui.Select):
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        super().__init__(
            placeholder="セットを選択してください",
            options=[
                discord.SelectOption(label="💰 資材MAXセット", value="set_money", description="ネコ缶・XP・チケット類 全MAX", emoji="💰"),
                discord.SelectOption(label="🗺️ ストーリー全開放セット", value="set_map", description="第1～3章/レジェンド/魔界 全クリア", emoji="🗺️"),
                discord.SelectOption(label="🦊 キャラ極みセット", value="set_char", description="全キャラ開放+LvMAX+最高形態+本能MAX", emoji="🦊"),
                discord.SelectOption(label="🏗️ 施設完備セット", value="set_facility", description="施設/ガマトト/神社 全MAX", emoji="🏗️"),
            ]
        )

    async def callback(self, interaction: Interaction):
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
        await interaction.response.edit_message(embed=embed, view=ConfirmPurchaseView(definition["items"], [definition["label"]], total))


class SetItemView(ui.View):
    def __init__(self, guild_id: int):
        super().__init__(timeout=120)
        self.add_item(SetItemSelect(guild_id))

# ======================================================
# ✅ コマンド定義
# ======================================================
@tree.command(name="panel", description="代行サービスパネルを表示")
async def panel_cmd(interaction: Interaction):
    embed = Embed(
        title="🐱 にゃんこ大戦争 代行サービス",
        description="下のメニューから希望のサービスを選択してください。\n✅ 引き継ぎコードと認証番号だけで完了！アカウント情報不要",
        color=0xffaa00
    )
    embed.set_footer(text="24時間稼働中🔥 | bcsfe 利用")
    await interaction.response.send_message(embed=embed, view=ClonePanelView(interaction.guild_id))


@tree.command(name="setprice", description="項目別価格を設定（管理者のみ）")
async def setprice_cmd(interaction: Interaction, key: str, price: int):
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


@tree.command(name="setjisseki", description="実績チャンネルを設定（管理者のみ）")
async def setjisseki_cmd(interaction: Interaction, channel_id: str):
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


@tree.command(name="admin_list", description="全項目キー一覧を表示（管理者のみ）")
async def admin_list_cmd(interaction: Interaction):
    if not is_admin(interaction.user.id):
        await interaction.response.send_message("❌ 管理者専用コマンドです。", ephemeral=True)
        return
    text = "\n".join(f"`{k}` — {v['label']} ({v['price']}円)" for k,v in ITEM_CONFIG.items())
    await interaction.response.send_message(
        embed=Embed(title="📋 全項目キー一覧", description=text[:4000], color=0xcccccc),
        ephemeral=True
    )

# ======================================================
# ✅ 起動処理
# ======================================================
@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ ログイン完了: {bot.user}")


if __name__ == "__main__":
    TOKEN = os.getenv("DISCORD_TOKEN", BOT_TOKEN)
    if not TOKEN or TOKEN in ("", "ここにBotトークンを貼り付け"):
        print("❌ DISCORD_TOKEN が設定されていません！環境変数を確認してください。")
        exit(1)
    bot.run(TOKEN)
