from asyncio import TimeoutError

from iamai import Context, Plugin, command


class SurveyPlugin(Plugin):
    name = "survey"

    @command("survey")
    async def survey(self, ctx: Context) -> None:
        await ctx.reply("你的昵称是？")
        try:
            answer = await ctx.wait_for_message(timeout=60)
        except TimeoutError:
            await ctx.reply("已超时，请重新开始。")
            return
        ctx.state["nickname"] = answer.text
        await ctx.reply(f"已记录：{answer.text}")
