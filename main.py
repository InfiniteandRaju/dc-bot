import discord
from discord.ext import commands, tasks
from discord.ui import View, Button, Select, Modal, TextInput
import asyncio
import json
import os
import datetime
import random
from typing import Optional

# Load configuration
def load_config():
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Default config
        default_config = {
            "channel_ids": {
                "minecraft_plans": 123456789,
                "vps_plans": 123456790,
                "developer_plans": 123456791,
                "domain_plans": 123456792,
                "booster_plans": 123456793,
                "youtuber_plans": 123456794,
                "partnership": 123456795,
                "ticket_category": 123456796,
                "log_channel": 123456797,
                "giveaway_channel": 123456798
            }
        }
        with open('config.json', 'w') as f:
            json.dump(default_config, f, indent=4)
        return default_config

config = load_config()
CHANNELS = config["channel_ids"]

# Bot configuration
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# Data storage
GIVEAWAY_FILE = "giveaways.json"

# Plan configurations
PLANS = {
    "minecraft": {
        "Basic": {"price": "$2", "ram": "4GB", "cpu": "400%", "ssd": "Fast Storage"},
        "Standard": {"price": "$4", "ram": "8GB", "cpu": "500%", "ssd": "Fast Storage"},
        "Advanced": {"price": "$6", "ram": "12GB", "cpu": "600%", "ssd": "Fast NVMe"},
        "Pro": {"price": "$10", "ram": "16GB", "cpu": "700%", "ssd": "Fast NVMe"},
        "Ultra": {"price": "$12", "ram": "24GB", "cpu": "800%", "ssd": "Ultra NVMe"},
        "Mega": {"price": "$16", "ram": "32GB", "cpu": "1000%", "ssd": "Ultra NVMe"}
    },
    "vps": {
        "Starter VPS": {"price": "$5", "ram": "2GB", "cpu": "2 vCPU", "storage": "40GB SSD", "bandwidth": "1TB"},
        "Business VPS": {"price": "$10", "ram": "4GB", "cpu": "4 vCPU", "storage": "80GB NVMe", "bandwidth": "2TB"},
        "Pro VPS": {"price": "$20", "ram": "8GB", "cpu": "6 vCPU", "storage": "160GB NVMe", "bandwidth": "4TB"},
        "Enterprise VPS": {"price": "$40", "ram": "16GB", "cpu": "8 vCPU", "storage": "320GB NVMe", "bandwidth": "Unlimited"}
    },
    "developer": {
        "Basic Dev": {"price": "$3", "ram": "2GB", "storage": "20GB", "features": "Database + Domain"},
        "Pro Dev": {"price": "$8", "ram": "4GB", "storage": "50GB", "features": "Premium Support + SSL"},
        "Team Dev": {"price": "$15", "ram": "8GB", "storage": "100GB", "features": "Multiple Projects + CI/CD"}
    },
    "domain": {
        ".com": {"price": "$10/year", "transfer": "Free", "features": "Free Privacy Protection + Email"},
        ".net": {"price": "$12/year", "transfer": "Free", "features": "Free DNS Management + SSL"},
        ".org": {"price": "$8/year", "transfer": "Free", "features": "Free Email Forwarding + Privacy"},
        ".io": {"price": "$30/year", "transfer": "$10", "features": "Premium Domain + Business Email"}
    },
    "booster": {
        "Server Booster": {"price": "Free", "benefits": "Discord Perks + Priority Support"},
        "Premium Booster": {"price": "$5/month", "benefits": "Enhanced Features + VIP Role"},
        "Ultra Booster": {"price": "$10/month", "benefits": "All Features + Custom Emojis"}
    },
    "youtuber": {
        "Starter Pack": {"price": "Free", "subs": "1K+", "benefits": "Basic Promotion + Shoutout"},
        "Growth Pack": {"price": "Custom", "subs": "5K+", "benefits": "Featured Promotion + Partnership"},
        "Pro Pack": {"price": "Sponsored", "subs": "10K+", "benefits": "Full Sponsorship + Revenue Share"}
    }
}

