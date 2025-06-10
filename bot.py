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
    today = datetime.now(timezone.utc).date()
    today_str = today.strftime("%Y-%m-%d")

    if user_id not in data or "pig" not in data[user_id]:
        await update.message.reply_text("🐷 You don't have a pig! Use /buy to start.")
        return

    pig = data[user_id]["pig"]
    fed_dates = pig.get("fed_dates", [])

    # Check if already fed today
    if today_str in fed_dates:
        await update.message.reply_text("🍽 You already fed your pig today!")
        return

    # Append today's feed date
    fed_dates.append(today_str)
    pig["fed_dates"] = fed_dates

    # Streak logic (based on consecutive days)
    streak = data[user_id].get("streak", 0)
    yesterday = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    
    if len(fed_dates) == 1 or yesterday in fed_dates:
        streak += 1
        data[user_id]["coins"] = data[user_id].get("coins", 0) + 1
        streak_msg = f"🔥 Streak: {streak} days! (+1 coin)"
    else:
        streak = 1
        streak_msg = "🍽 Pig fed! Streak restarted."

    data[user_id]["streak"] = streak
    save_data(data)

    await update.message.reply_text(
        f"✅ Your pig enjoyed the meal!\n{streak_msg}\n💰 Coins: {data[user_id]['coins']}"
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
async def buyfeed(update, context):
    user_id = str(update.effective_user.id)
    args = context.args
    if len(args) != 2:
        await update.message.reply_text("Usage: /buyfeed seller_id amount")
        return

    seller_id = args[0]
    try:
        amount = int(args[1])
    except ValueError:
        await update.message.reply_text("❌ Invalid amount.")
        return

    feed_data = load_feed_data()
    players = load_data()
    buyer = players.get(user_id)
    seller = feed_data["mills"].get(seller_id)
    if not buyer or not seller:
        await update.message.reply_text("❌ Invalid buyer or seller.")
        return

    for offer in feed_data["market"]:
        if offer["seller_id"] == seller_id and offer["amount"] >= amount:
            total_price = amount * offer["price"]
            if buyer["coins"] < total_price:
                await update.message.reply_text("❌ Not enough coins.")
                return

            offer["amount"] -= amount
            offer["sales"] += amount
            feed_data["mills"][seller_id]["royalty_points"] += amount
            feed_data["mills"][seller_id]["sales"] += amount
            buyer["coins"] -= total_price
            players[seller_id]["coins"] += total_price

            save_feed_data(feed_data)
            save_data(players)
            await update.message.reply_text(f"✅ Purchased {amount} feed from {offer['brand']}.")
            return

    await update.message.reply_text("❌ Offer not found or insufficient stock.")

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
   
    print("🐷 Bot is running...")
    app.run_polling()