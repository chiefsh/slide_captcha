import logging
import random
from PIL import Image, ImageFilter
from io import BytesIO
import requests

SQUARE_SIZE = 50       # 正方形的边长
CIRCLE_SIZE = 20       # 圆形的直径
SHADOW_PEX = 70        # 阴影处理减弱的像素值

# 随机获取半圆出现的方向
SQUARE_UP_DOWN = ["up", "down"]
SQUARE_LEFT_RIGHT = ["left", "right"]

# 验证码图片尺寸
THUMB = (260, 160)

# 源图远程地址
SOURCE_IMG = [
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/c2/9c/49c17eac-4f2a-48e8-9804-03dd5370c0ec.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/a7/40/4eb76a26-7f1b-4c1c-99a7-d217fef08fe4.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/99/90/827ebe96-ac9b-4005-b8bc-c2638d975b0a.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/f2/f8/e774737f-3e2d-46b7-a474-8249c9fa9978.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/64/5b/155bac49-1664-45e1-ba90-a8c3af1498cf.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/f8/8a/04b547dc-1cc1-4a64-ae65-cee2e92b24df.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/95/5f/b5bb3272-2389-47d2-bbb1-498b90fa8ee6.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/a1/59/b17af22d-72ae-40ba-87f5-65674fc3176a.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/a6/d0/4b343df2-8609-4944-a51c-5f4eb73cbc3f.png",
    "https://cloudwork.oss-cn-beijing.aliyuncs.com/startup/2e/5e/d048caf1-9be9-4d93-a56f-8c5344eabdc6.png",
]

logger = logging.getLogger(__name__)


# 根据正方形出现的位置（x, y）计算半圆型出现的位置
def random_circle_location(x, y):
    up_down = random.choice(SQUARE_UP_DOWN)
    mx = x + random.randint(10, SQUARE_SIZE - CIRCLE_SIZE - 5)
    if up_down == "up":
        my = y - CIRCLE_SIZE // 2
    else:
        my = y + SQUARE_SIZE - CIRCLE_SIZE // 2
    left_right = random.choice(SQUARE_LEFT_RIGHT)
    ny = y + random.randint(10, SQUARE_SIZE - CIRCLE_SIZE - 5)
    if left_right == "left":
        nx = x - CIRCLE_SIZE // 2
    else:
        nx = x + SQUARE_SIZE - CIRCLE_SIZE // 2
    circle1_center = (mx + CIRCLE_SIZE//2, my + CIRCLE_SIZE // 2)
    circle2_center = (nx + CIRCLE_SIZE//2, ny + CIRCLE_SIZE // 2)
    return (mx, my, up_down, circle1_center), (nx, ny, left_right, circle2_center)


# 检查当前坐标是否在半圆形区域内
def check_in_circle(circle, i, j, direct):
    x, y, up_down, center = circle
    if direct == "out":
        if up_down == "left":
            x, y, h, z = x, y, x+CIRCLE_SIZE//2, y+CIRCLE_SIZE
        elif up_down == "up":
            x, y, h, z = x, y, x+CIRCLE_SIZE, y+CIRCLE_SIZE//2
        elif up_down == "right":
            x, y, h, z = x+CIRCLE_SIZE//2, y, x+CIRCLE_SIZE, y+CIRCLE_SIZE
        else:
            x, y, h, z = x, y+CIRCLE_SIZE//2, x+CIRCLE_SIZE, y+CIRCLE_SIZE
    else:
        if up_down == "left":
            x, y, h, z = x+CIRCLE_SIZE//2, y, x+CIRCLE_SIZE, y+CIRCLE_SIZE
        elif up_down == "up":
            x, y, h, z = x, y+CIRCLE_SIZE//2, x+CIRCLE_SIZE, y+CIRCLE_SIZE
        elif up_down == "right":
            x, y, h, z = x, y, x+CIRCLE_SIZE//2, y+CIRCLE_SIZE
        else:
            x, y, h, z = x, y, x+CIRCLE_SIZE, y+CIRCLE_SIZE//2
    # 上面的计算是为了进一步减少计算边长的范围
    if x <= i <= h and y <= j <= z:
        a, b = abs(center[0] - i), abs(center[1] - j)
        # 勾股定理
        if (a**2 + b**2) <= (CIRCLE_SIZE // 2)**2:
            return True
    return False


def get_cutout(img):
    # 获取随机的正方形区域
    width, height = img.size
    l = random.randint(width // 3, width - SQUARE_SIZE - CIRCLE_SIZE)
    u = height // 2
    r, d = l + SQUARE_SIZE, u + SQUARE_SIZE

    # 创建空白图
    bg = Image.new("L", (width, height))
    # 设置图片为RGBA模式
    if bg.mode != "RGBA":
        bg = bg.convert("RGBA")
    # 设置背景透明
    _, _, _, alpha = bg.split()
    alpha = alpha.point(lambda i: i > 0 and 1)
    bg.putalpha(alpha)

    # 确定两个圆形的坐标
    circles = random_circle_location(l, u)
    # 随机确定一个为内部圆(缺口)，一个为外部圆(凸出)
    n = random.randint(0, 1)
    for i in range(width):
        for j in range(height):
            # 判断是否在圆形内, n为外部圆 or 判断是否在正方形内
            if check_in_circle(circles[n], i, j, "out") or (l <= i <= r and u <= j <= d):
                # 内部半圆需要做排除
                if check_in_circle(circles[abs(1 - n)], i, j, "inner"):
                    continue
                rgb = img.getpixel((i, j))
                # 更新bg上的像素rgba值
                bg.putpixel((i, j), rgb)
                # 修改原图抠图位置的rgba值，阴影化
                img.putpixel((i, j), (rgb[0] - SHADOW_PEX, rgb[1] - SHADOW_PEX, rgb[2] - SHADOW_PEX, 0))

    # 扣出小图
    bg = bg.crop((l - CIRCLE_SIZE // 2 - 2, u - CIRCLE_SIZE // 2 - 2, l + SQUARE_SIZE + CIRCLE_SIZE // 2 + 2,
                     u + SQUARE_SIZE + CIRCLE_SIZE // 2 + 2))

    # 模糊处理
    bg = bg.filter(ImageFilter.UnsharpMask)

    # 返回正方形的中心坐标，验证码验证判断的依据
    icon_center = (l + SQUARE_SIZE // 2, u + SQUARE_SIZE // 2)

    # 保存到本地
    img.save("1.png")
    bg.save("2.png")

    # 返回二进制
    org_buf = BytesIO()
    bg_buf = BytesIO()
    img.save(org_buf, format='PNG')
    bg.save(bg_buf, format='PNG')

    return icon_center, org_buf.getvalue(), bg_buf.getvalue()


# 从本地源图片生成验证码
def get_captcha_by_local():
    pil_img = Image.open('snap.png')
    pil_img = pil_img.resize((THUMB[0], THUMB[1]), Image.LANCZOS)
    get_cutout(pil_img.copy())


# 从远端源图片生成验证码
def get_captcha_by_remote_url(url):
    res = requests.get(url)
    if res.status_code != 200:
        logger.error("get origin image error:%r", res.text)
        return ""
    content = res.content
    img = Image.open(BytesIO(content))
    img = img.resize((THUMB[0], THUMB[1]), Image.LANCZOS)
    get_cutout(img)


if __name__ == '__main__':
    # get_captcha()
    get_captcha_by_remote_url(SOURCE_IMG[1])