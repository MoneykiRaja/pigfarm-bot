import os
import json
import random
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
load_dotenv()
# Load token from environment variable
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")  # Use proper env var name
if not TOKEN:
    print("❌ Error: TELEGRAM_BOT_TOKEN environment variable not set!")
    exit(1)

print("🔑 Loaded token:", TOKEN[:10] + "..." if TOKEN else "None")

# Data management
DATA_FILE = "players.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)

FEED_FILE = "feed_data.json"

def load_feed_data():
    if os.path.exists(FEED_FILE):
        with open(FEED_FILE, "r") as f:
            return json.load(f)
    return {"mills": {}, "market": []}

def save_feed_data(data):
    with open(FEED_FILE, "w") as f:
        json.dump(data, f, indent=2)

def filter_valid_feed(stock):
    # Optional cleaner to remove spoiled feed — for now, just return stock
    return stock

MILL_LEVELS = {
    0: {"cooldown": 8, "amount": 2, "type": "normal"},
    1: {"cooldown": 6, "amount": 3, "type": "normal"},
    2: {"cooldown": 4, "amount": 4, "type": "normal"},
    3: {"cooldown": 3, "amount": 5, "type": "normal"},
    4: {"cooldown": 2, "amount": 6, "type": "normal"},
    5: {"cooldown": 1, "amount": 7, "type": "normal"},
    6: {"cooldown": 1, "amount": 8, "type": "premium"},
}

def can_produce(last_timestamp, cooldown_hours):
    try:
        last_time = datetime.fromisoformat(last_timestamp)
    except:
        return True
    now = datetime.now()
    return (now - last_time).total_seconds() >= cooldown_hours * 3600

# Task list - Admin-defined daily tasks
TASKS = {
    "join1": {
        "type": "telegram",
        "description": "Join our TON group 🪙",
        "url": "https://t.me/YourGroup",
        "reward": 3
    },
    "view1": {
        "type": "url",
        "description": "View sponsor page 🖼️",
        "url": "https://example.com/ad",
        "reward": 2
    },
    "share1": {
        "type": "manual",
        "description": "Share a pig meme in a group 🐷",
        "url": None,
        "reward": 5  # Changed from "special_feed" to integer for consistency
    }
}

MARKET = [
    {"type": "normal", "price": 2},
    {"type": "spotted", "price": 4},
    {"type": "golden", "price": 7}
]

def refresh_market():
    return random.choices(MARKET, k=3)  # 3 random offers

#porkplant data


# 🌭 Pork Plant Levels & Rewards
PLANT_LEVELS = {
    0: {"products": ["meat"], "reward": {"meat": 1}},
    1: {"products": ["meat"], "reward": {"meat": 1}},
    2: {"products": ["meat"], "reward": {"meat": 1}},
    3: {"products": ["meat"], "reward": {"meat": 1}},
    4: {"products": ["meat", "sausage"], "reward": {"meat": 1, "sausage": 2}},
    5: {"products": ["meat", "sausage"], "reward": {"meat": 1, "sausage": 2}},
    6: {"products": ["meat", "sausage", "bacon"], "reward": {"meat": 1, "sausage": 2, "bacon": 3.5}}
}

def has_processed_today(user_data, product):
    today = datetime.now().strftime("%Y-%m-%d")
    return user_data.get("last_processed", {}).get(product) == today

def mark_processed_today(user_data, product):
    today = datetime.now().strftime("%Y-%m-%d")
    if "last_processed" not in user_data:
        user_data["last_processed"] = {}
    user_data["last_processed"][product] = today


EXCHANGE_RATE = 100  # 100 coins = 1 TON 🪙 💰 👛 

# 🌭 Pork Plant Levels & Rewards

# Command handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()

    # Optional: Referrer check
    referrer_id = context.args[0] if context.args else None

    if user_id not in data:
        # New user: create record
        data[user_id] = {
            "username": user.username or user.first_name,
            "coins": 0,
            "streak": 0,
            "piglets": [],
            "referrals": 0,
            "claimed_tasks": []
        }

        # Reward user for joining
        data[user_id]["coins"] += 2

        # Handle referral bonus
        if referrer_id and referrer_id in data and referrer_id != user_id:
            data[referrer_id]["coins"] += 5
            data[referrer_id]["referrals"] = data[referrer_id].get("referrals", 0) + 1
            await update.message.reply_text("🎉 You joined with a referral! +2 coins for you 🐽")
            try:
                await context.bot.send_message(
                    chat_id=int(referrer_id),
                    text=f"🎉 Someone joined using your referral link! You earned 5 coins 🐷"
                )
            except Exception as e:
                print(f"Failed to send referral notification: {e}")
        else:
            await update.message.reply_text("🐷 Welcome to Pig Farm! Feed your pig and grow your farm.")

        save_data(data)
    else:
        await update.message.reply_text("👋 You're already part of the farm. Let's grow some pigs!")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()
    today = datetime.now(timezone.utc).date().strftime("%Y-%m-%d")

    # Initialize user data if not exists
    if user_id not in data:
        data[user_id] = {
            "username": user.username or user.first_name,
            "coins": 0,
            "streak": 0,
            "piglets": [],
            "referrals": 0,
            "claimed_tasks": []
        }

    if "pig" in data[user_id]:
        await update.message.reply_text("😅 You already own a pig!")
        return

    # Set up a full pig object
    new_pig = {
        "birth_date": today,
        "fed_dates": [],
        "pregnant": False,
        "pregnant_date": None
    }

    data[user_id]["pig"] = new_pig
    save_data(data)

    await update.message.reply_text("🎉 You just bought your first pig 🐖!\nTake good care of it and it might give you piglets!")

