import datetime
import os
import random
import time
import yaml
from PIL import Image
import jmcomic
import os
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Bot,Message, GroupMessageEvent
from pathlib import Path
import subprocess
import zipfile
from nonebot.params import CommandArg
import shutil
import asyncio


def sorted_numeric_filenames(file_list):
    """对文件名按数字部分排序"""
    def extract_number(s):
        name, _ = os.path.splitext(s)
        return int(''.join(filter(str.isdigit, name)) or 0)
    return sorted(file_list, key=extract_number)

async def convert_images_to_pdf(input_folder, output_path, pdf_name):
    start_time = time.time()
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
    output_path = os.path.normpath(output_path)
    os.makedirs(output_path, exist_ok=True)
    pdf_full_path = os.path.join(output_path, f"{os.path.splitext(pdf_name)[0]}.pdf")

    image_iterator = []

    # 获取子目录并排序
    try:
        subdirs = sorted(
            [d for d in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, d))],
            key=lambda x: int(x) if x.isdigit() else float('inf')
        )
    except Exception as e:
        print(f"错误：无法读取目录 {input_folder}，原因：{e}")
        return

    for subdir in subdirs:
        subdir_path = os.path.join(input_folder, subdir)
        try:
            files = [f for f in os.listdir(subdir_path)
                     if os.path.isfile(os.path.join(subdir_path, f)) and os.path.splitext(f)[1].lower() in allowed_extensions]
            files = sorted_numeric_filenames(files)
            for f in files:
                image_iterator.append(os.path.join(subdir_path, f))
        except Exception as e:
            print(f"警告：读取子目录失败 {subdir_path}，原因：{e}")

    if not image_iterator:
        print("错误：未找到任何图片文件")
        return

    try:
        def open_image(path):
            img = Image.open(path)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img

        # 用生成器延迟加载，首张图用作 PDF 的 base 图
        image_iter = (open_image(p) for p in image_iterator)
        first_image = next(image_iter, None)

        if not first_image:
            print("错误：没有有效图片可生成PDF")
            return

        print(f"开始生成PDF：{pdf_full_path}")
        first_image.save(
            pdf_full_path,
            "PDF",
            save_all=True,
            append_images=[img for img in image_iter],
            optimize=True
        )
        print(f"✅ 成功生成PDF：{pdf_full_path}")

    except Exception as e:
        print(f"❌ 生成PDF失败：{e}")

    print(f"处理完成，耗时 {time.time() - start_time:.2f} 秒")

    return

async def xor_pdf(file_path, date):
    """对pdf进行简单异或加密（在后台线程执行阻塞文件操作）"""
    def _xor():
        try:
            with open(file_path, 'rb') as f:
                data = f.read()

            key = date.toordinal() % 256
            encrypted_data = bytearray(b ^ key for b in data)

            encrypted_file_path = f"{file_path}.xor"
            with open(encrypted_file_path, 'wb') as f:
                f.write(encrypted_data)

            print(f"✅ PDF加密成功：{encrypted_file_path}")
            return encrypted_file_path

        except Exception as e:
            print(f"❌ PDF加密失败：{e}")
            return None

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _xor)

