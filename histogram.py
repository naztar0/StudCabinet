from PIL import Image, ImageDraw, ImageFont, ImageOps

width = 1000
height = 563
max_line_height = 25 * height // 100  # padding on top
#                 ^ padding percentage


def histogram(line_count, percent, name_text, full_name=None):
    factor = 100 // max(percent)
    line_width = width // line_count // 2  # column width

    im = Image.open("media/bg3.jpg")  # open background image
    draw = ImageDraw.Draw(im)   # draw method initialization
    fnt = ImageFont.truetype('fonts/Rubik-Bold.ttf', int(line_width / 1.5))    # font for integers
    fnt_txt = ImageFont.truetype('fonts/Rubik-Bold.ttf', int(line_width / 3))  # font for left-side text
    fnt_fio = ImageFont.truetype('fonts/Rubik-Regular.ttf', 25)                # font for full name

    if full_name:
        draw.multiline_text((5, 5), text=full_name, fill=(150, 150, 150), font=fnt_fio)  # draw full name
        #                   ^ top left side              ^ grey color

    step = width / (line_count + 1)  # column spacing

    for i in range(1, line_count + 1):  # while cols are
        color = (230 - i * 20, 0 + i * 10, 150 + i * 10)  # color gradient
        color_inner = (color[0] - 20, color[1] - 20, color[2] - 20)  # a little darker color than on column
        color_text = (color[0] + 100, color[1] + 100, color[2] + 100)  # a little lighter color than on column
        line_height = percent[i - 1] * (height - max_line_height) / 100 * factor  # column height in px, calculated in proportion
        x = i * step  # X column coordinate
        draw.line(((x, height), (x, height - line_height + line_width / 2)), fill=color, width=line_width + 1)  # draw column
        #          ^ 1-st point ^ 2-nd point, subtracted from height because OX-mirroring is necessary
        draw.ellipse(((x - line_width / 2, height - line_height), (x + line_width / 2, height - line_height + line_width)), fill=color)
        k = 2.5  # inner circle radius coefficient [1..inf]
        draw.ellipse(((x - line_width / (k * 2), height - line_height + (line_width - (line_width / k)) / 2),
                      (x + line_width / (k * 2), height - line_height + (line_width + (line_width / k)) / 2)), fill=color_inner)  # draw inner circle

        text_k = 0.85  # text shift coefficient [0..1]
        text_vertical_shift = height - line_height - (line_width * text_k)  # space between column and top integer
        num_text = str(percent[i - 1])  # top integer
        if len(num_text) == 1:
            num_text = '  ' + num_text
        draw.text((x - (line_width / 2), text_vertical_shift), text=num_text, fill=color, font=fnt)  # draw top integer
        #              ^ center of integer

        # line abbreviation depending on its length and font size
        txt_height_coefficient = len(name_text[i - 1]) * (line_width + 5)
        if txt_height_coefficient > 2500:
            name_text[i - 1] = name_text[i - 1][:int(2500 / txt_height_coefficient * len(name_text[i - 1]))] + "..."
        
        txt = Image.new('L', (len(name_text[i - 1]) * 25, 60))  # blank for vertical left-side text
        draw_text = ImageDraw.Draw(txt)                         # draw method initialization
        draw_text.text((0, 0), text=str(name_text[i - 1]), fill=255, font=fnt_txt)  # drawing left-side text
        vert_text = txt.rotate(90, expand=1)  # rotating text
        im.paste(ImageOps.colorize(vert_text, (0, 0, 0), color_text),
                 (int(x - line_width), int(height - len(name_text[i - 1]) * 25.3)),  vert_text)  # pasting rotated text
        #                                           ^ subtracting text length to get a start of pasted pattern

    im.save("media/img.png")
