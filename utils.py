from PIL import Image

def resize_and_crop(image, target_width=768, target_height=1024):
    aspect_ratio = image.width / image.height
    new_height = int(target_width / aspect_ratio)
    resized_image = image.resize((target_width, new_height), Image.LANCZOS)

    left = 0
    top = (new_height - target_height) // 2
    right = target_width
    bottom = top + target_height
    cropped_image = resized_image.crop((left, top, right, bottom))
    return cropped_image

if __name__ == "__main__":
    image = Image.open("/workspace1/pdawson/tryon-scraping/test/1239914003/4d6d7ce19cb9220388adc36ce9ef8eebbbef9a02.jpg")
    cropped_image = resize_and_crop(image)
    cropped_image.save("test_cropped.jpg")