import asyncio
import base64
import os
import urllib
import httpx
import time

from uuid import uuid4

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


async def cli(
    agent,
    session,
    history,
    use_push_notifications: bool,
    push_notification_receiver: str,
    header,
    prompt,
    file_path,
):
    headers = {h.split("=")[0]: h.split("=")[1] for h in header}
    print(f"Will use headers: {headers}")
    async with httpx.AsyncClient(timeout=30, headers=headers) as httpx_client:
        card_resolver = A2ACardResolver(httpx_client, agent)
        card = await card_resolver.get_agent_card()

        print("======= Agent Card ========")
        print(card.model_dump_json(exclude_none=True))

        notif_receiver_parsed = urllib.parse.urlparse(push_notification_receiver)
        notification_receiver_host = notif_receiver_parsed.hostname
        notification_receiver_port = notif_receiver_parsed.port

        client = A2AClient(httpx_client, agent_card=card)

        streaming = card.capabilities.streaming
        context_id = session if session > 0 else uuid4().hex

        print("=========  starting a new task ======== ")
        taskId = uuid4().hex
        await completeTask(
            client,
            streaming,
            use_push_notifications,
            notification_receiver_host,
            notification_receiver_port,
            taskId,
            context_id,
            prompt,
            file_path,
        )



async def completeTask(
    client: A2AClient,
    streaming,
    use_push_notifications: bool,
    notification_receiver_host: str,
    notification_receiver_port: int,
    taskId,
    contextId,
    prompt: str,
    file_path: str,
):
    if prompt == ":q" or prompt == "quit":
        return False, None, None

    message = Message(
        role="user",
        parts=[TextPart(text=prompt)],
        messageId=str(uuid4()),
        taskId=taskId,
        contextId=contextId,
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

    if use_push_notifications:
        payload["pushNotification"] = {
            "url": f"http://{notification_receiver_host}:{notification_receiver_port}/notify",
            "authentication": {
                "schemes": ["bearer"],
            },
        }

    taskResult = None
    message = None
    if streaming:
        response_stream = client.send_message_streaming(
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
                message = event
            print(f"stream event => {event.model_dump_json(exclude_none=True)}")
        # Upon completion of the stream. Retrieve the full task if one was made.
        if taskId:
            taskResult = await client.get_task(
                GetTaskRequest(
                    id=str(uuid4()),
                    params=TaskQueryParams(id=taskId),
                )
            )
            taskResult = taskResult.root.result
    else:
        try:
            # For non-streaming, assume the response is a task or message.
            event = await client.send_message(
                SendMessageRequest(
                    id=str(uuid4()),
                    params=payload,
                )
            )
            event = event.root.result
        except Exception as e:
            print("Failed to complete the call", e)
        if not contextId:
            contextId = event.contextId
        if isinstance(event, Task):
            if not taskId:
                taskId = event.id
            taskResult = event
        elif isinstance(event, Message):
            message = event

    if message:
        print(f"\n{message.model_dump_json(exclude_none=True)}")
        return True, contextId, taskId
    if taskResult:
        # Don't print the contents of a file.
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
        ## if the result is that more input is required, loop again.
        state = TaskState(taskResult.status.state)
        if state.name == TaskState.input_required.name:
            return (
                await completeTask(
                    client,
                    streaming,
                    use_push_notifications,
                    notification_receiver_host,
                    notification_receiver_port,
                    taskId,
                    contextId,
                ),
                contextId,
                taskId,
            )
        ## task is complete
        return True, contextId, taskId
    ## Failure case, shouldn't reach
    return True, contextId, taskId


# 作为脚本运行时调用
if __name__ == "__main__":
    async def main():
        agent = "http://localhost:10005"
        session = 0
        history = False
        use_push_notifications = False
        push_notification_receiver =  "http://localhost:5000"
        header  = [
            "X-A2A-Client-Name=Python-Client",
            "X-A2A-Client-Version=1.0.0",
        ]
        prompt = "北京的今天的天气是?"
        file_path = ""
        await cli(agent, session, history, use_push_notifications, push_notification_receiver, header,  prompt, file_path)
    asyncio.run(main())
