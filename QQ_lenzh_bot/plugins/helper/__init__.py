from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment


# /support 指令，打印github源代码地址
sup_cmd = on_command("support", aliases={"support"}, priority=5, block=True)

# /help 指令，打印所有的指令及其用法
help_cmd = on_command("help", aliases={"help"}, priority=5, block=True)

# /support 指令
@sup_cmd.handle()
async def _(args: Message = CommandArg()):
    await sup_cmd.finish("本插件的源码托管在GitHub: https://github.com/Lenzhzh/qq-latexmd-bot, \n 支持lenzh喵 ~ 打个star喵！")

# /help 帮助
@help_cmd.handle()
async def _(args: Message = CommandArg()):
    await help_cmd.finish("用法: \n"
    "    /md 你的Markdown文本 \n"
    "    /tex 你的LaTeX(支持 $...$ 或 $$...$$) \n"
    "    /support 查看插件源码地址 \n"
    "    /help 查看帮助信息 \n"
    "    /jm 下载jm车牌号并压缩，传入到群文件（慎用） \n" 
    "    /file 下载网页文件并发送至群文件（慎用）\n" 
    "    /get_avatar 获取头像 \n")
