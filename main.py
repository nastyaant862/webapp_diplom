from fastapi import FastAPI, HTTPException, Response, Depends, BackgroundTasks
from fastapi.responses import FileResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from authx import AuthX, AuthXConfig
from db_actions import (UserLoginSchema, select_login_pass, get_cell_contents, search_in_db,
                        get_types, ManageTypeSchema, manage_types, save_results, log_action,
                        get_users, get_logs, get_reps)
from mqtt import run_mqtt_client
from pydantic import BaseModel
from typing import List
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")  #раздача статических файлов (картинки)

config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = "my_access_token"
config.JWT_TOKEN_LOCATION = ["cookies"]
security = AuthX(config=config)

user = 0


@app.get("/")
async def root():
    return RedirectResponse(url="/login")


@app.get("/login")
async def login_page():
    return FileResponse(r"D:\python\webapp_diplom\pages\login.html")


@app.post("/login")
async def login(creds: UserLoginSchema, responce: Response):
    try:
        result = usname, pas = select_login_pass(creds.username)
        if not result:
            raise HTTPException(status_code=401, detail="Incorrect username or password")
        if creds.username == usname and creds.password == pas:
            token = security.create_access_token(uid="1")
            responce.set_cookie(config.JWT_ACCESS_COOKIE_NAME, token)

            global user
            user = usname
            log_action(user, 1)

            return {"access_token": token}
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    except Exception as e:
        raise HTTPException(status_code=401, detail="Incorrect username or password")


@app.get("/logout")
async def logout(response: Response):
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(config.JWT_ACCESS_COOKIE_NAME)
    global user
    log_action(user, 9)
    return response


@app.get("/base", dependencies=[Depends(security.access_token_required)])
async def base():
    global user
    log_action(user, 10)
    return FileResponse(r"D:\python\webapp_diplom\pages\index.html")


@app.get("/check", dependencies=[Depends(security.access_token_required)])
async def check():
    global user
    log_action(user, 2)
    return FileResponse(r"D:\python\webapp_diplom\pages\checking.html")


# -- ВЗАИМОДЕЙСТВИЕ С БД -- #
@app.get("/database_interaction", dependencies=[Depends(security.access_token_required)])
async def database_interaction():
    global user
    log_action(user, 3)
    return FileResponse(r"D:\python\webapp_diplom\pages\db_int.html")


# получение данных ячеек склада (СКЛАД)
@app.get("/api/get_cell_data")
async def get_cell_data(address: str):
    data = get_cell_contents(address)
    global user
    log_action(user, 4)
    return JSONResponse(content=data, media_type="application/json")


# получение типов данных для поиска (ПОИСК)
@app.get("/api/get_types")
def api_get_types(objectType: str):
    return get_types(objectType)


# поиск данных из бд по критериям (ПОИСК)
@app.post("/api/search")
async def search_items(search_data: dict):
    # print(search_data)
    try:
        results = search_in_db(search_data)
        global user
        log_action(user, 5)
        return JSONResponse(content=results, media_type="application/json")
    except Exception as e:
        print("Ошибка поиска:", e)
        raise HTTPException(status_code=500, detail=str(e))


# изменение данных (УПРАВЛЕНИЕ ОБЪЕКТАМИ)
@app.post("/api/manage_type")
def api_manage_type(data: ManageTypeSchema):
    global user
    log_action(user, 6)
    return manage_types(data)


# получение списка пользователей для фильтрации (ЖУРНАЛЫ)
@app.get("/api/get_users")
async def get_users_db():
    return get_users()


# получение журнала логов (ЖУРНАЛЫ)
@app.get("/api/get_logs")
async def get_logs_db(
        user_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
):
    logs = get_logs(user_id, date_from, date_to)
    return logs


# получение отчёта по проверке комплектности (ОТЧЁТЫ)
@app.get("/api/get_reps")
async def get_reports(
        user_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None
):
    reps = get_reps(user_id, date_from, date_to)
    return reps


# -- ПРОВЕРКА КОМПЛЕКТНОСТИ -- #
check_result = {}  # Хранилище состояния проверки


@app.post("/api/start_check")
async def start_checking(background_tasks: BackgroundTasks):
    global check_result
    check_result = {"status": "in_progress", "missing": [], "all_parts": []}  # Сброс перед запуском
    try:
        background_tasks.add_task(run_mqtt_client, check_result)
        global user
        log_action(user, 11)
        return {"message": "Проверка начата"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка запуска: {str(e)}")


@app.get("/api/check_result")
async def get_check_result():
    return check_result


class PartResult(BaseModel):
    name: str
    quantity: int


@app.post("/api/save_results")
async def save_results_db(data: List[PartResult]):
    try:
        # print("Полученные данные для сохранения:")
        # for part in data:
        #     print(f"🛠 Деталь: {part.name} — Количество: {part.quantity}")
        global user
        save_results(user, '7')
        log_action(user, 12)
        return {"message": "Результаты сохранены"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# uvicorn main:app --reload
