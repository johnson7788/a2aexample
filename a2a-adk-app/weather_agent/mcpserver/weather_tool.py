#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Date  : 2025/4/29 (Modified: 2025-04-22)
# @File  : rag_tool.py
# @Author: johnson
# @Contact : github: johnson7788
# @Desc  : eg: 天气工具
import time
from fastmcp import FastMCP
import random

mcp = FastMCP("天气查询工具")

@mcp.tool()
def QueryCityWeather(city: str) -> str:
    """
    根据城市查询天气
    :param city: 城市名称
    :return:
    """
    weathers = ["晴朗, 25摄氏度", "多云, 18摄氏度",  "雨, 15摄氏度", "雪, -5摄氏度", "雷阵雨, 20摄氏度"]
    weather = random.choice(weathers)
    return weather

if __name__ == '__main__':
    result = QueryCityWeather(city="Beijing")
    print(result)