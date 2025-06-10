#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/4/29 (Modified: 2025-04-22)
# @File  : rag_tool.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  : eg: 邮编
import time
import random
from fastmcp import FastMCP

mcp = FastMCP("获取某个地区的邮编")

@mcp.tool()
def QueryCityPostCode(city: str) -> str:
    """
    模拟根据地址返回邮编。
    :param city: 城市名称
    :return:
    """

    """
    由于没有实际的地址-邮编数据库，这里返回一个随机邮编。
    """
    print(f"正在尝试获取地址 '{city}' 的邮编...")
    zip_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
    return zip_code

if __name__ == '__main__':
    result = QueryCityPostCode(city="Beijing")
    print(result)