async def downloader(jm_comic, bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    album_id = args.extract_plain_text().strip()

    if not album_id :
        await jm_comic.finish("用法: /jm 漫画ID (例如: /jm 350234)")
        return
    
    try:
        # 下载漫画
        try: 
            download_dir = Path(f"./comic_temp/{album_id}")
            if (os.path.exists(download_dir)):
                await bot.send(event, "⚠️ 相同的临时文件已存在，请不要发起多次请求...")
                return 0

            download_dir.mkdir(parents=True, exist_ok=True)
            
            result = subprocess.run(
                f"jmcomic {album_id}", 
                shell=True, 
                capture_output=True, 
                text=True,
                cwd=str(download_dir)
            )

            if result.returncode != 0:
                await bot.send(event, f"❌ 下载失败: {result.stderr.strip()}")
                return 0

        except Exception as e:
            await bot.send(event, f"❌ 下载失败 {e}") 
            return 0

        # 查找图片文件
        image_files = []
        for file in download_dir.rglob("*"):
            if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                image_files.append(file)
        
        if image_files:
            image_files.sort(key=lambda x: x.name)
            total_pages = len(image_files)

            # 创建pdf
            pdf_path = Path(f"./comic_temp/{album_id}.pdf")


            try:
                await convert_images_to_pdf(download_dir, pdf_path.parent, pdf_path.name)
                await xor_pdf(pdf_path, date=datetime.date.today())
            except Exception as e:
                print(f"❌ 出现问题 {e}")
                pass

            xor_pdf_path = Path(f"./comic_temp/{album_id}.pdf.xor")
            comic_name = f"comic_{album_id}_key_{datetime.date.today()}.pdf.xor"

            try:
                if (xor_pdf_path is None):
                    await bot.send(event, "❌ 加密失败，上传取消")

                await bot.upload_group_file(
                    group_id=event.group_id,
                    file=str(os.path.abspath(pdf_path)),
                    name=comic_name
                )

                await bot.send(event, f"✅ 上传成功 \n 总页数: {total_pages}")

            except Exception as e:
                await bot.send(event, f"❌ 上传失败{e}")
                return 0
            
            # 通过shutil强制删除临时文件夹
            try:
                shutil.rmtree(download_dir)
                pdf_path.unlink(missing_ok=True)
                xor_pdf_path.unlink(missing_ok=True)
            except Exception as e:
                await bot.send(event, f"⚠️ 清理临时文件失败 {e}")

        else:
            await bot.send(event, "❌ 未找到图片")
            return 0
            
    except Exception as e:
        await bot.send(event, f"❌ 处理失败 {e}")
        return 0
    

async def daily_downloader(daily, bot: Bot, event: GroupMessageEvent, args: Message = CommandArg()):
    # 以日期为种子，调用random生成comic_id
    today = datetime.date.today()
    random.seed(today.toordinal())

    async def generate_comic():
        album_id = random.randint(200000, 999999)
        
        res_dir = Path(f"./comic_daily/{datetime.date.today()}")
        if (id and os.path.exists(f"./comic_daily/{datetime.date.today()}")):
            xor_pdf_path = None
            for file in res_dir.rglob("*"):
                if file.suffix.lower() in ['.xor']:
                    xor_pdf_path = file
                    break
            
            # 已存在今日漫画，直接上传
            if (xor_pdf_path is not None):
                comic_name = f"comic_{album_id}_daily_{datetime.date.today()}.xor"
                try:
                    await bot.upload_group_file(
                        group_id=event.group_id,
                        file=str(os.path.abspath(xor_pdf_path)),
                        name=comic_name
                    )
                    await bot.send(event, f"✅ 今日漫画已存在，上传成功~")
                    return 0
                except Exception as e:
                    await bot.send(event, f"❌ 上传失败{e}，预料之外的错误，请联系管理员")
                    return 0

        try:
            # 下载漫画
            try: 
                download_dir = Path(f"./comic_temp/{album_id}")
                if not(os.path.exists(download_dir)):
                    download_dir.mkdir(parents=True, exist_ok=True)
                    
                    result = subprocess.run(
                        f"jmcomic {album_id}", 
                        shell=True, 
                        capture_output=True, 
                        text=True,
                        cwd=str(download_dir)
                    )

                    if result.returncode != 0:
                        await bot.send(event, f"❌ 下载失败: {result.stderr.strip()}")
                        return 0
                        
            except Exception as e:
                await bot.send(event, f"❌ 下载失败 {e}")
                return 0
            
            # 查找图片文件
            image_files = []
            for file in download_dir.rglob("*"):
                if file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                    image_files.append(file)

            if (image_files is None or len(image_files) == 0):
                # 此时说明下载失败，重新生成comic_id
                # 通过shutil强制删除临时文件夹
                try:
                    shutil.rmtree(download_dir)
                    pdf_path.unlink(missing_ok=True)
                    xor_pdf_path.unlink(missing_ok=True)
                except Exception as e:
                    pass
                    
                await generate_comic()
                return 0
            
            image_files.sort(key=lambda x: x.name)
            total_pages = len(image_files)

            # 创建pdf
            pdf_path = Path(f"./comic_daily/{datetime.date.today()}/jmcomic_{album_id}.pdf")

            try:
                await convert_images_to_pdf(download_dir, pdf_path.parent, pdf_path.name)
                await xor_pdf(pdf_path, date=datetime.date.today())
            except Exception as e:
                print(f"❌ 出现问题 {e}")
                pass

            xor_pdf_path = Path(f"{pdf_path}.xor")
            comic_name = f"comic_{album_id}_daily_{datetime.date.today()}.pdf.xor"

            try:
                if (xor_pdf_path is None):
                    await bot.send(event, "❌ 加密失败，上传取消")
                await bot.upload_group_file(
                    group_id=event.group_id,
                    file=str(os.path.abspath(xor_pdf_path)),
                    name=comic_name
                )
                await bot.send(event, f"✅ 上传成功 \n 总页数: {total_pages}")

            except Exception as e:
                await bot.send(event, f"❌ 上传失败{e}")
                return 0

            # 通过shutil强制删除临时文件夹
            try:
                shutil.rmtree(download_dir)
                await bot.send(f"✅ 清理成功~")
            except Exception as e:
                await bot.send(event, f"⚠️ 清理临时文件失败 {e}")
            
        except Exception as e:
            await bot.send(event, f"❌ 处理失败 {e}")
            return 0

    await generate_comic()