async def feed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("🐷 You don't own a pig yet! Use /myfarm to get started.")
        return

    player = data[user_id]
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Ensure feed tracking exists
    if "feed" not in player:
        player["feed"] = 0

    if player["feed"] <= 0:
        await update.message.reply_text("❌ You don’t have any feed! Use /buyfeed or /makefeed.")
        return

    pig = player["pig"]
    if today in pig.get("fed_dates", []):
        await update.message.reply_text("🐖 Your pig has already been fed today.")
        return

    # Feed pig
    pig.setdefault("fed_dates", []).append(today)
    player["streak"] = player.get("streak", 0) + 1
    player["feed"] -= 1

    # Reward coins
    coins_earned = 1
    if player["streak"] % 3 == 0:
        coins_earned += 1

    player["coins"] += coins_earned

    save_data(data)

    await update.message.reply_text(
        f"✅ Your pig enjoyed the meal!\n"
        f"🔥 Streak: {player['streak']} days! (+{coins_earned} coins)\n"
        f"💰 Coins: {player['coins']}\n"
        f"📦 Feed left: {player['feed']}"
    )

async def myfarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    data = load_data()

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("😢 You don't have a pig yet. Use /buy to start your farm!")
        return

    user_data = data[user_id]
    pig = user_data["pig"]
    today = datetime.now(timezone.utc).date()

    # Core info
    birth_date = datetime.strptime(pig["birth_date"], "%Y-%m-%d").date()
    age = (today - birth_date).days
    streak = user_data.get("streak", 0)
    coins = user_data.get("coins", 0)
    feed_stock = user_data.get("feed", 0)

    # Mood check
    last_fed = pig["fed_dates"][-1] if pig["fed_dates"] else None
    if last_fed:
        days_missed = (today - datetime.strptime(last_fed, "%Y-%m-%d").date()).days
        if days_missed == 0:
            mood = "😊 Happy"
        elif days_missed == 1:
            mood = "😐 Hungry"
        elif days_missed < 4:
            mood = "😟 Sad"
        else:
            mood = "🏃 Ran Away"
    else:
        mood = "😴 Never Fed"

    # Pregnancy check
    pregnant_msg = ""
    if pig.get("pregnant"):
        preg_date = datetime.strptime(pig["pregnant_date"], "%Y-%m-%d").date()
        days_pregnant = (today - preg_date).days
        if days_pregnant >= 3:
            pregnant_msg = "🍼 Ready to give birth! Use /checkbreed to collect piglets."
        else:
            remaining = 3 - days_pregnant
            pregnant_msg = f"🤰 Pregnant ({days_pregnant} days). {remaining} day(s) until birth."

    # Piglet info
    piglet_count = len(user_data.get("piglets", []))

    await update.message.reply_text(
        f"🏡 Welcome to your farm!\n"
        f"👤 Owner: {user_data.get('username', 'Farmer')}\n"
        f"🐖 Pig Age: {age} days\n"
        f"🔥 Streak: {streak} days\n"
        f"💰 Coins: {coins}\n"
        f"❤️ Mood: {mood}\n"
        f"🐽 Piglets: {piglet_count}\n"
        f"{pregnant_msg}"
        f"📦 Feed Stock: {feed_stock}"
    )

async def breed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = datetime.now(timezone.utc).date()

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("🐷 You don't own any pigs to breed!")
        return

    pig = data[user_id]["pig"]

    # Age Check (changed to 7 days minimum)
    birth_date_str = pig.get("birth_date")
    if not birth_date_str:
        await update.message.reply_text("❌ Pig birth date missing.")
        return

    birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d").date()
    age_days = (today - birth_date).days
    if age_days < 7:
        await update.message.reply_text("🍼 Your pig must be at least 7 days old to breed.")
        return

    # Feeding Check (last 3 days)
    fed_dates = pig.get("fed_dates", [])
    last_3 = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(3)]
    if not all(day in fed_dates for day in last_3):
        await update.message.reply_text("🍽 Your pig must be well-fed (last 3 days) to breed.")
        return

    # Coin Check
    coins = data[user_id].get("coins", 0)
    if coins < 1:
        await update.message.reply_text("💰 You need at least 1 coin to breed.")
        return

    # Check if already pregnant
    if pig.get("pregnant"):
        await update.message.reply_text("🤰 Your pig is already pregnant!")
        return

    # BREED: deduct coin and set pregnancy
    data[user_id]["coins"] -= 1
    pig["pregnant"] = True
    pig["pregnant_date"] = today.strftime("%Y-%m-%d")
    save_data(data)

    await update.message.reply_text("💘 Your pig is now pregnant! Come back in 3 days to check for piglets.")

