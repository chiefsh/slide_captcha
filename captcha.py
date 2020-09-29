import logging
import random
from PIL import Image, ImageFilter
from io import BytesIO
import requests

SQUARE_SIZE = 50
CIRCLE_SIZE = 20
SQUARE_UP_DOWN = ["up", "down"]
SQUARE_LEFT_RIGHT = ["left", "right"]
THUMB = (260, 160)

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
    if x <= i <= h and y <= j <= z:
        a, b = abs(center[0] - i), abs(center[1] - j)
        if (a**2 + b**2) <= (CIRCLE_SIZE // 2)**2:
            return True
    return False


def get_cutout(img):
    # 获取正方形区域
    width, height = img.size
    l = random.randint(width // 3, width - SQUARE_SIZE - CIRCLE_SIZE)
    u = height // 2
    r, d = l + SQUARE_SIZE, u + SQUARE_SIZE
    # 确定两个圆形的坐标
    circles = random_circle_location(l, u)

    # 创建空白图
    bg = Image.new("L", (width, height))
    if bg.mode != "RGBA":
        bg = bg.convert("RGBA")

    _, _, _, alpha = bg.split()
    alpha = alpha.point(lambda i: i > 0 and 1)
    bg.putalpha(alpha)

    n = random.randint(0, 1)
    for i in range(width):
        for j in range(height):
            # 判断是否在圆形内, n为外部圆 or 判断是否在正方形内
            if check_in_circle(circles[n], i, j, "out") or (l <= i <= r and u <= j <= d):
                # 内部圆需要做排除
                if check_in_circle(circles[abs(1 - n)], i, j, "inner"):
                    continue
                rgb = img.getpixel((i, j))
                # 更新bg上的像素rgba值
                bg.putpixel((i, j), rgb)
                # 修改原图抠图位置的rgba值阴影化
                img.putpixel((i, j), (rgb[0] - 50, rgb[1] - 50, rgb[2] - 50, 0))

    bg = bg.crop((l - CIRCLE_SIZE // 2 - 2, u - CIRCLE_SIZE // 2 - 2, l + SQUARE_SIZE + CIRCLE_SIZE // 2 + 2,
                     u + SQUARE_SIZE + CIRCLE_SIZE // 2 + 2))

    # bg = bg.filter(ImageFilter.BoxBlur)
    bg = bg.filter(ImageFilter.UnsharpMask)

    img.save("1.png")
    bg.save("2.png")

    # 转二进制
    org_buf = BytesIO()
    bg_buf = BytesIO()
    img.save(org_buf, format='PNG')
    bg.save(bg_buf, format='PNG')

    icon_center = (l+SQUARE_SIZE//2, u+SQUARE_SIZE//2)
    return icon_center, org_buf.getvalue(), bg_buf.getvalue()


def get_captcha():
    pil_img = Image.open('snap.png')
    pil_img = pil_img.resize((THUMB[0], THUMB[1]), Image.LANCZOS)
    get_cutout(pil_img.copy())


def get_captcha_by_url(url):
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
    get_captcha_by_url(SOURCE_IMG[0])