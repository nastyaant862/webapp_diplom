import mysql
from pydantic import BaseModel
from mysql.connector import connect
from datetime import datetime
from typing import Optional


class UserLoginSchema(BaseModel):
    username: str
    password: str


class ManageTypeSchema(BaseModel):
    objectType: str
    action: str
    id: int | None = None
    name: str
    description: str


def connect_to_db():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="nastyaant862",
        database="diplom"
    )
    return connection


def select_login_pass(userlogin):
    connection = connect_to_db()
    cursor = connection.cursor()
    query = f''' SELECT diplom.данные_аккаунта.логин, diplom.данные_аккаунта.пароль 
                    FROM diplom.данные_аккаунта WHERE diplom.данные_аккаунта.логин = {userlogin} '''
    cursor.execute(query)
    result = cursor.fetchall()
    connection.close()
    return result[0][0], result[0][1]


def get_cell_contents(address):
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    # Получаем id_ячейки и статус по адресу
    cursor.execute("""
        SELECT id_ячейки, статус_занятости
        FROM ячейки_склада
        WHERE адрес_ячейки = %s
    """, (address,))
    cell = cursor.fetchone()

    if not cell:
        connection.close()
        return {"status": "unknown", "details": [], "reducers": []}

    cell_id = cell['id_ячейки']

    # Получаем детали в ячейке
    cursor.execute("""
        SELECT типы_деталей.название AS название, детали.количество
        FROM детали
        JOIN типы_деталей ON детали.id_типа_детали = типы_деталей.id_типа_детали
        WHERE детали.id_ячейки = %s
    """, (cell_id,))
    details = cursor.fetchall()

    # Получаем готовые редукторы в ячейке
    cursor.execute("""
        SELECT типы_редукторов.название AS название
        FROM готовые_редукторы
        JOIN типы_редукторов ON готовые_редукторы.id_типа_редуктора = типы_редукторов.id_типа_редуктора
        WHERE готовые_редукторы.id_ячейки = %s
    """, (cell_id,))
    reducers = cursor.fetchall()

    connection.close()

    return {
        "status": cell['статус_занятости'],
        "details": details,
        "reducers": reducers
    }


def search_in_db(search_criteria):
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    object_type = search_criteria.get('objectType', 'all')
    results = []

    date_from = search_criteria.get('dateFrom')
    date_to = search_criteria.get('dateTo')
    if date_from:
        date_from += " 00:00:00"
    if date_to:
        date_to += " 23:59:59"

    # --- Поиск редукторов ---
    if object_type in ['all', 'reducer']:
        query = """
            SELECT 
                'reducer' AS type,
                типы_редукторов.название AS subtype,
                ячейки_склада.адрес_ячейки AS cell,
                готовые_редукторы.датавремя AS date
            FROM готовые_редукторы
            JOIN типы_редукторов ON готовые_редукторы.id_типа_редуктора = типы_редукторов.id_типа_редуктора
            LEFT JOIN ячейки_склада ON готовые_редукторы.id_ячейки = ячейки_склада.id_ячейки
            WHERE 1=1
        """
        reducer_params = []

        if search_criteria.get('reducerType') and search_criteria['reducerType'] != 'all':
            query += " AND типы_редукторов.название LIKE %s"
            reducer_params.append(f"%{search_criteria['reducerType']}%")  # Поиск по вхождению

        if search_criteria.get('cell'):
            cell = search_criteria['cell'].strip()
            if cell:
                query += " AND ячейки_склада.адрес_ячейки = %s"
                reducer_params.append(cell)

        if date_from:
            query += " AND готовые_редукторы.датавремя >= %s"
            reducer_params.append(date_from)

        if date_to:
            query += " AND готовые_редукторы.датавремя <= %s"
            reducer_params.append(date_to)

        cursor.execute(query, reducer_params)
        results.extend(cursor.fetchall())

    # --- Поиск деталей ---
    if object_type in ['all', 'det']:
        query = """
            SELECT 
                'det' AS type,
                типы_деталей.название AS subtype,
                ячейки_склада.адрес_ячейки AS cell
            FROM детали
            JOIN типы_деталей ON детали.id_типа_детали = типы_деталей.id_типа_детали
            LEFT JOIN ячейки_склада ON детали.id_ячейки = ячейки_склада.id_ячейки
            WHERE 1=1
        """
        det_params = []

        if search_criteria.get('detType') and search_criteria['detType'] != 'all':
            query += " AND типы_деталей.название LIKE %s"
            det_params.append(f"%{search_criteria['detType']}%")  # Поиск по вхождению

        if search_criteria.get('cell'):
            cell = search_criteria['cell'].strip()
            if cell:
                query += " AND ячейки_склада.адрес_ячейки = %s"
                det_params.append(cell)

        cursor.execute(query, det_params)
        results.extend(cursor.fetchall())

    connection.close()

    for row in results:
        if row['type'] == 'reducer' and isinstance(row.get('date'), datetime):
            row['date'] = row['date'].strftime("%Y-%m-%d %H:%M:%S")

    return results


