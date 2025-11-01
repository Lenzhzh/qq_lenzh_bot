import datetime


def xor_pdf(file_path, date):
    try:
        with open(file_path, 'rb') as f:
            data = f.read()

        key = date.toordinal() % 256
        encrypted_data = bytearray(b ^ key for b in data)

        encrypted_file_path = f"{file_path[:-4]}"
        with open(encrypted_file_path, 'wb') as f:
            f.write(encrypted_data)

        print(f"✅ PDF加密成功：{encrypted_file_path}")

        return 
    
    except Exception as e:
        print(f"❌ PDF加密失败：{e}")
        return 


p = input("请输入PDF文件路径：")
d = input("请输入加密日期（YYYY-MM-DD）")
if d=="":
    d = datetime.date.today()
xor_pdf(p, d)