async def checkbreed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    today = datetime.now(timezone.utc).date()

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("🐷 You don't have a pig yet!")
        return

    pig = data[user_id]["pig"]

    # Check if pig is pregnant
    if not pig.get("pregnant", False):
        await update.message.reply_text("🤰 Your pig is not pregnant right now.")
        return

    # Check how many days since pregnancy
    preg_date = pig.get("pregnant_date")
    if not preg_date:
        await update.message.reply_text("⚠️ Pregnancy date missing.")
        return

    preg_date = datetime.strptime(preg_date, "%Y-%m-%d").date()
    days_pregnant = (today - preg_date).days

    if days_pregnant < 3:
        remaining = 3 - days_pregnant
        await update.message.reply_text(f"🍼 Not yet! Your pig needs {remaining} more day(s) to give birth.")
        return

    # Birth time! Generate piglets
    piglets_count = random.randint(1, 4)  # 1-4 piglets
    piglets = []
    for _ in range(piglets_count):
        roll = random.randint(1, 100)
        if roll <= 5:
            piglets.append({"type": "golden", "age": 0})
        elif roll <= 20:
            piglets.append({"type": "spotted", "age": 0})
        else:
            piglets.append({"type": "normal", "age": 0})

    pig["pregnant"] = False
    pig["pregnant_date"] = None
    data[user_id]["piglets"] = data[user_id].get("piglets", []) + piglets
    save_data(data)

    # Summary message
    summary = {}
    for p in piglets:
        summary[p["type"]] = summary.get(p["type"], 0) + 1

    summary_msg = "\n".join([f"🐽 {typ.title()}: {count}" for typ, count in summary.items()])
    await update.message.reply_text(f"🎉 Your pig gave birth to {piglets_count} piglet(s)!\n{summary_msg}")

async def sellpiglet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data or not data[user_id].get("piglets"):
        await update.message.reply_text("😢 You don't have any piglets to sell.")
        return

    # Show piglets first if no argument provided
    if not context.args:
        piglets = data[user_id]["piglets"]
        msg = "🐽 Your piglets:\n"
        for i, piglet in enumerate(piglets, 1):
            price = 5 if piglet["type"] == "golden" else 3 if piglet["type"] == "spotted" else 1
            msg += f"{i}. {piglet['type'].title()} (worth {price} coins)\n"
        msg += "\nUse: /sellpiglet <number>"
        await update.message.reply_text(msg)
        return

    # Validate input
    try:
        index = int(context.args[0]) - 1
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid number.")
        return

    piglets = data[user_id]["piglets"]

    if index < 0 or index >= len(piglets):
        await update.message.reply_text("❌ Invalid piglet number.")
        return

    # Get piglet and assign value
    piglet = piglets.pop(index)
    pig_type = piglet["type"]

    if pig_type == "golden":
        coins_earned = 5
    elif pig_type == "spotted":
        coins_earned = 3
    else:
        coins_earned = 1

    # Update user coins and save
    data[user_id]["coins"] += coins_earned
    save_data(data)

    await update.message.reply_text(
        f"💰 Sold your {pig_type} piglet for {coins_earned} coin(s)!\n"
        f"🐖 Remaining piglets: {len(piglets)}\n"
        f"💰 Total coins: {data[user_id]['coins']}"
    )

async def market(update: Update, context: ContextTypes.DEFAULT_TYPE):
    offers = refresh_market()
    context.user_data["market"] = offers

    msg = "🛒 Piglet Market — Buy with your coins!\n\n"
    for i, offer in enumerate(offers, 1):
        msg += f"{i}. {offer['type'].title()} piglet — {offer['price']} coins\n"

    msg += "\nUse /buymarket <number> to buy."
    await update.message.reply_text(msg)

async def buymarket(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    coins = user_data.get("coins", 0)
    offers = context.user_data.get("market")

    if not offers:
        await update.message.reply_text("❌ No market offers. Use /market first.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Use: /buymarket <number>")
        return

    try:
        index = int(context.args[0]) - 1
        offer = offers[index]
    except (ValueError, IndexError):
        await update.message.reply_text("⚠️ Invalid selection. Use /market to see options.")
        return

    if coins < offer["price"]:
        await update.message.reply_text("💸 Not enough coins!")
        return

    # Deduct coins & add piglet
    user_data["coins"] -= offer["price"]
    user_data["piglets"] = user_data.get("piglets", [])
    user_data["piglets"].append({"type": offer["type"], "age": 0})

    save_data(data)
    await update.message.reply_text(
        f"✅ You bought a {offer['type']} piglet!\n💰 Coins left: {user_data['coins']}"
    )

async def referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    referral_count = user_data.get("referrals", 0)

    bot_username = context.bot.username
    await update.message.reply_text(
        f"📣 Share this link to earn 5 coins for every friend who joins!\n"
        f"🔗 https://t.me/{bot_username}?start={user_id}\n\n"
        f"👥 Total referrals: {referral_count}"
    )

async def tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})
    claimed_tasks = user_data.get("claimed_tasks", [])
    
    msg = "📋 Daily Piggy Tasks:\n\n"

    for code, task in TASKS.items():
        status = "✅ Completed" if code in claimed_tasks else "🔹 Available"
        msg += f"{status} {task['description']}\n"
        if task["url"]:
            msg += f"🔗 {task['url']}\n"
        reward_text = f"{task['reward']} coins"
        msg += f"🏆 Reward: {reward_text}\n"
        if code not in claimed_tasks:
            msg += f"➡️ Type `/claim {code}` to receive reward\n"
        msg += "\n"
    
    await update.message.reply_text(msg)

