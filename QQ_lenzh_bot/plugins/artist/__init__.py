import os
from nonebot import on_command
from nonebot.rule import to_me
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,Message, MessageSegment, Event, GroupMessageEvent

# rule=to_me() 表示只有 @bot 或者以 bot 昵称开头才会响应
# priority 设置响应优先级
# block=True 表示如果这个命令被响应，后续的处理器将不再处理

get_avatar = on_command("get_avatar", priority=5, block=True)

DongZhuo = on_command("DZ", priority=5, block=True)

s_file = on_command("file", priority=5, block=True)




@get_avatar.handle()
async def _(event: Event, args: Message = CommandArg()):
    target_qq = ""

    # 解析参数：检查消息中是否包含 @
    for seg in args:
        if seg.type == "at":
            # 提取 @ 的 QQ 号
            target_qq = seg.data.get("qq")
            break # 找到第1个 @ 停止

    # 如果没有 @, 则获取发送者自己的 QQ 号
    if not target_qq:
        target_qq = event.get_user_id()
        await get_avatar.send("用法 @xxx 获取头像，无则获取自己的头像~")

    # 特殊处理 @全体成员 的情况
    if target_qq == "all":
        await get_avatar.finish("无法获取全体成员的头像哦~")
        return
    # 构建头像 URL
    avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={target_qq}&s=640"

    await get_avatar.finish(MessageSegment.image(avatar_url))


# @DongZhuo.handle()
# async def _(event: Event, args: Message = CommandArg()):
#     """
#     处理合成董卓图片命令
#     """
#     async def get_avatar():
#         target_qq = ""

#         # 解析参数：检查消息中是否包含 @
#         for seg in args:
#             if seg.type == "at":
#                 # 提取 @ 的 QQ 号
#                 target_qq = seg.data.get("qq")
#                 break # 找到第1个 @ 停止

#         # 如果没有 @, 则获取发送者自己的 QQ 号
#         if not target_qq:
#             target_qq = event.get_user_id()

#         # 特殊处理 @全体成员 的情况
#         if target_qq == "all":
#             await DongZhuo.finish("无法获取全体成员的头像哦~")
#             return

#         # 构建头像 URL
#         avatar_url = f"http://q1.qlogo.cn/g?b=qq&nk={target_qq}&s=640"

#         return avatar_url

#     avatar_url_1 = await get_avatar()
#     avatar_url_2 = await get_avatar()

#     try:
#         image_url = generate_dongzhuo(avatar_url_1, avatar_url_2)
#         await DongZhuo.finish(MessageSegment.image(image_url))
#         return 
    
#     except Exception as e:
#         await DongZhuo.finish(f"生成董卓图片失败: {e}")
#         return
    

@s_file.handle()
async def __(bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    path = args.extract_plain_text().strip()
    # 检查文件是否存在
    if not path:
        await s_file.finish("用法 /file 你的文件路径(网络路径)")

    try:
        await bot.send(event, "正在上传文件，请稍候...")

        # if (path!="qq_latexmd_bot\\plugins\\artist\\Downloads.zip"):
        #     await s_file.finish("你要寄吧干嘛？")
        #     return 
        
        path = os.path.abspath(path)

        # 如果是本地文件则拒绝
        if os.path.isfile(path):
            await s_file.finish("只能上传网络文件哦~")
            return

        # NapCatQQ API
        await bot.upload_group_file(
            group_id=event.group_id,
            file=str(path),    # 文件路径，可以是本地路径或网络路径
            name=os.path.basename(path)  # 文件名
        )

        await bot.send(event, "文件上传成功！请在群文件中查看。")

    except Exception as e:
        await s_file.finish(f"文件上传失败: {e}")
        return

    await s_file.finish()