# Giveaway system
class GiveawaySystem:
    def __init__(self):
        self.giveaways = self.load_giveaways()
    
    def load_giveaways(self):
        try:
            with open(GIVEAWAY_FILE, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    def save_giveaways(self):
        with open(GIVEAWAY_FILE, 'w') as f:
            json.dump(self.giveaways, f, indent=4)
    
    def create_giveaway(self, message_id, channel_id, prize, winners, duration, host_id, requirements=None):
        end_time = datetime.datetime.now() + datetime.timedelta(seconds=duration)
        self.giveaways[str(message_id)] = {
            "channel_id": channel_id,
            "prize": prize,
            "winners": winners,
            "end_time": end_time.isoformat(),
            "host_id": host_id,
            "participants": [],
            "requirements": requirements or {},
            "ended": False
        }
        self.save_giveaways()
    
    def end_giveaway(self, message_id):
        if str(message_id) in self.giveaways:
            self.giveaways[str(message_id)]["ended"] = True
            self.save_giveaways()
    
    def delete_giveaway(self, message_id):
        if str(message_id) in self.giveaways:
            del self.giveaways[str(message_id)]
            self.save_giveaways()

giveaway_system = GiveawaySystem()

class GiveawayView(View):
    def __init__(self, giveaway_id, requirements=None):
        super().__init__(timeout=None)
        self.giveaway_id = giveaway_id
        self.requirements = requirements or {}
    
    @discord.ui.button(label="Enter Giveaway 🎉", style=discord.ButtonStyle.success, custom_id="enter_giveaway")
    async def enter_giveaway(self, button, interaction):
        giveaway = giveaway_system.giveaways.get(self.giveaway_id)
        if not giveaway:
            await interaction.response.send_message("This giveaway has ended!", ephemeral=True)
            return
        
        if interaction.user.id in giveaway["participants"]:
            await interaction.response.send_message("You've already entered this giveaway!", ephemeral=True)
            return
        
        # Check requirements
        if self.requirements.get("boost_server") and not interaction.user.premium_since:
            await interaction.response.send_message("❌ You need to boost this server to enter!", ephemeral=True)
            return
        
        giveaway["participants"].append(interaction.user.id)
        giveaway_system.save_giveaways()
        
        await interaction.response.send_message("✅ You've successfully entered the giveaway! Good luck! 🎉", ephemeral=True)

class CreateGiveawayModal(Modal):
    def __init__(self):
        super().__init__(title="Create New Giveaway")
        
        self.prize = TextInput(
            label="Prize",
            placeholder="e.g., 1 Month Free Minecraft Hosting",
            required=True,
            max_length=100
        )
        
        self.winners = TextInput(
            label="Number of Winners",
            placeholder="e.g., 1",
            required=True,
            max_length=2
        )
        
        self.duration = TextInput(
            label="Duration (minutes)",
            placeholder="e.g., 60",
            required=True,
            max_length=4
        )
        
        self.requirements = TextInput(
            label="Requirements (optional)",
            placeholder="e.g., Server Boost, Level 5, etc.",
            required=False,
            max_length=100
        )
        
        self.add_item(self.prize)
        self.add_item(self.winners)
        self.add_item(self.duration)
        self.add_item(self.requirements)
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            winners = int(self.winners.value)
            duration = int(self.duration.value) * 60  # Convert to seconds
        except ValueError:
            await interaction.response.send_message("❌ Please enter valid numbers for winners and duration!", ephemeral=True)
            return
        
        # Parse requirements
        requirements = {}
        req_text = self.requirements.value.lower()
        if "boost" in req_text:
            requirements["boost_server"] = True
        
        # Create giveaway embed
        embed = discord.Embed(
            title="🎉 **GIVEAWAY** 🎉",
            description=f"**Prize:** {self.prize.value}\n"
                       f"**Winners:** {winners}\n"
                       f"**Hosted by:** {interaction.user.mention}\n"
                       f"**Ends:** <t:{int((datetime.datetime.now() + datetime.timedelta(seconds=duration)).timestamp())}:R>",
            color=0xffd700
        )
        
        if requirements:
            req_text = ""
            if requirements.get("boost_server"):
                req_text += "• Server Boost Required\n"
            embed.add_field(name="📋 Requirements", value=req_text, inline=False)
        
        embed.set_footer(text="Click the button below to enter!")
        
        view = GiveawayView("temp", requirements)
        message = await interaction.channel.send(embed=embed, view=view)
        
        # Store giveaway
        giveaway_system.create_giveaway(
            message.id,
            interaction.channel.id,
            self.prize.value,
            winners,
            duration,
            interaction.user.id,
            requirements
        )
        
        # Update view with actual giveaway ID
        view.giveaway_id = str(message.id)
        
        await interaction.response.send_message("✅ Giveaway created successfully!", ephemeral=True)

class GiveawayManagementView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Create Giveaway", style=discord.ButtonStyle.primary, emoji="🎉")
    async def create_giveaway(self, button, interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need manage messages permission to create giveaways!", ephemeral=True)
            return
        
        modal = CreateGiveawayModal()
        await interaction.response.send_modal(modal)
    
    @discord.ui.button(label="Reroll Giveaway", style=discord.ButtonStyle.secondary, emoji="🔁")
    async def reroll_giveaway(self, button, interaction):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ You need manage messages permission to reroll giveaways!", ephemeral=True)
            return
        
        await interaction.response.send_message("🔁 Use `!gend <message_id>` to end a giveaway and pick winners!", ephemeral=True)

class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="Select an option...",
        options=[
            discord.SelectOption(label="Buy VPS/Server", emoji="💎", value="buy"),
            discord.SelectOption(label="Claim Free Server", emoji="🎁", value="free"),
            discord.SelectOption(label="Partnership", emoji="🤝", value="partnership"),
            discord.SelectOption(label="Support", emoji="🛠️", value="support"),
            discord.SelectOption(label="Giveaways", emoji="🎉", value="giveaways")
        ]
    )
    async def select_callback(self, select, interaction):
        await interaction.response.defer()
        await create_ticket(interaction, select.values[0])

async def create_ticket(interaction, ticket_type):
    category = bot.get_channel(CHANNELS["ticket_category"])
    if not category:
        await interaction.followup.send("❌ Ticket category not found! Please contact admin.", ephemeral=True)
        return
    
    # Create ticket channel
    overwrites = {
        interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
        bot.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
    }
    
    ticket_channel = await category.create_text_channel(
        name=f"{ticket_type}-{interaction.user.name}",
        overwrites=overwrites
    )
    
    # Send initial message based on ticket type
    if ticket_type == "buy":
        embed = discord.Embed(
            title="💎 Purchase Ticket",
            description="Please select the type of service you want to purchase:",
            color=0x00ff00
        )
        view = PurchaseView()
        await ticket_channel.send(embed=embed, view=view)
        
    elif ticket_type == "free":
        embed = discord.Embed(
            title="🎁 Free Server Claim",
            description="Please answer the following questions:\n\n1. What will you use the server for?\n2. How long do you need it?\n3. Any specific requirements?\n4. Why should we choose you?",
            color=0xffd700
        )
        await ticket_channel.send(embed=embed)
        
    elif ticket_type == "partnership":
        embed = discord.Embed(
            title="🤝 Partnership Application",
            description="**Please provide the following information:**\n\n"
                       "1. **Organization/Channel Name**\n"
                       "2. **Platform** (YouTube/Twitch/Server/etc.)\n"
                       "3. **Statistics** (Subscribers/Viewers/Player Count)\n"
                       "4. **Partnership Proposal**\n"
                       "5. **How can we help each other?**\n\n"
                       "*Our team will review your application shortly.*",
            color=0x00ff00
        )
        await ticket_channel.send(embed=embed)
        
    elif ticket_type == "support":
        embed = discord.Embed(
            title="🛠️ Support Ticket",
            description="Please describe your issue in detail:\n\n1. What service are you using?\n2. What problem are you experiencing?\n3. When did this issue start?\n4. Any error messages?",
            color=0x3498db
        )
        await ticket_channel.send(embed=embed)
    
    elif ticket_type == "giveaways":
        embed = discord.Embed(
            title="🎉 Giveaway Support",
            description="**How can we help you with giveaways?**\n\n"
                       "1. **Issue with entering a giveaway**\n"
                       "2. **Haven't received giveaway prize**\n"
                       "3. **Question about giveaway rules**\n"
                       "4. **Report giveaway issue**\n\n"
                       "Please describe your issue below:",
            color=0xffd700
        )
        await ticket_channel.send(embed=embed)
    
    await interaction.followup.send(f"Ticket created! {ticket_channel.mention}", ephemeral=True)

class PurchaseView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="Choose service type...",
        options=[
            discord.SelectOption(label="Minecraft Plans", emoji="🪐", value="minecraft"),
            discord.SelectOption(label="VPS Plans", emoji="💻", value="vps"),
            discord.SelectOption(label="Developer Plans", emoji="👨‍💻", value="developer"),
            discord.SelectOption(label="Domain Plans", emoji="🌐", value="domain"),
            discord.SelectOption(label="Booster Plans", emoji="🚀", value="booster"),
            discord.SelectOption(label="YouTuber Plans", emoji="📹", value="youtuber")
        ]
    )
    async def select_callback(self, select, interaction):
        await interaction.response.defer()
        await send_plan_details(interaction, select.values[0])