async def claim(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user_data = data.get(user_id, {})

    if not context.args:
        await update.message.reply_text("⚠️ Usage: /claim <taskcode>")
        return

    task_code = context.args[0]
    task = TASKS.get(task_code)

    if not task:
        await update.message.reply_text("❌ Invalid task code.")
        return

    # Prevent duplicate claiming
    claimed = user_data.get("claimed_tasks", [])
    if task_code in claimed:
        await update.message.reply_text("🙅 You've already claimed this task.")
        return

    # Reward
    user_data["coins"] = user_data.get("coins", 0) + task["reward"]
    reward_msg = f"💰 You earned {task['reward']} coins!"

    claimed.append(task_code)
    user_data["claimed_tasks"] = claimed
    data[user_id] = user_data
    save_data(data)
    await update.message.reply_text(reward_msg)

# Feed Mills Code 
# Start feed mill
async def startmill(update, context):
    user_id = str(update.effective_user.id)
    data = load_feed_data()
    if user_id in data["mills"]:
        await update.message.reply_text("🏭 You already own a feed mill!")
        return
    data["mills"][user_id] = {
        "level": 0,
        "last_production": "1970-01-01T00:00:00",
        "stock": [],
        "brand": f"Mill #{user_id[-4:]}",
        "emoji": "🏭",
        "slogan": "Quality feed for every pig!",
        "royalty_points": 0,
        "sales": 0
    }
    save_feed_data(data)
    await update.message.reply_text("🎉 Feed mill created at level 0! Use /makefeed to produce feed.")

# Make feed
async def makefeed(update, context):
    user_id = str(update.effective_user.id)
    data = load_feed_data()
    if user_id not in data["mills"]:
        await update.message.reply_text("❌ You don’t own a feed mill. Use /startmill first.")
        return

    mill = data["mills"][user_id]
    mill["stock"] = filter_valid_feed(mill.get("stock", []))
    level = mill["level"]
    cooldown = MILL_LEVELS[level]["cooldown"]

    if not can_produce(mill["last_production"], cooldown):
        await update.message.reply_text("⏳ Your mill is cooling down. Try again later.")
        return

    amount = MILL_LEVELS[level]["amount"]
    ftype = MILL_LEVELS[level].get("type", "normal")

    mill["stock"].append({
        "amount": amount,
        "type": ftype,
        "timestamp": datetime.now().isoformat()
    })
    mill["last_production"] = datetime.now().isoformat()
    save_feed_data(data)
    await update.message.reply_text(f"✅ Produced {amount} units of {ftype} feed!")

# Mill status
async def millstatus(update, context):
    user_id = str(update.effective_user.id)
    data = load_feed_data()
    if user_id not in data["mills"]:
        await update.message.reply_text("❌ You don’t own a feed mill. Use /startmill first.")
        return
    mill = data["mills"][user_id]
    stock = filter_valid_feed(mill["stock"])
    total_feed = sum(item["amount"] for item in stock)
    time_left = "Ready" if can_produce(mill["last_production"], MILL_LEVELS[mill["level"]]["cooldown"]) else "Cooling down"
    await update.message.reply_text(
        f"🏭 {mill['brand']} {mill['emoji']}\n"
        f"📦 Feed Stock: {total_feed} units\n"
        f"🧪 Level: {mill['level']}\n"
        f"⏱️ Cooldown: {time_left}\n"
        f"💬 Slogan: {mill['slogan']}\n"
        f"🏅 Royalty Points: {mill['royalty_points']}\n"
        f"🛒 Total Sales: {mill['sales']}"
    )

# Upgrade mill
async def upgrademill(update, context):
    user_id = str(update.effective_user.id)
    data = load_feed_data()
    players = load_data()
    if user_id not in data["mills"]:
        await update.message.reply_text("❌ You don’t own a feed mill.")
        return

    current_level = data["mills"][user_id]["level"]
    if current_level >= 6:
        await update.message.reply_text("🔝 Your feed mill is already maxed out!")
        return

    cost = [0, 10, 20, 30, 50, 75][current_level + 1]
    if players[user_id]["coins"] < cost:
        await update.message.reply_text(f"💰 You need {cost} coins to upgrade to level {current_level + 1}.")
        return

    players[user_id]["coins"] -= cost
    data["mills"][user_id]["level"] += 1
    save_data(players)
    save_feed_data(data)
    await update.message.reply_text(f"🔧 Upgraded to level {current_level + 1}!")

# Rush mill
async def rushmill(update, context):
    user_id = str(update.effective_user.id)
    data = load_feed_data()
    players = load_data()
    if user_id not in data["mills"]:
        await update.message.reply_text("❌ You don’t own a feed mill.")
        return

    if players[user_id].get("ton_balance", 0) < 1:
        await update.message.reply_text("💎 You need at least 1 TON to rush production!")
        return

    data["mills"][user_id]["last_production"] = "1970-01-01T00:00:00"
    players[user_id]["ton_balance"] -= 1
    save_data(players)
    save_feed_data(data)
    await update.message.reply_text("⚡ Rush successful! You may now /makefeed immediately.")

# Sell feed
async def sellfeed(update, context):
    user_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /sellfeed amount price")
        return

    try:
        amount = int(args[0])
        price = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Please enter valid numbers.")
        return

    data = load_feed_data()
    if user_id not in data["mills"]:
        await update.message.reply_text("❌ You don’t own a feed mill.")
        return

    stock = filter_valid_feed(data["mills"][user_id]["stock"])
    total_feed = sum(item["amount"] for item in stock)
    if total_feed < amount:
        await update.message.reply_text("❌ Not enough feed to sell.")
        return

    # Deduct feed from stock
    deducted = 0
    new_stock = []
    for batch in stock:
        if deducted >= amount:
            new_stock.append(batch)
        elif deducted + batch["amount"] <= amount:
            deducted += batch["amount"]
        else:
            remain = batch["amount"] - (amount - deducted)
            new_stock.append({"amount": remain, "type": batch["type"], "timestamp": batch["timestamp"]})
            deducted = amount

    data["mills"][user_id]["stock"] = new_stock

    # Add to market
    market_entry = {
        "seller_id": user_id,
        "amount": amount,
        "price": price,
        "type": "premium" if data["mills"][user_id]["level"] == 6 else "normal",
        "timestamp": datetime.now().isoformat(),
        "brand": data["mills"][user_id]["brand"],
        "emoji": data["mills"][user_id]["emoji"],
        "slogan": data["mills"][user_id]["slogan"],
        "sales": 0
    }
    data["market"].append(market_entry)
    save_feed_data(data)
    await update.message.reply_text(f"📦 Listed {amount} feed for {price} coins each.")

# View feed market
async def feedmarket(update, context):
    data = load_feed_data()
    lines = []
    for i, offer in enumerate(data["market"], 1):
        lines.append(f"{i}. {offer['emoji']} {offer['brand']} — {offer['amount']} feed @ {offer['price']} coins\n"
                     f"   “{offer['slogan']}” | Sales: {offer['sales']}")
    if not lines:
        await update.message.reply_text("📭 No feed available in the market.")
        return
    await update.message.reply_text("📦 FEED MARKET:\n" + "\n".join(lines))

# Buy feed

#update userid with millions
def find_user_id_by_mill(mill_id):
    feed_data = load_feed_data()
    for user_id, mill in feed_data["mills"].items():
        if str(user_id)[-4:] == str(mill_id):
            return user_id
    return None
    
#async def buyfeed(update, context):
async def buyfeed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    feed_data = load_feed_data()

    if user_id not in data:
        await update.message.reply_text("🐷 You don't own a pig yet! Use /myfarm first.")
        return

    if len(context.args) != 2:
        await update.message.reply_text("Usage: /buyfeed mill_id amount")
        return

    mill_id, amount = context.args
    amount = int(amount)

    # 🔍 Find actual user_id from mill_id
    seller_id = find_user_id_by_mill(mill_id)

    if not seller_id or seller_id not in feed_data["mills"] or feed_data["mills"][seller_id]["feed_stock"] < amount:

    #seller_mill = feed_data[seller_id]
    seller_mill = feed_data["mills"][seller_id]
    total_price = amount * seller_mill["price"]

    if data[user_id]["coins"] < total_price:
        await update.message.reply_text("💰 You don't have enough coins to buy this feed.")
        return

    # Do the trade
    data[user_id]["feed"] = data[user_id].get("feed", 0) + amount
    data[user_id]["coins"] -= total_price

    feed_data["mills"][seller_id]["feed_stock"] -= amount
    feed_data["mills"][seller_id]["sales"] += amount
    feed_data["mills"][seller_id]["royalty_points"] += amount
    data[seller_id]["coins"] += total_price

    save_data(data)
    save_feed_data(feed_data)

    await update.message.reply_text(f"✅ Purchased {amount} feed from Mill #{mill_id} for {total_price} coins.")

#updated milltofarm
async def milltofarm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)

    data = load_data()
    feed_data = load_feed_data()

    if user_id not in data:
        await update.message.reply_text("🐷 You don't own a pig yet. Use /myfarm to get started.")
        return

    if user_id not in feed_data["mills"]:
        await update.message.reply_text("🏭 You don't own a feed mill yet. Use /startmill to begin.")
        return

    if len(context.args) != 1 or not context.args[0].isdigit():
        await update.message.reply_text("Usage: /milltofarm <amount>")
        return

    amount = int(context.args[0])

    if feed_data["mills"][user_id]["feed_stock"] < amount:
        await update.message.reply_text("❌ Not enough feed in your mill to transfer.")
        return

    # Transfer
    feed_data["mills"][user_id]["feed_stock"] -= amount
    data[user_id]["feed"] = data[user_id].get("feed", 0) + amount

    save_feed_data(feed_data)
    save_data(data)

    await update.message.reply_text(
        f"✅ Moved {amount} feed from your Mill to your Farm.\n"
        f"📦 Farm Feed: {data[user_id]['feed']} units\n"
        f"🏭 Mill Feed: {feed_data['mills'][user_id]['feed_stock']} units"
        )

