from typing import Self

import discord
from discord.ext import commands
from enum import Enum, auto
from dataclasses import dataclass
import logging
import yaml

PREFIX = "."
VERSION = "A is for Alpha"
INTENTS = discord.Intents.all()
# INTENTS.message_content = True
# INTENTS.members = True
BOT = commands.Bot(command_prefix=commands.when_mentioned_or(PREFIX), intents=INTENTS)
TOKEN = open("tokenfile").read()

logging.basicConfig(level=logging.INFO)


class RecruitmentStatus(Enum):
    READY = auto()
    ACTIVE = auto()

    @classmethod
    async def convert(cls, _ctx: commands.Context, role: str) -> Self | None:
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
            BOT.get_user(userID): RecruitmentStatus[statusName]
            for (userID, statusName) in dict(yaml.safe_load(open(filename))).items()
        }
    except FileNotFoundError:
        open(filename, "w").close()
        return {}


def save_recruiters_to_yaml(queue: dict, filename: str) -> None:
    yaml.safe_dump(
        {user.id: status.name for (user, status) in queue.items()}, open(filename, "w")
    )


BOT.RQ = RecruitQueue({})


@BOT.event
async def on_ready() -> None:
    print(f"Logged in as {BOT.user} (ID: {BOT.user.id})")
    print("------")
    recruiters = load_recruiters_from_yaml("recruiters.yaml")
    BOT.RQ = RecruitQueue(recruiters)
    await BOT.get_channel(945513732115673192).send("I just restarted!")


@BOT.command()
async def set_status(ctx: commands.Context, stat: str) -> None:
    try:
        if (
            RecruitmentStatus[stat.upper()] == RecruitmentStatus.ACTIVE
            and RecruitmentStatus.ACTIVE in BOT.RQ.queue.values()
            and BOT.RQ.active_user is not None
        ):
            await ctx.channel.send(
                f"{BOT.RQ.active_user} is already actively recruiting. "
                f"Ask them to leave first."
            )
        else:
            BOT.RQ.update_user(ctx.author, RecruitmentStatus[stat.upper()])
            await ctx.channel.send(f"{ctx.author} is now {stat.lower()}.")
    except ValueError:
        await ctx.channel.send(
            f"{stat.upper()} is not a valid status. "
            f"Valid statuses are: {', '.join([rs.name for rs in RecruitmentStatus])}."
        )
    finally:
        save_recruiters_to_yaml(BOT.RQ.queue, "recruiters.yaml")


@BOT.command()
async def join(ctx: commands.Context) -> None:
    await set_status(ctx, "active")


@BOT.command()
async def ready(ctx: commands.Context) -> None:
    await set_status(ctx, "ready")


@BOT.command()
async def leave(ctx: commands.Context) -> None:
    if ctx.author in BOT.RQ.queue.keys():
        BOT.RQ.update_user(ctx.author, None)
        await ctx.channel.send(f"{ctx.author} has left the queue.")
    else:
        await ctx.channel.send("You can't leave something you aren't a part of!")


@BOT.command()
async def display(ctx: commands.Context) -> None:
    # await ctx.channel.send(RQ.queue)
    await ctx.channel.send(
        embed=discord.Embed(
            title="Current Recruiters",
            description=(
                "Name:\t\t\t\tStatus\n"
                + (
                    f"**{BOT.RQ.active_user}: ACTIVE**\n"
                    if BOT.RQ.active_user is not None
                    else ""
                )
                + "\n".join(
                    f"{user}:\t\t\t\t{status.name}"
                    for (user, status) in BOT.RQ.queue.items()
                    if status != RecruitmentStatus.ACTIVE
                )
            ),
        ).set_footer(text=f"Project BATON: {VERSION}")
    )


@BOT.command()
async def user_from_id(ctx: commands.Context, id_: int) -> None:
    await ctx.channel.send(BOT.get_user(id_))


@BOT.command()
async def ping(
    ctx: commands.Context, role: RecruitmentStatus, *, msg: str = ""
) -> None:
    await ctx.channel.send(
        f"{ctx.author.mention} -> "
        f"{' '.join([user.mention for (user, status) in BOT.RQ.queue.items() if status == role])}"
        + (
            f": {msg}"
            if msg != "" and role in BOT.RQ.queue.values()
            else f"Literally nobody is {role.name.lower()} right now."
        )
    )


@BOT.command()
async def all_commands(ctx: commands.Context) -> None:
    await ctx.channel.send(", ".join(BOT.all_commands.keys()))


@BOT.command()
@commands.has_permissions(administrator=True)
async def remove_from_queue(ctx: commands.Context, user: discord.Member) -> None:
    try:
        BOT.RQ.update_user(user, None)
    except KeyError:
        await ctx.channel.send(f"{user} is not in the queue. L + clueless :P")


@remove_from_queue.error
async def remove_from_queue_error(
    error: commands.CommandError, ctx: commands.Context
) -> None:
    if isinstance(error, commands.CheckFailure):
        await ctx.channel.send("Yikes sweaty, check your (Discord) privilege(s).")
    else:
        await ctx.channel.send(
            f"There was an error removing that user from the queue: {error}"
        )


BOT.run(TOKEN)
