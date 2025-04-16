from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from google.cloud import firestore, storage
from google.api_core.exceptions import GoogleAPIError
import os

app = FastAPI()

# Константы
CREDENTIALS_PATH = 'credentials/service-account.json'
BUCKET_NAME = 'your-bucket-name'  # Замените на актуальное имя

# Инициализация клиентов
try:
    db = firestore.Client.from_service_account_json(CREDENTIALS_PATH)
    storage_client = storage.Client.from_service_account_json(CREDENTIALS_PATH)
except Exception as e:
    raise RuntimeError(f'Ошибка инициализации GCP клиентов: {e}')


# Загрузка изображения в Cloud Storage
def upload_image(image_file: UploadFile) -> str:
    try:
        bucket = storage_client.bucket(BUCKET_NAME)
        blob = bucket.blob(image_file.filename)
        blob.upload_from_file(image_file.file, content_type=image_file.content_type)
        return blob.public_url
    except GoogleAPIError as e:
        raise HTTPException(status_code=500, detail=f'Ошибка загрузки изображения: {e}')


# Сохранение метаданных в Firestore
def save_image_metadata(image_url: str, description: str) -> str:
    try:
        doc_ref = db.collection('exit').add({
            'url': image_url,
            'description': description
        })
        return doc_ref[1].id  # Возвращаем ID добавленного документа
    except GoogleAPIError as e:
        raise HTTPException(status_code=500, detail=f'Ошибка сохранения метаданных: {e}')


# Получение всех документов
@app.get('/items')
async def get_items():
    try:
        items_ref = db.collection('exit')
        docs = items_ref.stream()
        data = [{doc.id: doc.to_dict()} for doc in docs]
        return JSONResponse(content=data)
    except GoogleAPIError as e:
        raise HTTPException(status_code=500, detail=f'Ошибка получения данных: {e}')


# Получение одного документа по ID
@app.get('/items/{item_id}')
async def get_item(item_id: str):
    try:
        doc_ref = db.collection('exit').document(item_id)
        doc = doc_ref.get()
        if doc.exists:
            return JSONResponse(content=doc.to_dict())
        raise HTTPException(status_code=404, detail='Item not found')
    except GoogleAPIError as e:
        raise HTTPException(status_code=500, detail=f'Ошибка доступа к документу: {e}')


# Добавление нового изображения
@app.post('/items')
async def add_item(image: UploadFile = File(...), description: str = File(...)):
    if not description:
        raise HTTPException(status_code=400, detail='Description is required')

    image_url = upload_image(image)
    item_id = save_image_metadata(image_url, description)
    return JSONResponse(
        content={'id': item_id, 'url': image_url, 'description': description},
        status_code=201
    )


# Локальный запуск (опционально)
if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host='127.0.0.1', port=8000, log_level="info", reload=True)
