from fastapi import FastAPI, File, UploadFile, HTTPException
import face_recognition
from typing import Tuple
from io import BytesIO
from PIL import Image

app = FastAPI()

def get_face_encoding(file: UploadFile) -> Tuple[bool, any]:
    try:
        image = face_recognition.load_image_file(BytesIO(file.file.read()))
        encodings = face_recognition.face_encodings(image)
        if not encodings:
            return False, "Лицо не найдено на изображении"
        return True, encodings[0]
    except Exception as e:
        return False, f"Ошибка обработки изображения: {str(e)}"

@app.post("/compare-faces/")
async def compare_faces(
    file1: UploadFile = File(...),
    file2: UploadFile = File(...)
):
    success1, result1 = get_face_encoding(file1)
    success2, result2 = get_face_encoding(file2)

    if not success1 or not success2:
        raise HTTPException(status_code=400, detail=f"{result1 if not success1 else result2}")

    match = face_recognition.compare_faces([result1], result2)[0]
    distance = face_recognition.face_distance([result1], result2)[0]

    return {
        "match": match,
        "distance": round(float(distance), 4)
    }