def get_types(objecttype: str):
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)

    if objecttype == "reducer":
        cursor.execute("SELECT id_типа_редуктора AS id, CONCAT(типы_редукторов.название, ' ред-р: ', модели.название) "
                       "AS name FROM diplom.типы_редукторов JOIN diplom.модели "
                       "ON типы_редукторов.id_модели = модели.id_модели")
    else:
        cursor.execute("SELECT id_типа_детали AS id, название AS name FROM типы_деталей")

    results = cursor.fetchall()
    connection.close()
    return results


def manage_types(data: ManageTypeSchema):
    connection = connect_to_db()
    cursor = connection.cursor()

    if data.objectType == "reducer":
        table = "типы_редукторов"
        id_field = "id_типа_редуктора"
    else:
        table = "типы_деталей"
        id_field = "id_типа_детали"

    if data.action == "add":
        cursor.execute(f"""
                INSERT INTO {table} (название, описание, ссылка_на_чертёж, сборочная_карта, 3d_модель, id_модели)
                VALUES (%s, %s, '', '', '', 1)
            """, (data.name, data.description))

    elif data.action == "edit" and data.id:
        cursor.execute(f"""
                UPDATE {table}
                SET название = %s, описание = %s
                WHERE {id_field} = %s
            """, (data.name, data.description, data.id))

    connection.commit()
    connection.close()

    return {"message": "success"}


# def format_part_name(name: str) -> str:
#     name_map = {
#         "PIN_12X50": "Штифт 12×50",
#         "BALL_BEARING_1000908": "Подшипник шариковый 1000908",
#         "RING_B40_05": "Кольцо В40.05",
#         "PIN_12X30": "Штифт 12×30",
#         "ROLLER_BEARING_2205": "Подшипник роликовый 2205",
#         "BALL_BEARING_1000904": "Подшипник шариковый 1000904",
#         "KEY_4X4X25": "Шпонка 4×4×25",
#         "BALL_BEARING_101": "Подшипник шариковый 101",
#         "RING_B12_05": "Кольцо В12.05",
#         "RING_B37_05": "Кольцо В37.05",
#         "SCREW_M6_6GX14_14H_05": "Винт M6-6gx14.14H.05",
#         "SCREW_M6_6GX40_56_05": "Винт M6-6gx40.56.05",
#         "SHAFT_PCR19_10_016": "Вал ПЦР19.10.016",
#         "ECCENTRIC_PCR19_10_015": "Эксцентрик ПЦР19.10.015",
#         "SATELLITE_PCR19_10_014": "Сателлит ПЦР19.10.014",
#         "SHAFT_PCR19_10_022": "Вал ПЦР19.10.022",
#         "BUSHING_PCR19_10_023": "Втулка ПЦР19.10.023",
#         "RING_PCR19_10_011": "Кольцо ПЦР19.10.011",
#         "RING_PCR19_10_012": "Кольцо ПЦР19.10.012",
#         "RING_PCR19_10_013": "Кольцо ПЦР19.10.013",
#         "RING_PCR19_10_017": "Кольцо ПЦР19.10.017",
#         "COVER_PCR19_10_018": "Крышка ПЦР19.10.018",
#         "RING_PCR19_10_019": "Кольцо ПЦР19.10.019",
#         "BODY_PCR19_10_021": "Корпус ПЦР19.10.021"
#     }
#     return name_map.get(name, name)


