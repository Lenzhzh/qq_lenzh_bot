import os
from pathlib import Path
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,Message, GroupMessageEvent
from .downloader import downloader

import random
import datetime


async def reflection_handler(reflection, event: GroupMessageEvent, args: Message = CommandArg()):
    """根据当前日期，将读后感发送到本地每日一漫文件夹下"""
    text = args.extract_plain_text().strip()
    if not text:
        await reflection.finish("请提供读后感内容哦！")
        return

    today = datetime.date.today()
    daily_dir = f"./comic_daily/{today}/relection"
    
    dir = f"./comic_daily/{today}/"
    if (os.path.exists(dir) == False):
        await reflection.finish("今日还没有下载每日一漫哦，无法提交读后感~")
        return
    
    # 创建目录（如果不存在）
    os.makedirs(daily_dir, exist_ok=True)

    user_qq = event.get_user_id()
    reflection_file_path = f"{daily_dir}/reflection_{user_qq}.txt"

    # 将读后感内容写入文件，追加模式
    with open(reflection_file_path, 'a', encoding='utf-8') as f:
        f.write(text + "\n")

    await reflection.finish("读后感已保存，谢谢分享！")
    return 


async def see_reflection_handler(see_reflection, event: GroupMessageEvent, args: Message = CommandArg()):
    """查看特定日期的读后感"""
    text = args.extract_plain_text().strip()
    target_time = datetime.date.today()
    try:
        target_time = datetime.datetime.strptime(text, "%Y-%m-%d").date()
    except :
        pass # 默认今天日期

    daily_dir = f"./comic_daily/{target_time}/relection"

    if not os.path.exists(daily_dir):
        await see_reflection.finish("该日期没有读后感记录哦！")
        return

    target_qq = ""

    # 获取@的目标qq_id
    for seg in args:
        if seg.type == "at":
            # 提取 @ 的 QQ 号
            target_qq = seg.data.get("qq")
            break # 找到第1个 @ 停止

    # 如果没有 @, 则获取发送者自己的 QQ 号
    if not target_qq:
        target_qq = event.get_user_id()
        await see_reflection.send("用法 @xxx 获取读后感，无则获取自己的读后感~")
    
    # 特殊处理 @全体成员 的情况
    if target_qq == "all":
        await see_reflection.finish("无法获取全体成员的读后感哦~")
        return

    # 获取目标用户的读后感文件路径，如果存在则读取内容
    reflection_file_path = f"{daily_dir}/reflection_{target_qq}.txt"
    reflections = []

    if os.path.exists(reflection_file_path):
        with open(reflection_file_path, 'r', encoding='utf-8') as f:
            reflections = f.readlines()
            reflections = [line.strip() for line in reflections if line.strip()]

    if reflections:
        await see_reflection.send("\n".join(reflections))
    else:
        await see_reflection.finish("该用户今天还没有提交读后感哦！")