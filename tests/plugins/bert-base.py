from iamai import Plugin
from iamai.adapter.cqhttp.message import CQHTTPMessageSegment


class BertBase(Plugin):
    async def handle(self) -> None:
        import requests

        API_URL = "https://api-inference.huggingface.co/models/CompVis/stable-diffusion-v1-4"
        headers = {"Authorization": "Bearer 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"}

        def query(payload):
            response = requests.post(API_URL, headers=headers, json=payload)
            return response.content
        image_bytes = query({
            "inputs": self.event.message.get_plain_text().replace("sd>",""),
        })
        import io

        from PIL import Image
        image = Image.open(io.BytesIO(image_bytes))
        image.save('s.png')
        await self.event.reply(CQHTTPMessageSegment.image("file:///D:\\iamai_dev\\test\\s.png"))

    async def rule(self) -> bool:
        if self.event.adapter.name != "cqhttp":
            return False
        if self.event.type == "message_sent" or self.event.type == "message":
            return self.event.message.startswith("sd>")
        else:
            return False