# Brand stats
async def brandstats(update, context):
    user_id = str(update.effective_user.id)
    data = load_feed_data()
    if user_id not in data["mills"]:
        await update.message.reply_text("❌ You don’t own a feed mill.")
        return

    mill = data["mills"][user_id]
    await update.message.reply_text(
        f"📊 {mill['brand']} {mill['emoji']}\n"
        f"🧪 Level: {mill['level']}\n"
        f"📦 Feed stock: {sum(item['amount'] for item in mill['stock'])}\n"
        f"🏅 Royalty Points: {mill['royalty_points']}\n"
        f"🛒 Total Sales: {mill['sales']}"
    )

# Top brands leaderboard
async def topbrands(update, context):
    data = load_feed_data()
    ranked = sorted(data["mills"].items(), key=lambda x: x[1].get("royalty_points", 0), reverse=True)
    lines = []
    for i, (uid, mill) in enumerate(ranked[:5], 1):
        lines.append(f"{i}. {mill['brand']} {mill['emoji']} — {mill['royalty_points']} RP, {mill['sales']} sales")
    if not lines:
        await update.message.reply_text("📭 No branded mills ranked yet.")
    else:
        await update.message.reply_text("🏆 Top Feed Brands:\n" + "\n".join(lines))

# 

#pork plants 


