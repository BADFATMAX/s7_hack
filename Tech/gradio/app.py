import gradio as gr
import requests
import json

def process_and_verify(image_passport, image_person):
    results = [{}, {}]  # [passport_result, verify_result]

    # Обработка паспорта
    if image_passport:
        try:
            url = "http://192.168.0.159:8000/process-image/"
            with open(image_passport, "rb") as f:
                response = requests.post(url, files={"file": f})
            results[0] = response.json()
        except Exception as e:
            results[0] = {"error": f"Ошибка распознавания: {str(e)}"}

    # Верификация личности
    if image_passport and image_person:
        try:
            url = "http://192.168.0.160:8031/verify"
            with open(image_passport, "rb") as f1, open(image_person, "rb") as f2:
                response = requests.post(url, files={"file1": f2, "file2": f1})
            results[1] = response.json()
        except Exception as e:
            results[1] = {"error": f"Ошибка верификации: {str(e)}"}

    return results

def create_passport_summary(data):
    if "error" in data:
        return gr.HTML(f"<div style='color: red'>{data['error']}</div>")

    ocr = data.get("OCR", {})
    return gr.HTML(f"""
    <div style='color: #2ecc71; font-weight: bold'>
        Фамилия: {ocr.get('Last_name_ru', 'N/A')}<br>
        Имя: {ocr.get('First_name_ru', 'N/A')}<br>
        Отчество: {ocr.get('Middle_name_ru', 'N/A')}<br>
        Дата рождения: {ocr.get('Birth_date', 'N/A')}<br>
        Серия/номер: {ocr.get('Licence_number', 'N/A')}
    </div>
    """)

def create_verification_summary(data):
    if "error" in data:
        return gr.HTML(f"<div style='color: red'>{data['error']}</div>")

    verified = data.get("verified", False)
    distance = round(data.get("distance", 0) * 100, 2)

    status = "Личность подтверждена ✅" if verified else "Личности не совпадают ❌"
    color = "#2ecc71" if verified else "#e74c3c"

    return gr.HTML(f"""
    <div style='color: {color}; font-weight: bold'>
        {status}<br>
        Различность: {distance}%
    </div>
    """)

with gr.Blocks(title="Проверка документов") as app:
    # Заголовок проекта
    gr.HTML("""
    <div style="
        text-align: center;
        width: 100%;
        padding: 15px 0;
        margin: 10px 0;
        border-bottom: 2px solid #2ecc71;
    ">
        <h1 style="
            font-size: 2.8em;
            margin: 0;
            color: #2c3e50;
            text-transform: uppercase;
            letter-spacing: 4px;
            font-family: 'Arial Black', sans-serif;
        ">АэроСтраж AI</h1>
    </div>
    """)

    gr.Markdown("## Загрузка документов для проверки")

    with gr.Row():
        passport_img = gr.Image(
            label="Фото паспорта",
            type="filepath",
            show_label=True
        )
        person_img = gr.Image(
            label="Фото человека",
            type="filepath",
            show_label=True
        )

    process_btn = gr.Button("Распознать паспорт и верифицировать личность", variant="primary")

    with gr.Row():
        with gr.Column():
            passport_header = gr.HTML()
            passport_json = gr.JSON(label="Данные паспорта")

        with gr.Column():
            verify_header = gr.HTML()
            verify_json = gr.JSON(label="Результат верификации")

    process_btn.click(
        fn=process_and_verify,
        inputs=[passport_img, person_img],
        outputs=[passport_json, verify_json]
    ).then(
        fn=create_passport_summary,
        inputs=passport_json,
        outputs=passport_header
    ).then(
        fn=create_verification_summary,
        inputs=verify_json,
        outputs=verify_header
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=8003, share=True)
