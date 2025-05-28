from PIL import Image

def convert_png_to_ico(png_file_path, ico_file_path):
    with Image.open(png_file_path) as img:
        img.save(ico_file_path, format="ICO")

if __name__ == "__main__":
    png_file = "icons\\app_icon.png"
    ico_file = "icons\\app_icon.ico"

    convert_png_to_ico(png_file, ico_file)
    print(f"图片已成功转换，路径：{ico_file}。")
