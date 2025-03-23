import sys
import os
from pathlib import Path

# Добавляем корень проекта в PYTHONPATH
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.append(str(project_root))

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
import tempfile
from document_processing import Pipeline
from scripts.process_img import process_img  # Изменённый импорт
import uvicorn

app = FastAPI()

# Инициализация Pipeline при старте приложения
pipeline = Pipeline(model_format='OpenVINO', device='cpu')

@app.post("/process-image/")
async def api_process_image(file: UploadFile = File(...)):
    try:
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        # Параметры для обработки
        params = {
            'img_path': Path(temp_file_path),
            'pipeline': pipeline,
            'check_quality': False,
            'img_size': 1500,
            'format': 'OpenVINO',
            'device': 'cpu'
        }

        # Обработка изображения
        result = process_img(**params)
        
        # Удаление временного файла
        os.unlink(temp_file_path)

        return JSONResponse(content=result.full_report)

    except Exception as e:
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
