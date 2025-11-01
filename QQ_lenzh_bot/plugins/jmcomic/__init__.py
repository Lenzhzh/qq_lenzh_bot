import os
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,Message, GroupMessageEvent
from .downloader import downloader, daily_downloader
from .reflection import see_reflection_handler, reflection_handler

import random
import datetime


WHITE_LIST_GROUP = [778032966, 466810500]  # 允许使用该插件的群号列表


# /jm 指令：下载 jmcomic 漫画
jm_comic = on_command("jm", priority=5, block=True)

# /daily 指令：下载 jmcomic 每日一漫
daily_comic = on_command("daily", priority=5, block=True)

# /reflection 指令： 传输读后感指令
reflection = on_command("reflection", priority=5, block=True)

# /see_reflection 指令： 查看读后感指令
see_reflection = on_command("see_reflection", priority=5, block=True)


@jm_comic.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    await downloader(jm_comic, bot, event, args)
    await jm_comic.finish()
    

@daily_comic.handle()
async def _(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 固定群号才能使用每日一漫功能
    if not(event.group_id in WHITE_LIST_GROUP):
        await daily_comic.finish("❌ 每日一漫功能仅限特定群组使用，如有需要请联系管理员开通...")
        return 0
    
    await daily_downloader(daily_comic, bot, event, args)
    await daily_comic.finish()


@reflection.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    """根据当前日期，将读后感发送到本地每日一漫文件夹下"""
    # 固定群号才能使用每日一漫功能
    if not(event.group_id in WHITE_LIST_GROUP):
        await reflection.finish("❌ 每日一漫功能仅限特定群组使用，如有需要请联系管理员开通...")
        return 0
    await reflection_handler(reflection, event, args)
    await reflection.finish()


@see_reflection.handle()
async def _(event: GroupMessageEvent, args: Message = CommandArg()):
    """查看特定日期的读后感"""
    # 固定群号才能使用每日一漫功能 
    if not(event.group_id in WHITE_LIST_GROUP):
        await see_reflection.finish("❌ 每日一漫功能仅限特定群组使用，如有需要请联系管理员开通...")
        return 0
    await see_reflection_handler(see_reflection, event, args)
    await see_reflection.finish()
