import random
import re
from iamai import Plugin

class Roll(Plugin):
    async def handle(self) -> None:
        def roll_dice(num=1,RangeNum=100,Enhans=0) -> 'list|int' : # type: ignore
            DiceList = [y for x in range(1,num+1) for y in range(1,RangeNum+1)] # 存储num个骰子的1~6数字
            IndexList = [random.randint(0,len(DiceList)-1) for i in range(num)] # 键值索引
            ValList = []
            for i in IndexList:
                ValList.append(DiceList[i])
            PrintList = []
            for i in ValList:
                PrintList.append(str(i)+"+"+str(Enhans))
            if Enhans == 0:
                return ValList,sum(ValList) # type: ignore
            else:
                return PrintList,sum(ValList)+num*Enhans  # type: ignore
        
        numList = re.findall(r'r(\d+)?d?(\d+)?\+?(\d+)?',self.event.message.get_plain_text())
        try:
            RangeNum = int(numList[0][1])
        except ValueError:
            RangeNum = 100
        try:
            RollNum = int(numList[0][0])
        except ValueError:
            RollNum = 1
        try:
            Enhans = int(numList[0][2])
        except ValueError:
            Enhans = 0
        DiceList,Total = roll_dice(RollNum,RangeNum,Enhans) # type: ignore
        if random.randint(1,2) == 1:
            is_success = "成功"
        else:
            is_success = "失败"
        await self.event.reply(f"Dice: {DiceList}={Total}")

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type == "message_sent" or self.event.type == "message":
            return self.event.message.startswith("r")
        else:
            return False