async def send_plan_details(interaction, plan_type):
    channel_map = {
        "minecraft": CHANNELS["minecraft_plans"],
        "vps": CHANNELS["vps_plans"],
        "developer": CHANNELS["developer_plans"],
        "domain": CHANNELS["domain_plans"],
        "booster": CHANNELS["booster_plans"],
        "youtuber": CHANNELS["youtuber_plans"]
    }
    
    channel_id = channel_map.get(plan_type)
    if not channel_id:
        await interaction.followup.send("❌ Channel not configured!", ephemeral=True)
        return
    
    channel = bot.get_channel(channel_id)
    if not channel:
        await interaction.followup.send("❌ Channel not found!", ephemeral=True)
        return
    
    if plan_type == "minecraft":
        embed = discord.Embed(
            title="💎・Premium Minecraft Hosting Plans",
            description="✨ Get **high-performance Minecraft servers** at **super affordable prices** 💠\n💾 SSD / NVMe Storage ｜ ⚙️ Powerful CPU ｜ 💻 Full Panel ｜ 🧠 DDoS Protection\n",
            color=0x5865F2
        )
        
        for plan_name, details in PLANS["minecraft"].items():
            embed.add_field(
                name=f"💎 **{plan_name} Plan** — {details['price']} / Month",
                value=f"🐏 RAM - **{details['ram']}**\n💾 SSD - **{details['ssd']}**\n⚡ CPU - **{details['cpu']}**",
                inline=False
            )
        
        embed.add_field(
            name="⚙️ All Plans Include:",
            value="> 🌐 Free Subdomain\n> 🧠 DDoS Protection\n> 💻 Full Panel Access\n> 🧾 Permanent Server\n> 🕓 24/7 Uptime\n> 🎯 Fast Setup\n> 🧰 Plugin / Mods Supported\n\n> 💠 **Lapis Nodes** — *Performance • Power • Trust* 🚀",
            inline=False
        )
        
        await channel.send(embed=embed)
        await interaction.followup.send("✅ Minecraft plans posted in dedicated channel!", ephemeral=True)
    
    elif plan_type == "vps":
        embed = discord.Embed(
            title="💻・VPS Hosting Plans",
            description="🚀 **High-performance Virtual Private Servers** with full root access\n⚡ SSD/NVMe Storage ｜ 🔒 Full Root Access ｜ 🌐 Global Locations ｜ 🔄 Daily Backups\n",
            color=0x00ff00
        )
        
        for plan_name, details in PLANS["vps"].items():
            embed.add_field(
                name=f"💻 **{plan_name}** — {details['price']} / Month",
                value=f"🐏 RAM - **{details['ram']}**\n💾 Storage - **{details['storage']}**\n⚡ CPU - **{details['cpu']}**\n🌐 Bandwidth - **{details['bandwidth']}**",
                inline=True
            )
        
        embed.add_field(
            name="🔧 All VPS Plans Include:",
            value="> 🔒 Full Root Access\n> 🌐 Multiple OS Choices\n> 🔄 Daily Backups\n> 🛡️ DDoS Protection\n> 💾 SSD/NVMe Storage\n> 🚀 Instant Deployment",
            inline=False
        )
        
        await channel.send(embed=embed)
        await interaction.followup.send("✅ VPS plans posted in dedicated channel!", ephemeral=True)
    
    elif plan_type == "developer":
        embed = discord.Embed(
            title="👨‍💻・Minecraft Developer Plans",
            description="🛠️ **Specialized hosting for developers** with extra features\n🔧 Database Access ｜ 🌐 Domain Support ｜ 🚀 Development Tools ｜ 📦 Git Integration\n",
            color=0xFFA500
        )
        
        for plan_name, details in PLANS["developer"].items():
            embed.add_field(
                name=f"🔧 **{plan_name}** — {details['price']} / Month",
                value=f"🐏 RAM - **{details['ram']}**\n💾 Storage - **{details['storage']}**\n✨ Features - **{details['features']}**",
                inline=True
            )
        
        embed.add_field(
            name="🚀 Developer Features:",
            value="> 📦 Git Integration\n> 🗄️ Database Support\n> 🔧 API Access\n> 🚀 CI/CD Pipelines\n> 🌐 Staging Environments\n> 📊 Analytics Dashboard",
            inline=False
        )
        
        await channel.send(embed=embed)
        await interaction.followup.send("✅ Developer plans posted in dedicated channel!", ephemeral=True)
    
    elif plan_type == "domain":
        embed = discord.Embed(
            title="🌐・Domain Registration Plans",
            description="🔗 **Register your perfect domain name** with premium features\n🛡️ Privacy Protection ｜ 📧 Email Forwarding ｜ 🔄 Easy Transfer ｜ 🔒 SSL Certificates\n",
            color=0x9b59b6
        )
        
        for plan_name, details in PLANS["domain"].items():
            embed.add_field(
                name=f"🌐 **{plan_name}** — {details['price']}",
                value=f"🔄 Transfer - **{details['transfer']}**\n⭐ {details['features']}",
                inline=True
            )
        
        embed.add_field(
            name="🔒 Domain Features:",
            value="> 🛡️ Free Privacy Protection\n> 📧 Email Forwarding\n> 🔄 Easy Domain Transfer\n> 🔒 Free SSL Certificate\n> 🌐 DNS Management\n> 📊 Domain Analytics",
            inline=False
        )
        
        await channel.send(embed=embed)
        await interaction.followup.send("✅ Domain plans posted in dedicated channel!", ephemeral=True)
    
    elif plan_type == "booster":
        embed = discord.Embed(
            title="🚀・Server Booster Plans",
            description="🌟 **Enhance your Discord experience** with booster perks\n🎨 Custom Colors ｜ 🔊 Audio Quality ｜ 🏆 Priority Support ｜ ✨ Exclusive Rewards\n",
            color=0xe91e63
        )
        
        for plan_name, details in PLANS["booster"].items():
            embed.add_field(
                name=f"🌟 **{plan_name}** — {details['price']}",
                value=f"🎁 {details['benefits']}",
                inline=True
            )
        
        embed.add_field(
            name="✨ Booster Benefits:",
            value="> 🎨 Custom Color Roles\n> 🔊 Enhanced Audio Quality\n> 🏆 Priority Support\n> ✨ Exclusive Emojis\n> 📢 Special Announcements\n> 🎁 Monthly Rewards",
            inline=False
        )
        
        await channel.send(embed=embed)
        await interaction.followup.send("✅ Booster plans posted in dedicated channel!", ephemeral=True)
    
    elif plan_type == "youtuber":
        embed = discord.Embed(
            title="📹・YouTuber & Creator Plans",
            description="🎬 **Special offers for content creators** and influencers\n📢 Promotion ｜ 🤝 Partnership ｜ 🎁 Free Resources ｜ 💰 Revenue Sharing\n",
            color=0xff0000
        )
        
        for plan_name, details in PLANS["youtuber"].items():
            embed.add_field(
                name=f"📹 **{plan_name}** — {details['price']}",
                value=f"📊 Subs - **{details['subs']}**\n✨ {details['benefits']}",
                inline=True
            )
        
        embed.add_field(
            name="🎬 Creator Benefits:",
            value="> 📢 Social Media Promotion\n> 🤝 Partnership Opportunities\n> 🎁 Free Resources & Hosting\n> 💰 Revenue Sharing\n> 🚀 Early Access Features\n> 📊 Analytics Support",
            inline=False
        )
        
        await channel.send(embed=embed)
        await interaction.followup.send("✅ YouTuber plans posted in dedicated channel!", ephemeral=True)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def giveaway(ctx, action: str = None):
    """Giveaway management command"""
    if action == "create":
        modal = CreateGiveawayModal()
        await ctx.send_modal(modal)
    
    elif action == "panel":
        embed = discord.Embed(
            title="🎉 Giveaway Management Panel",
            description="Manage giveaways with the buttons below:",
            color=0xffd700
        )
        view = GiveawayManagementView()
        await ctx.send(embed=embed, view=view)
    
    elif action == "list":
        active_giveaways = [g for g in giveaway_system.giveaways.values() if not g["ended"]]
        if not active_giveaways:
            await ctx.send("No active giveaways!")
            return
        
        embed = discord.Embed(title="Active Giveaways", color=0xffd700)
        for msg_id, giveaway in list(giveaway_system.giveaways.items())[:5]:
            if not giveaway["ended"]:
                channel = bot.get_channel(giveaway["channel_id"])
                embed.add_field(
                    name=giveaway["prize"],
                    value=f"Winners: {giveaway['winners']} | Participants: {len(giveaway['participants'])}\n"
                         f"Ends: <t:{int(datetime.datetime.fromisoformat(giveaway['end_time']).timestamp())}:R>\n"
                         f"[Jump to Giveaway](https://discord.com/channels/{ctx.guild.id}/{giveaway['channel_id']}/{msg_id})",
                    inline=False
                )
        await ctx.send(embed=embed)
    
    else:
        embed = discord.Embed(
            title="Giveaway Commands",
            description="`!giveaway create` - Create a new giveaway\n"
                       "`!giveaway panel` - Show management panel\n"
                       "`!giveaway list` - List active giveaways\n"
                       "`!gend <message_id>` - End a giveaway\n"
                       "`!greroll <message_id>` - Reroll winners",
            color=0xffd700
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def gend(ctx, message_id: str):
    """End a giveaway and pick winners"""
    giveaway = giveaway_system.giveaways.get(message_id)
    if not giveaway:
        await ctx.send("❌ Giveaway not found!")
        return
    
    if giveaway["ended"]:
        await ctx.send("❌ This giveaway has already ended!")
        return
    
    participants = giveaway["participants"]
    if not participants:
        await ctx.send("❌ No participants to choose from!")
        return
    
    winners = []
    for _ in range(min(giveaway["winners"], len(participants))):
        winner_id = random.choice(participants)
        winners.append(winner_id)
        participants.remove(winner_id)
    
    winner_mentions = [f"<@{winner_id}>" for winner_id in winners]
    
    # Update the giveaway message
    channel = bot.get_channel(giveaway["channel_id"])
    try:
        message = await channel.fetch_message(int(message_id))
        embed = message.embeds[0]
        embed.color = 0xff0000
        embed.add_field(
            name="🎊 Winners",
            value=", ".join(winner_mentions) if winner_mentions else "No winners could be selected",
            inline=False
        )
        await message.edit(embed=embed, view=None)
    except:
        pass
    
    giveaway_system.end_giveaway(message_id)
    
    # Announce winners
    winners_embed = discord.Embed(
        title="🎉 Giveaway Ended!",
        description=f"**Prize:** {giveaway['prize']}\n**Winners:** {', '.join(winner_mentions)}",
        color=0x00ff00
    )
    await ctx.send(embed=winners_embed)

@bot.command()
@commands.has_permissions(manage_messages=True)
async def greroll(ctx, message_id: str):
    """Reroll giveaway winners"""
    giveaway = giveaway_system.giveaways.get(message_id)
    if not giveaway:
        await ctx.send("❌ Giveaway not found!")
        return
    
    participants = giveaway["participants"]
    if not participants:
        await ctx.send("❌ No participants to choose from!")
        return
    
    winner_id = random.choice(participants)
    
    embed = discord.Embed(
        title="🔁 Giveaway Rerolled!",
        description=f"New winner for **{giveaway['prize']}**: <@{winner_id}>",
        color=0xffd700
    )
    await ctx.send(embed=embed)

@tasks.loop(seconds=30)
async def check_giveaways():
    """Check for ended giveaways"""
    current_time = datetime.datetime.now()
    for message_id, giveaway in giveaway_system.giveaways.items():
        if giveaway["ended"]:
            continue
        
        end_time = datetime.datetime.fromisoformat(giveaway["end_time"])
        if current_time >= end_time:
            # Auto-end the giveaway
            channel = bot.get_channel(giveaway["channel_id"])
            if channel:
                participants = giveaway["participants"]
                winners = []
                
                for _ in range(min(giveaway["winners"], len(participants))):
                    winner_id = random.choice(participants)
                    winners.append(winner_id)
                    participants.remove(winner_id)
                
                winner_mentions = [f"<@{winner_id}>" for winner_id in winners]
                
                try:
                    message = await channel.fetch_message(int(message_id))
                    embed = message.embeds[0]
                    embed.color = 0xff0000
                    embed.add_field(
                        name="🎊 Winners",
                        value=", ".join(winner_mentions) if winner_mentions else "No participants",
                        inline=False
                    )
                    await message.edit(embed=embed, view=None)
                    
                    # Send announcement
                    announcement = discord.Embed(
                        title="🎉 Giveaway Ended!",
                        description=f"**Prize:** {giveaway['prize']}\n**Winners:** {', '.join(winner_mentions) if winner_mentions else 'No winners'}",
                        color=0x00ff00
                    )
                    await channel.send(embed=announcement)
                    
                except Exception as e:
                    print(f"Error ending giveaway: {e}")
                
                giveaway_system.end_giveaway(message_id)

@bot.command()
async def post_partnership(ctx):
    """Post the partnership guidelines"""
    channel = bot.get_channel(CHANNELS["partnership"])
    if not channel:
        await ctx.send("❌ Partnership channel not found!")
        return
    
    embed = discord.Embed(
        title="💎 Lapis Nodes Partnership",
        description="**Partnership Guidelines** 🤝\n\nWe're excited to collaborate with creators and communities who share our passion for gaming and technology!",
        color=0x00ff00
    )
    
    embed.add_field(
        name="🎯 Partnership Requirements",
        value="We're looking for passionate creators and communities to partner with. Here are our requirements:",
        inline=False
    )
    
    embed.add_field(
        name="📹 YouTubers",
        value="• Minimum 2,000 subscribers\n• Minimum 5,000 average views per video\n• Active posting schedule (2+ videos/month)\n• Gaming/tech-related content preferred",
        inline=False
    )
    
    embed.add_field(
        name="🎥 Streamers (Twitch, YouTube, etc.)",
        value="• Regular streaming schedule\n• Consistent 25+ active viewers\n• Professional stream quality\n• Active community engagement",
        inline=False
    )
    
    embed.add_field(
        name="🌐 Minecraft Servers",
        value="• Minimum 30 concurrent active players\n• Professional setup with website/Discord\n• Active maintenance and updates\n• Positive community reputation",
        inline=False
    )
    
    embed.add_field(
        name="💻 Tech Communities",
        value="• Active Discord/community platform\n• 500+ engaged members\n• Regular events/activities\n• Tech/gaming focused content",
        inline=False
    )
    
    embed.add_field(
        name="✅ What We Offer",
        value="• **Free or discounted hosting services**\n• **Promotion** on our social media and website\n• **Early access** to new features\n• **Dedicated support** and partner benefits\n• **Revenue sharing** opportunities\n• **Custom solutions** for your needs",
        inline=False
    )
    
    embed.add_field(
        name="💬 Interested in Partnering?",
        value="Submit your partnership proposal by:\n1. Opening a **partnership ticket** in our Discord\n2. Emailing us at **partnerships@lapisnodes.com**\n3. Contacting our partnership manager\n\nWe review applications within 2-3 business days!",
        inline=False
    )
    
    embed.set_footer(text="💎 Lapis Nodes - Building the future of gaming hosting")
    
    await channel.send(embed=embed)
    await ctx.send("✅ Partnership guidelines posted!")

@bot.command()
async def post_all_plans(ctx):
    """Post all plans to their respective channels"""
    plans = ["minecraft", "vps", "developer", "domain", "booster", "youtuber"]
    
    for plan_type in plans:
        try:
            await send_plan_details(ctx, plan_type)
            await asyncio.sleep(1)  # Avoid rate limits
        except Exception as e:
            await ctx.send(f"❌ Error posting {plan_type} plans: {str(e)}")
    
    await ctx.send("✅ All plans have been posted to their respective channels!")

@bot.event
async def on_ready():
    print(f'✅ {bot.user} has logged in successfully!')
    print(f'🎯 Bot is in {len(bot.guilds)} guild(s)')
    print(f'💎 Lapis Nodes Bot is ready!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Lapis Nodes & Giveaways"))
    check_giveaways.start()

@bot.command()
async def setup(ctx):
    """Main setup command"""
    embed = discord.Embed(
        title="💎 Lapis Nodes Support System",
        description="Welcome to Lapis Nodes! Please select an option below to get started:\n\n"
                   "💎 **Buy VPS/Server** - Purchase our premium hosting services\n"
                   "🎁 **Claim Free Server** - Apply for free hosting options\n"
                   "🤝 **Partnership** - Partnership and collaboration inquiries\n"
                   "🛠️ **Support** - Technical support and assistance\n"
                   "🎉 **Giveaways** - Giveaway-related questions and issues\n\n"
                   "*Select an option from the dropdown menu below*",
        color=0x5865F2
    )
    
    view = TicketView()
    await ctx.send(embed=embed, view=view)

@bot.command()
async def giveaway_panel(ctx):
    """Setup giveaway management panel"""
    if not ctx.author.guild_permissions.manage_messages:
        await ctx.send("❌ You need manage messages permission to use this!")
        return
    
    embed = discord.Embed(
        title="🎉 Giveaway System",
        description="**Create and manage amazing giveaways for your community!**\n\n"
                   "🎁 **Regular Giveaways** - Free hosting, Discord Nitro, games\n"
                   "💎 **Special Events** - Launch events, holidays, milestones\n"
                   "🚀 **Partner Giveaways** - Collaborations with other creators\n\n"
                   "Click the buttons below to get started!",
        color=0xffd700
    )
    
    view = GiveawayManagementView()
    await ctx.send(embed=embed, view=view)

@bot.command()
async def help_commands(ctx):
    """Display all available commands"""
    embed = discord.Embed(
        title="💎 Lapis Nodes Bot Commands",
        description="Here are all the available commands:",
        color=0x5865F2
    )
    
    commands_list = {
        "!setup": "Create the main ticket panel",
        "!post_all_plans": "Post all plans to their channels",
        "!post_partnership": "Post partnership guidelines",
        "!giveaway": "Giveaway management commands",
        "!giveaway_panel": "Setup giveaway management panel",
        "!gend <message_id>": "End a giveaway and pick winners",
        "!greroll <message_id>": "Reroll giveaway winners",
        "!help_commands": "Show this help message"
    }
    
    for cmd, desc in commands_list.items():
        embed.add_field(name=cmd, value=desc, inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def update_config(ctx, key: str, value: int):
    """Update channel configuration"""
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("❌ You need administrator permissions to use this command!")
        return
    
    if key in CHANNELS:
        CHANNELS[key] = value
        config["channel_ids"][key] = value
        with open('config.json', 'w') as f:
            json.dump(config, f, indent=4)
        await ctx.send(f"✅ Updated {key} to {value}")
    else:
        await ctx.send("❌ Invalid channel key!")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You don't have permission to use this command!")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ Invalid arguments provided!")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        print(f"Error: {error}")
        await ctx.send(f"❌ An error occurred: {str(error)}")

# Keep alive for Replit
from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "🤖 Lapis Nodes Bot is running!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    server = Thread(target=run)
    server.start()

# Start the bot
if __name__ == "__main__":
    keep_alive()
    bot.run(os.getenv('DISCORD_TOKEN'))
