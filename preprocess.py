import os
from PIL import Image
from ultralytics import YOLO
import json
import tqdm
import torch
from captions import create_garment_caption, create_model_caption
from utils import resize_and_crop
import time
os.environ["YOLO_VERBOSE"] = "False"

# -- Dataset structure --
#
# dataset/
# ├── train/
# │   ├── cloth/
# │   └── image/
# ├── test/
# ├── test_pairs.txt
# ├── train_pairs.txt
# └── verify_pairs.txt

dataset_name = "dataset"
train_path = os.path.join(dataset_name, "train")
train_cloth_path = os.path.join(train_path, "cloth")
train_image_path = os.path.join(train_path, "image")
test_path = os.path.join(dataset_name, "test")
test_cloth_path = os.path.join(test_path, "cloth")
test_image_path = os.path.join(test_path, "image")

os.makedirs(dataset_name, exist_ok=True)
os.makedirs(train_path, exist_ok=True)
os.makedirs(train_cloth_path, exist_ok=True)
os.makedirs(train_image_path, exist_ok=True)
os.makedirs(test_path, exist_ok=True)
os.makedirs(test_cloth_path, exist_ok=True)
os.makedirs(test_image_path, exist_ok=True)

debug = True

if debug:
    debug_image_path = os.path.join(dataset_name, "debug")
    os.makedirs(debug_image_path, exist_ok=True)

raw_data_path = "test"

model = YOLO("yolov8x-world.pt", verbose=False)
model.to("cuda")
train_split = 0.8

model.set_classes(["Garment", "Accesory", "Person"])

# txt files
train_pairs = open(os.path.join(dataset_name, "train_pairs.txt"), "w")
test_pairs = open(os.path.join(dataset_name, "test_pairs.txt"), "w")

for i, root in tqdm.tqdm(enumerate(os.listdir(raw_data_path)), total=len(os.listdir(raw_data_path))):

    time_start = time.time()

    images = [name for name in os.listdir(os.path.join(raw_data_path, root)) if name.endswith(".jpg")]
    info = json.load(open(os.path.join(raw_data_path, root, "info.json")))
    info_txt = open(os.path.join(raw_data_path, root, "info.json"), "r").read()

    if len(images) <= 2:
        print("No hay suficientes imágenes en", root)
        continue

    if i <= train_split * len(os.listdir(raw_data_path)):
        split = "train"
    else:
        split = "test"
    
    # Detectar: la prenda y la persona
    #model.set_classes([info["title"], "Person"])

    # Agregar todas las personas 
    smallest_area = float("inf")
    smallest_area_image = None
    model_images = []

    for image in images:

        image_path = os.path.join(raw_data_path, root, image)
        results = model.predict(image_path)

        if debug:
            results[0].save(os.path.join(debug_image_path, image))
        
        if len(results) == 0:
            print(f"No se detectó nada en {image_path}")
            continue
        
        result = results[0]
        boxes = result.boxes

        # A veces se detecta person en garments, usar un threshold distinto para personas
        person_idx = (boxes.cls == 2.0).nonzero().squeeze()
        person_conf = 0.0
        if person_idx.numel() != 0:
            person_conf = boxes.conf[person_idx].item()
        
        if torch.tensor(2.0) in boxes.cls and person_conf > 0.7:
            # Guardar todas las fotos de personas: Si detecta una persona o no detecta la prenda
            model_images.append(image)
        
        elif torch.tensor(0.0) in boxes.cls:

            if boxes.cls.numel() > 1:
                garment_idx = ((boxes.cls == 0.0) | (boxes.cls == 1.0)).nonzero().squeeze()
                area = boxes[garment_idx].xywh[:, 2] * boxes[garment_idx].xywh[:, 3]
            else:
                area = boxes.xywh[:, 2] * boxes.xywh[:, 3]

            if area < smallest_area:
                smallest_area = area
                smallest_area_image = image
        else:
            print(f"No se detectó la prenda en {image_path}")
            continue

        if len(model_images) == 0:
            print(f"No se detectó ninguna persona en {image_path}")
            continue
    
    # Guardar las imágenes y generar sus caption
    if smallest_area_image is not None:
        # Guardar garment
        img = resize_and_crop(Image.open(os.path.join(raw_data_path, root, smallest_area_image)))
        img.save(os.path.join(dataset_name, split, "cloth", smallest_area_image))
        caption = create_garment_caption(info_txt)
        with open(os.path.join(dataset_name, split, "cloth", f"{smallest_area_image}.txt"), "w") as f:
            f.write(caption)

        # Guardar cada model image
        for model_image in model_images:
            img = resize_and_crop(Image.open(os.path.join(raw_data_path, root, model_image)))
            img.save(os.path.join(dataset_name, split, "image", model_image))

            # Generar caption
            caption = create_model_caption(os.path.join(dataset_name, split, "image", model_image))
            with open(os.path.join(dataset_name, split, "image", f"{model_image}.txt"), "w") as f:
                f.write(caption)

            # Agregarlas al txt
            if split == "train":
                train_pairs.write(f"{smallest_area_image} {model_image}\n")
            else:
                test_pairs.write(f"{smallest_area_image} {model_image}\n")

    else:
        print(f"No se detectó la prenda en {root}")
        continue

    total_time = time.time() - time_start
    print(f"Total: {total_time:.2f} s, por imagen: {total_time / len(images):.2f} s")
