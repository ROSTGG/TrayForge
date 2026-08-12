import os
import tempfile
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Здесь мы импортируем функции из твоего оригинального скрипта.
# Замени 'process_gerber_to_svg' и 'generate_stl_from_gerber' на реальные названия 
# функций из твоего файла stencil_core.py.
from stencil_core import process_gerber_to_svg, generate_stl_from_gerber

app = FastAPI(title="StencilForge API")

# Раздаем статические файлы (наш красивый index.html)
# Папка 'static' должна лежать рядом с main.py
app.mount("/static", StaticFiles(directory="static", html=True), name="static")

@app.post("/api/preview")
async def preview_endpoint(
    file: UploadFile = File(...),
    thickness: float = Form(...),
    margin: float = Form(...),
    pad_shrink: float = Form(...),
    min_feature: float = Form(...),
    mirror_x: bool = Form(...),
    add_frame: bool = Form(...)
):
    """
    Эндпоинт для генерации 2D превью (SVG).
    """
    # Сохраняем загруженный файл во временную директорию
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gbr") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # ВЫЗОВ ТВОЕЙ ОРИГИНАЛЬНОЙ ЛОГИКИ
        # Передаем путь к файлу и параметры в твою функцию
        preview_data = process_gerber_to_svg(
            filepath=tmp_path,
            margin=margin,
            pad_shrink=pad_shrink,
            min_feature=min_feature,
            mirror_x=mirror_x
        )
        
        # Функция должна вернуть словарь (или объект) с данными для браузера. Например:
        # {
        #    "svg_content": "<svg>...</svg>",
        #    "view_box": "0 0 100 100",
        #    "pcb_w": 50, "pcb_h": 40,
        #    "stencil_w": 60, "stencil_h": 50,
        #    "aperture_count": 120
        # }
        
        return JSONResponse(content=preview_data)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # Удаляем временный файл
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@app.post("/api/convert")
async def convert_endpoint(
    file: UploadFile = File(...),
    thickness: float = Form(...),
    margin: float = Form(...),
    pad_shrink: float = Form(...),
    min_feature: float = Form(...),
    mirror_x: bool = Form(...),
    add_frame: bool = Form(...),
    frame_height: float = Form(...),
    frame_width: float = Form(...)
):
    """
    Эндпоинт для генерации 3D модели (STL).
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix=".gbr") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    # Создаем имя для выходного STL файла
    out_stl_path = tmp_path + ".stl"

    try:
        # ВЫЗОВ ТВОЕЙ ОРИГИНАЛЬНОЙ ЛОГИКИ
        # Функция должна сгенерировать STL и сохранить его по пути out_stl_path
        generate_stl_from_gerber(
            filepath=tmp_path,
            output_path=out_stl_path,
            thickness=thickness,
            margin=margin,
            pad_shrink=pad_shrink,
            min_feature=min_feature,
            mirror_x=mirror_x,
            add_frame=add_frame,
            frame_height=frame_height,
            frame_width=frame_width
        )
        
        # Отправляем готовый файл в браузер
        return FileResponse(
            path=out_stl_path, 
            filename=file.filename.replace(".gbr", "_stencil.stl"),
            media_type="application/octet-stream"
        )

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    finally:
        # Уборка временных файлов
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        # Файл STL удалится автоматически после отправки благодаря FileResponse (в более сложных реализациях используется background_tasks)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)