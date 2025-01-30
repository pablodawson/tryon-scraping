from dotenv import load_dotenv
import os
from anthropic import Anthropic
import base64
from PIL import Image
from io import BytesIO
import json
load_dotenv()

client = Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY"),  # This is the default and can be omitted
)

def create_model_caption(model_image_path):

    image1_media_type = "image/jpeg"

    # Resize manteniendo aspect ratio
    img = Image.open(model_image_path)
    
    ratio = 512.0 / img.size[0]
    new_size = (512, int(img.size[1] * ratio))
    resized_img = img.resize(new_size)
    resized_img.save("test.jpg")

    buffer = BytesIO()
    resized_img.save(buffer, format="JPEG")
    image1_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    instruction = open("instructions_model.txt", "r").read()

    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": image1_media_type,
                            "data": image1_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": instruction
                    }
                ],
            }
            ])
    
    return message.content[0].text

def create_garment_caption(garment_info):

    instruction = open("instructions_garment.txt", "r").read()
    instruction += "\n" + garment_info

    message = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": instruction
                    }
                ],
            }
            ])
    
    return message.content[0].text

def create_garment_caption_manual(garment_info):

    caption = ""
    
    if 'description' in garment_info:
        description = garment_info["description"]
    else:
        description = garment_info["title"]
    
    if 'color' in garment_info:
        caption = f"A {garment_info['color']} {description}"
    else:
        caption = f"A {description}"
    
    attrs = []
    caption += " It is "
    if 'Length: ' in garment_info:
        attrs.append(f"of {garment_info['Length: '].lower()} length")
    if 'Sleeve Length: ' in garment_info:
        attrs.append(f"{garment_info['Sleeve Length: '].lower()} sleeves")
    if 'Fit: ' in garment_info:
        attrs.append(f"the fit is {garment_info['Fit: '].lower()}")
    if 'Neckline: ' in garment_info:
        attrs.append(f"and has {garment_info['Neckline: '].lower()}")
    
    if attrs:
        caption += ". " + " , ".join(attrs)
    
    return caption.strip()

if __name__ == "__main__":
    #image_path = "/workspace1/pdawson/tryon-scraping/dataset/train/image/42f424b0d0942b62536d9359bca92483f749353b.jpg"
    #print(create_model_caption(image_path))
    garment_info_path = "/workspace1/pdawson/tryon-scraping/test/1228404006/info.json"
    garment_info = open(garment_info_path).read()
    print(create_garment_caption(garment_info))