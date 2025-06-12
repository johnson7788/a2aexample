import uuid
import httpx
from a2a.client import A2AClient
import asyncio
from a2a.types import (MessageSendParams, SendMessageRequest)


async def httpx_client():
    async with httpx.AsyncClient() as httpx_client:
        # 初始化客户端（确保base_url包含协议头）

        http_client = await A2AClient.get_client_from_agent_card_url(
            httpx_client, 'http://localhost:9000'  # 确保此处是完整 URL
        )

        # 生成唯一请求ID
        request_id = uuid.uuid4().hex

        # 构造消息参数
        send_message_payload = {
            'message': {
                'role': 'user',
                'parts': [{'type': 'text', 'text': 'how much is 10 UsD in INR?'}],
                'messageId': request_id
            }
        }

        # 创建请求对象
        request = SendMessageRequest(
            id=request_id,
            params=MessageSendParams(**send_message_payload) )

        # 发送请求
        response = await http_client.send_message(request)
        print(response)




asyncio.run(httpx_client())

#https://www.a2aprotocol.net/zh/docs/a2a-python-sdk-basic