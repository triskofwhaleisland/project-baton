import discord
from discord.ext import commands
from enum import Enum, auto
from dataclasses import dataclass
import logging
import yaml

prefix = "."
version = "A is for Alpha"
intents = discord.Intents.default()
intents.messages = True
intents.members = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or(prefix), intents=intents)
token = open("tokenfile").read()

logging.basicConfig(level=logging.INFO)


class RecruitmentStatus(Enum):
    READY = auto()
    # READY_CONDITIONAL = auto()
    ACTIVE = auto()

    @classmethod
    async def convert(cls, ctx, role: str):
        try:
            return cls[role.upper()]
        except ValueError:
            return None


@dataclass
class RecruitQueue:
    queue: dict[discord.Member : RecruitmentStatus]
    active_user: discord.Member | None = None

    def update_user(
        self, user: discord.Member, status: RecruitmentStatus | None
    ) -> None:
        if status is None:
            if self.queue[user] == RecruitmentStatus.ACTIVE:
                self.active_user = None
            del self.queue[user]
        else:
            if status == RecruitmentStatus.ACTIVE:
                self.active_user = user
            self.queue[user] = status


def load_recruiters_from_yaml(filename: str) -> dict:
    try:
        return {
            bot.get_user(userID): RecruitmentStatus[statusName]
            for (userID, statusName) in dict(yaml.safe_load(open(filename))).items()
        }
    except FileNotFoundError:
        open(filename, "w")
        return {}


def save_recruiters_to_yaml(queue: dict, filename: str) -> None:
    yaml.safe_dump(
        {user.id: status.name for (user, status) in queue.items()}, open(filename, "w")
    )


RQ = RecruitQueue({})


@bot.event
async def on_ready():
    global RQ
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    recruiters = load_recruiters_from_yaml("recruiters.yaml")
    RQ = RecruitQueue(recruiters)
    await bot.get_channel(945513732115673192).send("I just restarted!")


@bot.command()
async def set_status(ctx: commands.Context, stat: str):
    try:
        if (
            RecruitmentStatus[stat.upper()] == RecruitmentStatus.ACTIVE
            and RecruitmentStatus.ACTIVE in RQ.queue.values()
        ):
            await ctx.channel.send(
                f"{RQ.active_user} is already actively recruiting. Ask them to leave first."
            )
        else:
            RQ.update_user(ctx.author, RecruitmentStatus[stat.upper()])
            await ctx.channel.send(f"{ctx.author} is now {stat.lower()}.")
    except ValueError:
        await ctx.channel.send(
            f"{stat.upper()} is not a valid status. "
            f"Valid statuses are: {', '.join([rs.name for rs in RecruitmentStatus])}."
        )
    finally:
        save_recruiters_to_yaml(RQ.queue, "recruiters.yaml")


@bot.command()
async def join(ctx: commands.Context):
    await set_status(ctx, "active")


@bot.command()
async def ready(ctx: commands.Context):
    await set_status(ctx, "ready")


@bot.command()
async def leave(ctx: commands.Context):
    if ctx.author in RQ.queue.keys():
        RQ.update_user(ctx.author, None)
        await ctx.channel.send(f"{ctx.author} has left the queue.")
    else:
        await ctx.channel.send("You can't leave something you aren't a part of!")


@bot.command()
async def display(ctx: commands.Context):
    # await ctx.channel.send(RQ.queue)
    await ctx.channel.send(
        embed=discord.Embed(
            title="Current Recruiters",
            description="Name:\t\t\t\tStatus\n"
            + (f"**{RQ.active_user}: ACTIVE**\n" if RQ.active_user is not None else "")
            + "\n".join(
                f"{user}:\t\t\t\t{status.name}"
                for (user, status) in RQ.queue.items()
                if status != RecruitmentStatus.ACTIVE
            ),
        ).set_footer(text=f"Project BATON: {version}")
    )


@bot.command()
async def user_from_id(ctx: commands.Context, id_: int):
    await ctx.channel.send(bot.get_user(id_))


@bot.command()
async def ping(ctx: commands.Context, role: RecruitmentStatus, *, msg: str = ""):
    await ctx.channel.send(
        f"{ctx.author.mention} -> "
        f"{' '.join([user.mention for (user, status) in RQ.queue.items() if status == role])}"
        + (f": {msg}" if msg != "" else "")
        if role in RQ.queue.values()
        else f"Literally nobody is {role.name.lower()} right now."
    )


@bot.command()
async def all_commands(ctx: commands.Context):
    await ctx.channel.send(", ".join(bot.all_commands.keys()))


bot.run(token)
