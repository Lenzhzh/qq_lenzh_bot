from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from .renderer import render_markdown_image, render_latex_image

# /md 指令：把后面的 Markdown 渲染为图片
md_cmd = on_command("md", aliases={"markdown"}, priority=5, block=True)

# /tex 指令：把后面的 LaTeX 渲染为图片（支持行内/块公式）
tex_cmd = on_command("tex", aliases={"latex"}, priority=5, block=True)


@tex_cmd.handle()
async def _(args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        # 对于用法错误，直接 finish
        await tex_cmd.finish("用法:/tex 你的LaTeX(支持 $...$ 或 $$...$$)")

    try:
        # 只把真正可能失败的渲染过程放进 try 块
        img_bytes = await render_latex_image(text)
    except Exception as e:
        # 如果渲染失败，捕获异常并 finish
        # 可以在这里加上更详细的日志记录，方便排查问题
        # from nonebot.log import logger
        # logger.exception(f"LaTeX 渲染失败，原文：{text}")
        await tex_cmd.finish(f"渲染失败: {e}")
        return # 确保在处理完异常后函数能退出

    # 如果代码能走到这里，说明渲染成功了，此时再 finish 发送图片
    await tex_cmd.finish(MessageSegment.image(img_bytes))

# /md 指令也建议做类似修改
@md_cmd.handle()
async def _(args: Message = CommandArg()):
    text = args.extract_plain_text().strip()
    if not text:
        await md_cmd.finish("用法:/md 你的Markdown文本")
        
    try:
        img_bytes = await render_markdown_image(text)
    except Exception as e:
        await md_cmd.finish(f"渲染失败:{e}")
        return
        
    await md_cmd.finish(MessageSegment.image(img_bytes))