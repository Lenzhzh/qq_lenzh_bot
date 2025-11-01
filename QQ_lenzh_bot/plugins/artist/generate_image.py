
import requests
import base64
import os
 
# 设置API基本信息
API_URL = "https://api.siliconflow.cn/v1/images/generations"
API_KEY = "sk-wwmwpsuzwnkppckrgnwyzxrmyobsivlctpkwqwjxtscykzyy"

def encode_image_to_base64(image_path):
    """将本地图片编码为Base64字符串"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")
 
# def save_image_url(image_url, output_folder, output_filename):
#     """保存图片URL到本地文件"""
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     output_path = os.path.join(output_folder, output_filename)
#     with open(output_path, "w") as file:
#         file.write(image_url)
#     print(f"图片URL已保存至：{output_path}")
 
# def download_image(image_url_dict, output_folder, output_filename):
#     """下载并保存图片到本地"""
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
 
#     # 提取 URL 字典中的实际 URL
#     image_url = image_url_dict['url'] if isinstance(image_url_dict, dict) else image_url_dict
 
#     output_path = os.path.join(output_folder, output_filename)
#     response = requests.get(image_url)
#     if response.status_code == 200:
#         with open(output_path, "wb") as file:
#             file.write(response.content)
#         print(f"图片已下载并保存至：{output_path}")
#     else:
#         raise Exception(f"图片下载失败，状态码：{response.status_code}")
    
def generate_DongZhuo(avatar_url_1, avatar_url_2):
    """生成董卓图片"""

    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {API_KEY}",
        "content-type": "application/json"
    }
    
    payload = {
        "model": "Qwen-Image-Edit-2509",
        "prompt": "做一个三格漫画，最上边一行一格，下面一行左右两格。最上方格由第一张图的角色作为主角，角色流着眼泪，嘴巴却禁闭，幽怨的盯着镜头，对话框内：“……”。左下角的第二格依然由第一张图的角色作为主角，角色悔恨的流着眼泪，哭泣着询问：“你，你可有何话说？”。右下角的第三格由第二张图的角色作为主角，角色带着决绝的表情，有一根绳子从上方系在他的脖子上，他闭着眼神情庄重的回复到：“再无话说，请速动手！”，整体采用黑白画风，所有对话发生在对话框内，无重复内容，所有镜头以近身特写的方式表现，注意每格内的角色，我再次重复一遍，前两格为我发送的第一张图的角色，最后一格为我发送的第二张图的角色", # 描述您想如何编辑
        "image1": avatar_url_1,               # 背景图的Base64字符串
        "image2": avatar_url_2,     # 参考图的Base64字符串
        "n": 1,                              # 生成图片的数量，通常为1
        "size": "512x512",                 # 输出图片的尺寸，根据模型支持选择
        "response_format": "url"        # 响应格式，b64_json 表示返回Base64编码的图片
    }

    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()["images"]["url"]
    else :
        raise Exception(f"图片生成失败，状态码：{response.status_code}，错误信息：{response.text}")


if __name__ == "__main__":
    # 示例头像URL
    avatar_url_1 = "http://q1.qlogo.cn/g?b=qq&nk=2425985947&s=640"
    avatar_url_2 = "http://q1.qlogo.cn/g?b=qq&nk=2425985947&s=640"
    
    try:
        image_url = generate_DongZhuo(avatar_url_1, avatar_url_2)
        print(f"生成的董卓图片URL：{image_url}")
    except Exception as e:
        print(f"生成董卓图片失败: {e}")