async def startplant(update, context):
    user_id = str(update.effective_user.id)
    data = load_data()

    if "plant" in data.get(user_id, {}):
        await update.message.reply_text("🏭 You already own a pork plant!")
        return

    if data[user_id].get("ton_balance", 0) < 1:
        await update.message.reply_text("💎 You need 1 TON to start your pork plant business.")
        return

    data[user_id]["ton_balance"] -= 1  # Deduct 1 TON

    data[user_id]["plant"] = {
        "level": 0,
        "last_meat": "1970-01-01",
        "last_sausage": "1970-01-01",
        "last_bacon": "1970-01-01",
        "processed": 0,
        "ton_earned": 0
    }

    save_data(data)
    await update.message.reply_text("🎉 Welcome to the Sausage Syndicate™! Your pork plant is open for business. 🏭")

async def process_pig(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    feed_data = load_feed_data()

    if user_id not in data:
        await update.message.reply_text("🐷 You don't have a farm yet! Use /myfarm first.")
        return

    user = data[user_id]
    mill = feed_data.get(user_id, {})
    plant_level = mill.get("plant_level", 0)
    pigs = user.get("piglets", [])

    if not pigs:
        await update.message.reply_text("🐽 You have no piglets to process!")
        return

    eligible_pig = None
    reward_ton = 0
    product = ""
    today = datetime.now().strftime("%Y-%m-%d")

    for pig in pigs:
        age = pig.get("age", 0)
        pig_type = pig.get("type", "normal")

        # Determine product based on eligibility + level
        if "bacon" in PLANT_LEVELS[plant_level]["products"]:
            if pig_type == "golden" and age >= 10 and not has_processed_today(user, "bacon"):
                product = "bacon"
                eligible_pig = pig
                break
        if "sausage" in PLANT_LEVELS[plant_level]["products"]:
            if pig_type in ["golden", "spotted"] and not has_processed_today(user, "sausage"):
                product = "sausage"
                eligible_pig = pig
                break
        if "meat" in PLANT_LEVELS[plant_level]["products"]:
            if age >= 3 and not has_processed_today(user, "meat"):
                product = "meat"
                eligible_pig = pig
                break

    if not eligible_pig:
        await update.message.reply_text("⏱️ You’ve already processed a pig today or no piglets meet the criteria.")
        return

    # Reward TON using PLANT_LEVELS table
    reward_ton = PLANT_LEVELS[plant_level]["reward"][product]
    user["ton_balance"] = user.get("ton_balance", 0) + reward_ton
    user["piglets"].remove(eligible_pig)
    mark_processed_today(user, product)
    save_data(data)

    await update.message.reply_text(
        f"✅ Processed one piglet into {product.upper()}!\n💰 Earned {reward_ton} TON.\nCome back tomorrow to process again."
    )

async def plantstatus(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    feed_data = load_feed_data()

    user_plant = feed_data.get(user_id)
    if not user_plant or "plant_level" not in user_plant:
        await update.message.reply_text("❌ You don’t have a pork plant yet. Use /startplant to begin.")
        return

    level = user_plant["plant_level"]
    unlocked = PLANT_LEVELS[level]["products"]
    unlocked_emojis = {
        "meat": "🍖",
        "sausage": "🌭",
        "bacon": "🥓"
    }
    unlocked_display = ", ".join([unlocked_emojis[p] + " " + p.capitalize() for p in unlocked])

    next_level = level + 1 if level < 6 else None
    next_unlock = ""
    if next_level and next_level in PLANT_LEVELS:
        next_products = PLANT_LEVELS[next_level]["products"]
        new_unlocks = list(set(next_products) - set(unlocked))
        if new_unlocks:
            next_unlock = f"🔐 Next unlock at level {next_level}: " + ", ".join([unlocked_emojis[p] + " " + p.capitalize() for p in new_unlocks])
    else:
        next_unlock = "✅ You've unlocked all pork products!"

    message = (
        f"🏭 Pork Plant Status\n"
        f"Level: {level}\n"
        f"🔓 Unlocked: {unlocked_display}\n"
        f"{next_unlock}\n"
        f"💰 Daily limit: 1 process per product\n"
    )

    await update.message.reply_text(message)

async def upgradeplant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    feed_data = load_feed_data()

    user = data.get(user_id)
    plant = feed_data.get(user_id)

    if not user or not plant:
        await update.message.reply_text("❌ You need a farm and pork plant first.")
        return

    level = plant.get("plant_level", 0)
    if level >= 6:
        await update.message.reply_text("✅ Your plant is already at max level (6)!")
        return

    ton = user.get("ton_balance", 0)
    if ton < 1:
        await update.message.reply_text("❌ You need at least 1 TON to upgrade your plant.")
        return

    # Upgrade
    user["ton_balance"] = round(ton - 1, 2)
    plant["plant_level"] = level + 1

    # Log it
    if "ton_log" not in user:
        user["ton_log"] = []
    user["ton_log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "upgradeplant",
        "amount": -1
    })

    save_data(data)
    save_feed_data(feed_data)

    unlocked = PLANT_LEVELS[level + 1]["products"]
    emojis = {"meat": "🍖", "sausage": "🌭", "bacon": "🥓"}
    unlocked_str = ", ".join([emojis[p] + " " + p.capitalize() for p in unlocked])

    await update.message.reply_text(
        f"🎉 Pork Plant upgraded to Level {level + 1}!\n"
        f"🔓 New unlocks: {unlocked_str}\n"
        f"💎 Remaining TON: {user['ton_balance']:.2f}"
    )
#
# TON #Economy

#ingame

async def wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    user = data.get(user_id)

    if not user:
        await update.message.reply_text("🐷 You don't have a farm yet. Use /myfarm to begin.")
        return

    ton = user.get("ton_balance", 0)
    wallet = user.get("ton_wallet", "❌ Not set")

    await update.message.reply_text(
        f"💼 Your TON Wallet\nBalance: {ton:.2f} TON\nWallet: {wallet}\n\n"
        "Use /claimton to request payout or /exchangeton <coins> to convert coins into TON.\n"
        "Set your wallet with: /setwallet YOUR_TON_ADDRESS"
    )
#player TON wallet 

async def setwallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ You don’t have a farm yet. Use /start first.")
        return

    if not context.args:
        await update.message.reply_text("📥 Usage: /setwallet YOUR_TON_ADDRESS")
        return

    address = context.args[0]
    if not address.startswith("EQ") or len(address) < 20:
        await update.message.reply_text("❌ Invalid TON address.")
        return

    data[user_id]["ton_wallet"] = address
    save_data(data)

    await update.message.reply_text(f"✅ Wallet address saved!\n{address}")

# exchange coins for ton 🪙 💰 

async def exchangeton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("🐽 You need a farm first! Use /start.")
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("📥 Usage: /exchangeton <coin_amount>")
        return

    coins_to_convert = int(context.args[0])
    user = data[user_id]
    user_coins = user.get("coins", 0)

    if coins_to_convert > user_coins:
        await update.message.reply_text("❌ Not enough coins.")
        return

    ton_earned = coins_to_convert / EXCHANGE_RATE
    user["coins"] -= coins_to_convert
    user["ton_balance"] = user.get("ton_balance", 0) + ton_earned

    # log exchange
    if "ton_log" not in user:
        user["ton_log"] = []
    user["ton_log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": f"exchange:{coins_to_convert}coins",
        "amount": ton_earned
    })

    save_data(data)
    await update.message.reply_text(
        f"🔄 Exchanged {coins_to_convert} coins for {ton_earned:.2f} TON.\n"
        f"💼 New TON balance: {user['ton_balance']:.2f}"
    )


