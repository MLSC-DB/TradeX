from datetime import datetime
import os
import time
import discord
from discord.ext import commands
from discord_components import DiscordComponents
from dotenv import load_dotenv
import json
from pymongo import MongoClient

MONGODB_CONNECTION_URI = os.getenv("MONGODB_CONNECTION_URI")
client = MongoClient(MONGODB_CONNECTION_URI)

db = client["astellar"]
part_form = db["offlineTeams"]
bj = db["brokerJack"]

empty = []


def main():
    load_dotenv()
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    intents = discord.Intents.all()
    bot = commands.Bot(
        command_prefix="tx ",
        intents=intents,
        status=discord.Status.dnd,
        activity=discord.Game("BrokerJack at Astellar 2022 ✨"),
        help_command=None,
    )

    DiscordComponents(bot)

    @bot.event
    async def on_ready():
        print("Logged in as")
        print(bot.user.name)
        print(bot.user.id)
        print("------")
        print(os.path.expanduser("~"))

    bot.launch_time = datetime.utcnow()

    @bot.command(name="uptime")
    async def uptime(ctx):
        delta_uptime = datetime.utcnow() - bot.launch_time
        h, r = divmod(delta_uptime.total_seconds(), 3600)
        m, s = divmod(r, 60)
        d, h = divmod(h, 24)
        await ctx.reply(
            f"{int(d)} days, {int(h)} hours, {int(m)} minutes, {int(s)} seconds have elapsed since starting the bot."
        )

    @bot.command(name="ping")
    async def ping(ctx):
        ok = client.admin.command("ping")
        await ctx.reply(ok)


    @bot.command(name="register")
    async def register(ctx, TeamName):
        if bj.find_one({"TeamName": TeamName}):
            await ctx.send(
                "Hey!Looks like you already have registered for BrokerJack!,"
            )
        else:
            if not part_form.find_one({"TeamName": TeamName}):
                await ctx.reply(
                    "Hey! Looks like you haven't signed up for Astellar 2022!\n Perhaps give it a go at https://mlscdb.xyz/ ?"
                )
            else:
                bj.insert_one(
                    {
                        "TeamName": TeamName,
                        "Leader": str(ctx.author.id),
                        "Points": 750,
                        "Answers": empty,
                    }
                )
                await ctx.reply(
                    "Successfully registered your team **{}** ! ".format(TeamName)
                )

    @bot.command(name="trade")
    async def trade(ctx, TeamName, points, length):
        user = ctx.author.id

        user = str(user)

        res1 = bj.find_one({"Leader": user})
        res = bj.find_one({"TeamName": TeamName})
        if res:
            rest_points = res["Points"]
            

            rest_points = int(rest_points)
            points = abs(int(points))
            user1 = res["Leader"]
            user1 = bot.get_user(int(user1))
            user = ctx.author.id
            user0 = ctx.author
            if points > rest_points:
                await ctx.reply(
                    "Hey smart Jack, team **{}** doesn't have enough points to use your services".format(
                        TeamName
                    )
                )
            else:
                await ctx.send(
                    "{}, do you want an answer of length {} for {} points? (yes/no)".format(
                        user1.mention, length, points
                    )
                )

                def check(mssg):
                    return mssg.author == user1

                msg = await bot.wait_for("message", check=check)
                if "no" in msg.content.lower():
                    await ctx.send("Cancelling request")
                    await ctx.reply("Deal cancelled by {}".format(user1))
                    return 0
                elif "yes" in msg.content.lower():
                    await ctx.send("Proceeding for trade!")
                    try:
                        await ctx.reply("Hi, <@{}> please check your DMs".format(user))
                        time.sleep(1)
                        await user0.send(
                            "Hello! Enter the answer that you wanted to trade for {} points".format(
                                points
                            )
                        )

                        def check(mssg):
                            return mssg.author == ctx.message.author

                        while True:
                            msg = await bot.wait_for("message", check=check)
                            if "cancel" in msg.content.lower():
                                await user0.send("Cancelling request")
                                await ctx.reply("Deal cancelled by {}".format(user0))
                                return 0
                            if len(msg.content.strip()) == int(length):

                                time.sleep(0.5)
                                codeMessage = msg.content
                                break
                            else:
                                await user0.send(
                                    "Hey don't cheat, you've provided an answer of wrong length"
                                )
                                return 0
                        await user1.send("Here is your answer: {}".format(codeMessage))

                        def check(mssg):
                            return mssg.author == user1

                        await user1.send(
                            "Deducting **{}** points for successful transaction".format(
                                points
                            )
                        )
                        rest_points -= points
                        bj.find_one_and_update(
                            {"TeamName": TeamName},
                            {"$set": {"Points": rest_points}},
                        )
                        bj.find_one_and_update(
                            {"_id": res1["_id"]},
                            {"$set": {"Points": res1["Points"]+points}},
                        )
                        await ctx.reply("Successful Deal!")

                    except discord.errors.Forbidden:  # check if DM Closed
                        embed = discord.Embed(
                            title="UH OH!",
                            description="Looks like I'm unable to send you a Direct Message :(",
                            color=0xFF0000,
                        )
                        embed.add_field(
                            name="NOTE",
                            value="**Make sure this is turned on so that the bot is able to DM you!**",
                            inline=True,
                        )
                        embed.set_image(
                            url="https://support.discord.com/hc/article_attachments/360062973031/Screen_Shot_2020-07-24_at_10.46.47_AM.png"
                        )
                        embed.set_footer(text="Embed Support for Discord errors")
                        await ctx.send(user.mention, embed=embed)

        else:
            await ctx.reply(
                "Ayo lad, team **{}** doesn't exist on our BrokerJack database. Make sure they have signed up!".format(
                    TeamName
                )
            )

    @bot.command(name="points")
    async def points(ctx, TeamName):
        res = bj.find_one({"TeamName": TeamName})
        res = res["Points"]
        await ctx.reply("Team **{}** has {} points".format(TeamName, res))

    f = open("answers.json")
    data = json.load(f)

    @bot.command(name="check")
    async def check(ctx, level, question, answer):
        user = ctx.author.id

        user = str(user)

        res = bj.find_one({"Leader": user})
        print(res)
        points = res["Points"]
        # await ctx.reply(res)
        aL = res["Answers"]
        if answer.lower() in aL:
            await ctx.reply("You have already entered the answer!")
        else:
            if data[level][0][question] == answer.lower():
                result = bj.update_one(
                    {"_id": res["_id"]},
                    {
                        "$set": {
                            "Points": points + 20
                        },
                        "$push": {"Answers": answer.lower()}
                    },
                )
                print(result)
                await ctx.reply("Correct Answer!")
            else:
                await ctx.reply("Wrong Answer")

    # very bad implementaion, code just works tho

    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
