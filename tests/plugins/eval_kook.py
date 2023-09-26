from iamai import Plugin
from iamai.log import logger
from iamai.models.BM25 import BM25
from iamai.adapter.kook.message import (
    KookMessage,
    KookMessageSegment,
    escape_kmarkdown,
    unescape_kmarkdown,
)

documents = [
    "管制品兑换-远程武器-手枪-等级1".split("-"),
    "唐肆-技能-舞枪戈".split("-"),
    "五金店-道具-钉枪-等级0".split("-"),
    "五金店-道具-扳手-等级0".split("-"),
    "武器店-组件-民用自卫手枪弹夹-等级1".split("-"),
]
bm25 = BM25(documents)


class EvalKook(Plugin):
    global bm25

    async def handle(self) -> None:
        msg = KookMessage()
        msg += KookMessageSegment.text('jijijijiji')
        await self.event.reply(msg)
        logger.info(list(self.event))
        # await self.event.adapter.call_api(
        #     api="message/create", target_id=self.event.group_id, content=KookMessageSegment.KMarkdown('**hi**')
        # )
<<<<<<< HEAD
=======
        # await self.event.reply(bm25.get_score(query))
        await self.event.adapter.call_api(
            api="message/create",
            target_id=self.event.group_id,
            content=KookMessageSegment.KMarkdown("**hi**"),
        )
>>>>>>> e96a4d186b0e2d1cd114661c33c2ea51044528a8

    async def rule(self) -> bool:
        if self.event.adapter.name != "kook":
            return False
        return self.event.content.startswith(".test")