ADMIN_ID = "6382166583"  # replace with your Telegram ID

async def claimton(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("🐽 You need a farm to claim TON.")
        return

    user = data[user_id]
    ton = user.get("ton_balance", 0)
    wallet = user.get("ton_wallet")

    if not wallet:
        await update.message.reply_text("❌ Set your wallet first using /setwallet.")
        return

    if ton < 0.5:
        await update.message.reply_text("❌ You need at least 0.5 TON to claim.")
        return

    message = (
        f"💸 Claim Request Received!\n"
        f"👤 {user.get('username', 'Unknown')} ({user_id})\n"
        f"💎 Amount: {ton:.2f} TON\n"
        f"🏦 Wallet: {wallet}"
    )

    # Notify admin via private message
    await context.bot.send_message(chat_id=ADMIN_ID, text=message)

    await update.message.reply_text(
        "✅ Your TON claim request has been sent to admin.\nPlease wait for manual confirmation."
    )

ADMIN_IDS = ["6382166583"]  # your admin ID(s)

async def tonlog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You're not authorized to use this command.")
        return

    data = load_data()
    ton_summary = []

    for uid, info in data.items():
        ton = info.get("ton_balance", 0)
        name = info.get("username", "Unknown")
        if ton > 0:
            ton_summary.append((ton, name, uid))

    top_users = sorted(ton_summary, reverse=True)[:10]
    if not top_users:
        await update.message.reply_text("📭 No users with TON balance found.")
        return

    msg = "📊 Top TON Balances:\n"
    for ton, name, uid in top_users:
        msg += f"👤 {name} ({uid}) — 💎 {ton:.2f} TON\n"

    await update.message.reply_text(msg)

async def payuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You're not authorized.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("📥 Usage: /payuser <user_id> <amount>")
        return

    uid = context.args[0]
    try:
        amount = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")
        return

    data = load_data()
    user = data.get(uid)
    if not user:
        await update.message.reply_text("❌ User not found.")
        return

    current_balance = user.get("ton_balance", 0)
    if amount > current_balance:
        await update.message.reply_text("❌ Not enough TON balance.")
        return

    user["ton_balance"] = round(current_balance - amount, 2)

    # Optional: Add log entry
    if "ton_log" not in user:
        user["ton_log"] = []
    user["ton_log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "admin:cashout",
        "amount": -amount
    })

    save_data(data)
    await update.message.reply_text(f"✅ Deducted {amount} TON from {uid}.\n💼 New balance: {user['ton_balance']:.2f}")


