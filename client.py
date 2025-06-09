import asyncio
import base64
import os
import urllib
import httpx

from uuid import uuid4

import asyncclick as click

from a2a.client import A2AClient, A2ACardResolver
from a2a.types import (
    Part,
    TextPart,
    FilePart,
    FileWithBytes,
    Task,
    TaskState,
    Message,
    TaskStatusUpdateEvent,
    TaskArtifactUpdateEvent,
    MessageSendConfiguration,
    SendMessageRequest,
    SendStreamingMessageRequest,
    MessageSendParams,
    GetTaskRequest,
    TaskQueryParams,
    JSONRPCErrorResponse,
)
from common.utils.push_notification_auth import PushNotificationReceiverAuth


class A2AClientCLI:
    def __init__(self, agent_url, session, history, use_push_notifications, push_notification_receiver, headers):
        self.agent_url = agent_url
        self.session = session
        self.history = history
        self.use_push_notifications = use_push_notifications
        self.push_notification_receiver = push_notification_receiver
        self.headers = headers
        self.httpx_client = None
        self.card = None
        self.client = None
        self.streaming = False
        self.notification_receiver_host = None
        self.notification_receiver_port = None
        self.context_id = None

    async def setup(self):
        self.httpx_client = httpx.AsyncClient(timeout=30, headers=self.headers)
        card_resolver = A2ACardResolver(self.httpx_client, self.agent_url)
        self.card = await card_resolver.get_agent_card()
        print("======= Agent Card ========")
        print(self.card.model_dump_json(exclude_none=True))
        notif_receiver_parsed = urllib.parse.urlparse(self.push_notification_receiver)
        self.notification_receiver_host = notif_receiver_parsed.hostname
        self.notification_receiver_port = notif_receiver_parsed.port
        if self.use_push_notifications:
            from hosts.cli.push_notification_listener import (
                PushNotificationListener,
            )
            notification_receiver_auth = PushNotificationReceiverAuth()
            await notification_receiver_auth.load_jwks(f"{self.agent_url}/.well-known/jwks.json")
            push_notification_listener = PushNotificationListener(
                host=self.notification_receiver_host,
                port=self.notification_receiver_port,
                notification_receiver_auth=notification_receiver_auth,
            )
            push_notification_listener.start()
        self.client = A2AClient(self.httpx_client, agent_card=self.card)
        self.streaming = self.card.capabilities.streaming
        self.context_id = self.session if self.session > 0 else uuid4().hex

    async def run(self):
        await self.setup()
        continue_loop = True
        while continue_loop:
            print("=========  starting a new task ======== ")
            continue_loop, _, taskId = await self._complete_task(
                taskId=None,
                contextId=self.context_id,
            )
            if self.history and continue_loop:
                print("========= history ======== ")
                task_response = await self.client.get_task(
                    {"id": taskId, "historyLength": 10}
                )
                print(
                    task_response.model_dump_json(include={"result": {"history": True}})
                )

    async def _complete_task(self, taskId, contextId):
        prompt = click.prompt(
            "\nWhat do you want to send to the agent? (:q or quit to exit)"
        )
        if prompt == ":q" or prompt == "quit":
            return False, None, None
        message = Message(
            role="user",
            parts=[TextPart(text=prompt)],
            messageId=str(uuid4()),
            taskId=taskId,
            contextId=contextId,
        )
        file_path = click.prompt(
            "Select a file path to attach? (press enter to skip)",
            default="",
            show_default=False,
        )
        if file_path and file_path.strip() != "":
            with open(file_path, "rb") as f:
                file_content = base64.b64encode(f.read()).decode("utf-8")
                file_name = os.path.basename(file_path)
            message.parts.append(
                Part(root=FilePart(file=FileWithBytes(name=file_name, bytes=file_content)))
            )
        payload = MessageSendParams(
            id=str(uuid4()),
            message=message,
            configuration=MessageSendConfiguration(
                acceptedOutputModes=["text"],
            ),
        )
        if self.use_push_notifications:
            payload["pushNotification"] = {
                "url": f"http://{self.notification_receiver_host}:{self.notification_receiver_port}/notify",
                "authentication": {
                    "schemes": ["bearer"],
                },
            }
        taskResult = None
        msg = None
        if self.streaming:
            response_stream = self.client.send_message_streaming(
                SendStreamingMessageRequest(
                    id=str(uuid4()),
                    params=payload,
                )
            )
            async for result in response_stream:
                if isinstance(result.root, JSONRPCErrorResponse):
                    print("Error: ", result.root.error)
                    return False, contextId, taskId
                event = result.root.result
                contextId = event.contextId
                if isinstance(event, Task):
                    taskId = event.id
                elif isinstance(event, TaskStatusUpdateEvent) or isinstance(
                    event, TaskArtifactUpdateEvent
                ):
                    taskId = event.taskId
                elif isinstance(event, Message):
                    msg = event
                print(f"stream event => {event.model_dump_json(exclude_none=True)}")
            if taskId:
                taskResult = await self.client.get_task(
                    GetTaskRequest(
                        id=str(uuid4()),
                        params=TaskQueryParams(id=taskId),
                    )
                )
                taskResult = taskResult.root.result
        else:
            try:
                event = await self.client.send_message(
                    SendMessageRequest(
                        id=str(uuid4()),
                        params=payload,
                    )
                )
                event = event.root.result
            except Exception as e:
                print("Failed to complete the call", e)
                event = None
            if event and not contextId:
                contextId = event.contextId
            if isinstance(event, Task):
                if not taskId:
                    taskId = event.id
                taskResult = event
            elif isinstance(event, Message):
                msg = event
        if msg:
            print(f"\n{msg.model_dump_json(exclude_none=True)}")
            return True, contextId, taskId
        if taskResult:
            task_content = taskResult.model_dump_json(
                exclude={
                    "history": {
                        "__all__": {
                            "parts": {
                                "__all__": {"file"},
                            },
                        },
                    },
                },
                exclude_none=True,
            )
            print(f"\n{task_content}")
            state = TaskState(taskResult.status.state)
            if state.name == TaskState.input_required.name:
                return (
                    await self._complete_task(
                        taskId=taskId,
                        contextId=contextId,
                    ),
                    contextId,
                    taskId,
                )
            return True, contextId, taskId
        return True, contextId, taskId


@click.command()
@click.option("--agent", default="http://localhost:10000")
@click.option("--session", default=0)
@click.option("--history", default=False)
@click.option("--use_push_notifications", default=False)
@click.option("--push_notification_receiver", default="http://localhost:5000")
@click.option("--header", multiple=True)
async def cli(
    agent,
    session,
    history,
    use_push_notifications: bool,
    push_notification_receiver: str,
    header,
):
    headers = {h.split("=")[0]: h.split("=")[1] for h in header}
    cli_obj = A2AClientCLI(
        agent_url=agent,
        session=session,
        history=history,
        use_push_notifications=use_push_notifications,
        push_notification_receiver=push_notification_receiver,
        headers=headers,
    )
    await cli_obj.run()

if __name__ == "__main__":
    asyncio.run(cli())
