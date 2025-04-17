from fastapi import FastAPI, UploadFile, File
from typing import List
import uuid

app = FastAPI()

# Структура для хранения изображений с ID
images_db = []

@app.post("/upload-images/")
async def upload_images(files: List[UploadFile] = File(...)):
    global images_db
    images_db.clear()  # Очищаем предыдущие данные, если нужно

    for index, file in enumerate(files):
        image_id = str(uuid.uuid4())  # Генерация уникального ID
        content = await file.read()   # Читаем содержимое файла

        # Сохраняем в "базу"
        images_db.append({
            "index": index,       # Чтобы сохранить порядок
            "id": image_id,       # Уникальный идентификатор
            "filename": file.filename,
            "content": content    # Можно сохранить путь, если сохраняете на диск
        })

    return {
        "message": "Файлы получены",
        "images": [{"index": img["index"], "id": img["id"], "filename": img["filename"]} for img in images_db]
    }