async def cashout(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 You're not authorized.")
        return

    if not context.args:
        await update.message.reply_text("📥 Usage: /cashout <user_id>")
        return

    uid = context.args[0]
    data = load_data()
    user = data.get(uid)
    if not user:
        await update.message.reply_text("❌ User not found.")
        return

    old_balance = user.get("ton_balance", 0)
    user["ton_balance"] = 0

    if "ton_log" not in user:
        user["ton_log"] = []
    user["ton_log"].append({
        "date": datetime.now().strftime("%Y-%m-%d"),
        "source": "admin:fullcashout",
        "amount": -old_balance
    })

    save_data(data)
    await update.message.reply_text(f"💸 Full cashout for {uid} completed.\nDeducted {old_balance:.2f} TON.")

#


# Main application
if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("feed", feed))
    app.add_handler(CommandHandler("myfarm", myfarm))
    app.add_handler(CommandHandler("breed", breed))
    app.add_handler(CommandHandler("checkbreed", checkbreed))
    app.add_handler(CommandHandler("sellpiglet", sellpiglet))
    app.add_handler(CommandHandler("market", market))
    app.add_handler(CommandHandler("buymarket", buymarket))
    app.add_handler(CommandHandler("referral", referral))
    app.add_handler(CommandHandler("tasks", tasks))
    app.add_handler(CommandHandler("claim", claim))
    app.add_handler(CommandHandler("startmill", startmill))
    app.add_handler(CommandHandler("makefeed", makefeed))
    app.add_handler(CommandHandler("millstatus", millstatus))
    app.add_handler(CommandHandler("upgrademill", upgrademill))
    app.add_handler(CommandHandler("rushmill", rushmill))
    app.add_handler(CommandHandler("sellfeed", sellfeed))
    app.add_handler(CommandHandler("feedmarket", feedmarket))
    app.add_handler(CommandHandler("buyfeed", buyfeed))
    app.add_handler(CommandHandler("brandstats", brandstats))
    app.add_handler(CommandHandler("topbrands", topbrands))
    app.add_handler(CommandHandler("startplant", startplant))
    app.add_handler(CommandHandler("processpig", process_pig))
    app.add_handler(CommandHandler("plantstatus", plantstatus))
    app.add_handler(CommandHandler("upgradeplant", upgradeplant))
    app.add_handler(CommandHandler("wallet", wallet))
    app.add_handler(CommandHandler("setwallet", setwallet))
    app.add_handler(CommandHandler("exchangeton", exchangeton))
    app.add_handler(CommandHandler("claimton",claimton))
    app.add_handler(CommandHandler("tonlog", tonlog))
    app.add_handler(CommandHandler("payuser", payuser))
    app.add_handler(CommandHandler("cashout", cashout))
    app.add_handler(CommandHandler("milltofarm", milltofarm))
    
    print("🐷 Bot is running...")
    app.run_polling()
