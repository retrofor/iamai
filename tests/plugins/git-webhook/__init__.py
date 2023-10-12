from aiohttp import web
from iamai import Plugin
from iamai.log import logger
from .config import EVENT_DESCRIPTIONS

server = None
app = web.Application()

class F(Plugin):
    async def handle(self) -> None:
        global server

        if str(self.event.message) == "service on":
            app.router.add_post("/", self.handle_request)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "localhost", 8888)

            try:
                await site.start()
                logger.info("Server started on localhost:8888")
                await self.event.reply("Server started on localhost:8888")
            except OSError:
                logger.error("Failed to start server. Port is already in use.")
                await self.event.reply(
                    "Failed to start server. Port is already in use."
                )
        elif str(self.event.message) == "service off":
            if server is not None:
                server.close()
                await server.wait_closed()
                await self.event.reply("Server Off.")
            else:
                await self.event.reply("Server is not running.")
    
    async def handle_request(self, request):
        data = await request.json()
        # logger.info(f'Received JSON body: {data}')

        event_type = request.headers.get("X-GitHub-Event")
        if event_type in [
            "commit_comment",
            "create",
            "delete",
            "fork",
            "issue_comment",
            "issues",
            "pull_request",
            "push",
            "release",
            "watch",
        ]:
            message = self._format_event(event_type=event_type, data=data)
            if message:
                await self.event.adapter.call_api(
                    "send_group_msg", group_id=126211793, message=message
                )
            else:
                return

        response = {"message": "Received request"}
        return web.json_response(response)

    async def rule(self) -> bool:
        return str(self.event.message) in ["service on", "service off"]

    @staticmethod
    def _format_event(self, event_type, data):
        try:
            if isinstance(EVENT_DESCRIPTIONS[event_type], dict):
                return EVENT_DESCRIPTIONS[event_type][data["action"]].format(**data)
            elif isinstance(EVENT_DESCRIPTIONS[event_type], str):
                return EVENT_DESCRIPTIONS[event_type].format(**data)
        except KeyError:
            return None


"""
>smee -u https://smee.io/MHldOrjI8msgNUa5 -p 8888
"""
