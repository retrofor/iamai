from iamai import Plugin
from iamai.log import logger
from iamai.models.BM25 import BM25
from iamai.adapter.kook.message import KookMessageSegment, KookMessage
from iamai.adapter.kook.message import unescape_kmarkdown, escape_kmarkdown

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
        logger.info(self.event.type)
        # query = str(self.event.content)[5:]
        # logger.info(eval(query))
        # await self.event.reply(escape_kmarkdown(query))
        # await self.event.reply(str(eval(query)))
        # await self.event.reply(
        #     "\n".join([str(x) for x in bm25.search_top_k(query, k=5)])
        # )
        # await self.event.reply(bm25.get_score(query))
        await self.event.adapter.call_api(
            api="message/create", target_id=self.event.group_id, content=KookMessageSegment.KMarkdown('**hi**')
        )

    async def rule(self) -> bool:
        if self.event.adapter.name != "kook":
            return False
        return self.event.content.startswith(".test")