def save_results(user, red_type):
    connection = connect_to_db()
    cursor = connection.cursor()
    curr_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    query = f'''INSERT INTO `diplom`.`контроль_комплектности` 
            (`id_пользователя`, `id_типа_редуктора`, `статус`, `комментарий`, `датавремя`) 
            VALUES ({user}, {red_type}, 1, 'контроль пройден!', '{curr_datetime}') '''
    print(query)
    cursor.execute(query)
    connection.commit()
    connection.close()


def log_action(user_id: int, operation_id: int):
    # connection = connect_to_db()
    # cursor = connection.cursor()
    # try:
    #     curr_datetime = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    #     query = f'''INSERT INTO `журнал_действий`
    #             (`датавремя`, `id_операции`, `id_пользователя`)
    #             VALUES ('{curr_datetime}', {operation_id}, {user_id})'''
    #     cursor.execute(query)
    #     connection.commit()
    # except Exception as e:
    #     print(f"Ошибка при логировании действия: {e}")
    #     connection.rollback()
    # finally:
    #     cursor.close()
    #     connection.close()
    return True


def get_users():
    # Получение списка пользователей для фильтра
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    try:
        query = '''SELECT id_пользователя as id, CONCAT (фамилия, ' ', имя, ' ', отчество) as name FROM пользователи'''
        cursor.execute(query)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_logs(user_id: Optional[int] = None, date_from: Optional[str] = None, date_to: Optional[str] = None):
    """Получение журналов с фильтрацией"""
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
            SELECT журнал_действий.id_действия AS id, журнал_действий.датавремя AS date_time, 
                CONCAT (фамилия, ' ', имя, ' ', отчество) as username, 
                типы_операций.название AS operation
            FROM diplom.журнал_действий JOIN diplom.пользователи ON журнал_действий.id_пользователя = пользователи.id_пользователя
            JOIN типы_операций ON журнал_действий.id_операции = типы_операций.id_операции WHERE 1=1"""
        params = []

        if user_id:
            query += " AND журнал_действий.id_пользователя = %s"
            params.append(user_id)

        if date_from:
            query += " AND журнал_действий.датавремя >= %s"
            params.append(f"{date_from} 00:00:00")

        if date_to:
            query += " AND журнал_действий.датавремя <= %s"
            params.append(f"{date_to} 23:59:59")

        query += " ORDER BY журнал_действий.датавремя DESC LIMIT 1000"

        cursor.execute(query, params)
        return cursor.fetchall()
    finally:
        cursor.close()
        connection.close()


def get_reps(
        user_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None):
    """Получение отчетов с фильтрацией"""
    connection = connect_to_db()
    cursor = connection.cursor(dictionary=True)
    try:
        query = """
                SELECT 
                    контроль_комплектности.id_проверки as id,
                    контроль_комплектности.датавремя as date_time,
                    CONCAT(фамилия, ' ', имя, ' ', отчество) as username,
                    типы_редукторов.название as red_type,
                    контроль_комплектности.статус as status,
                    контроль_комплектности.комментарий as комментарий
                FROM контроль_комплектности
                JOIN пользователи ON контроль_комплектности.id_пользователя = пользователи.id_пользователя
                LEFT JOIN типы_редукторов ON контроль_комплектности.id_типа_редуктора = типы_редукторов.id_типа_редуктора
                WHERE 1=1
            """
        params = []

        if user_id:
            query += " AND контроль_комплектности.id_пользователя = %s"
            params.append(user_id)

        if date_from:
            query += " AND контроль_комплектности.датавремя >= %s"
            params.append(f"{date_from} 00:00:00")

        if date_to:
            query += " AND контроль_комплектности.датавремя <= %s"
            params.append(f"{date_to} 23:59:59")

        query += " ORDER BY контроль_комплектности.датавремя DESC LIMIT 1000"

        cursor.execute(query, params)
        reports = cursor.fetchall()
        return reports
    finally:
        cursor.close()
        connection.close()