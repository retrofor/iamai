# from iamai import Plugin


# class Echo(Plugin):
#     async def handle(self) -> None:
#         await self.event.reply(self.event.message.replace("echo ", ""))

#     async def rule(self) -> bool:
#         if self.event.adapter.name != "cqhttp":
#             return False
#         if self.event.type == "message_sent" or self.event.type == "message":
#             return self.event.message.startswith("echo ")
#         else:
#             return False

import random


def roll_dice(num=1,RangeNum=100,Enhans=0) -> 'list|int' : # type: ignore
            DiceList = [y for x in range(1,num+1) for y in range(1,RangeNum+1)] # 存储num个骰子的1~6数字
            IndexList = [random.randint(0,len(DiceList)-1) for i in range(num)] # 键值索引
            ValList = []
            for i in IndexList:
                ValList.append(DiceList[i]+Enhans)
            PrintList = []
            for i in ValList:
                PrintList.append(str(i)+"+"+str(Enhans))
            if Enhans == 0:
                return ValList,sum(ValList) # type: ignore
            else:
                return PrintList,sum(ValList)  # type: ignore

print(roll_dice(5,4,2))
