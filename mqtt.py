import paho.mqtt.client as mqtt
import random
import time
from datetime import datetime, UTC
import threading
import json

# MQTT конфигурация
MQTT_BROKER = "mqtt.eclipseprojects.io" #broker.hivemq.com
MQTT_PORT = 1883
MQTT_KEEP_ALIVE_INTERVAL = 60

# Словарь с топиками и названиями деталей
PART_TOPICS = {
    "PIN_12X50": "/assembly/reducer/PCR19.10/pin_12x50",
    "BALL_BEARING_1000908": "/assembly/reducer/PCR19.10/ball_bearing_1000908",
    "RING_B40_05": "/assembly/reducer/PCR19.10/ring_b40_05",
    "PIN_12X30": "/assembly/reducer/PCR19.10/pin_12x30",
    "ROLLER_BEARING_2205": "/assembly/reducer/PCR19.10/roller_bearing_2205",
    "BALL_BEARING_1000904": "/assembly/reducer/PCR19.10/ball_bearing_1000904",
    "KEY_4X4X25": "/assembly/reducer/PCR19.10/key_4x4x25",
    "BALL_BEARING_101": "/assembly/reducer/PCR19.10/ball_bearing_101",
    "RING_B12_05": "/assembly/reducer/PCR19.10/ring_b12_05",
    "RING_B37_05": "/assembly/reducer/PCR19.10/ring_b37_05",
    "SCREW_M6_6GX14_14H_05": "/assembly/reducer/PCR19.10/screw_m6_6gx14_14h_05",
    "SCREW_M6_6GX40_56_05": "/assembly/reducer/PCR19.10/screw_m6_6gx40_56_05",
    "SHAFT_PCR19_10_016": "/assembly/reducer/PCR19.10/shaft_pcr19_10_016",
    "ECCENTRIC_PCR19_10_015": "/assembly/reducer/PCR19.10/eccentric_pcr19_10_015",
    "SATELLITE_PCR19_10_014": "/assembly/reducer/PCR19.10/satellite_pcr19_10_014",
    "SHAFT_PCR19_10_022": "/assembly/reducer/PCR19.10/shaft_pcr19_10_022",
    "BUSHING_PCR19_10_023": "/assembly/reducer/PCR19.10/bushing_pcr19_10_023",
    "RING_PCR19_10_011": "/assembly/reducer/PCR19.10/ring_pcr19_10_011",
    "RING_PCR19_10_012": "/assembly/reducer/PCR19.10/ring_pcr19_10_012",
    "RING_PCR19_10_013": "/assembly/reducer/PCR19.10/ring_pcr19_10_013",
    "RING_PCR19_10_017": "/assembly/reducer/PCR19.10/ring_pcr19_10_017",
    "COVER_PCR19_10_018": "/assembly/reducer/PCR19.10/cover_pcr19_10_018",
    "RING_PCR19_10_019": "/assembly/reducer/PCR19.10/ring_pcr19_10_019",
    "BODY_PCR19_10_021": "/assembly/reducer/PCR19.10/body_pcr19_10_021"
}

# Словарь с нужным количеством деталей
PART_REQUIRED_QUANTITY = {
    "PIN_12X50": 6,
    "BALL_BEARING_1000908": 2,
    "RING_B40_05": 1,
    "PIN_12X30": 6,
    "ROLLER_BEARING_2205": 2,
    "BALL_BEARING_1000904": 1,
    "KEY_4X4X25": 1,
    "BALL_BEARING_101": 1,
    "RING_B12_05": 1,
    "RING_B37_05": 1,
    "SCREW_M6_6GX14_14H_05": 3,
    "SCREW_M6_6GX40_56_05": 8,
    "SHAFT_PCR19_10_016": 1,
    "ECCENTRIC_PCR19_10_015": 2,
    "SATELLITE_PCR19_10_014": 2,
    "SHAFT_PCR19_10_022": 1,
    "BUSHING_PCR19_10_023": 1,
    "RING_PCR19_10_011": 1,
    "RING_PCR19_10_012": 1,
    "RING_PCR19_10_013": 1,
    "RING_PCR19_10_017": 1,
    "COVER_PCR19_10_018": 1,
    "RING_PCR19_10_019": 1,
    "BODY_PCR19_10_021": 1
}

# Словарь для хранения статусов деталей (не используется)
# PART_STATUS = {}


# Генерация данных о наличии детали
def generate_part_status(part_name: str):
    required_quantity = PART_REQUIRED_QUANTITY.get(part_name, 1)
    # Эмулируем наличие: в 90% (0.9) случаев деталь есть полностью, в 10% недостача
    present_quantity = required_quantity if random.random() < 1 else random.randint(0, required_quantity - 1)
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "required": required_quantity,
        "present": present_quantity
    }


# Обработка входящих сообщений
def on_message(client, userdata, msg):
    print(f"📩 Получено сообщение:\n └ Топик: {msg.topic}\n └ Payload: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        for part_name, topic in PART_TOPICS.items():
            if msg.topic == topic:
                if 'received_parts' not in userdata:
                    userdata['received_parts'] = {}
                userdata['received_parts'][part_name] = payload
                print(f"💾 Сохранено состояние детали {part_name}")
                break
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка декодирования JSON для топика {msg.topic}: {e}")


# Callback при подключении
def on_connect(client, userdata, flags, rc):
    print(f"🔌 Подключено к MQTT брокеру (код: {rc})")
    for topic in PART_TOPICS.values():
        client.subscribe(topic, qos=1)  # Подписываемся с QoS=1
        print(f"📡 Подписка на: {topic} (QoS=1)")


def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Соединение с брокером потеряно, пытаемся переподключиться...")
        client.reconnect()


# Публикация сообщений по всем деталям
def publish_all_parts(client):
    print("🚀 Публикация статуса всех деталей:")
    for part_name, topic in PART_TOPICS.items():
        payload = generate_part_status(part_name)
        client.publish(topic, json.dumps(payload), qos=1)  # Используем QoS=1 для надежности
        print(f" → {part_name}: {payload}")
        time.sleep(0.1)  # задержка между сообщениями


# Проверка комплектности
def check_completeness(result_dict):
    if 'received_parts' not in result_dict:
        result_dict['received_parts'] = {}

    start_time = time.time()
    while len(result_dict['received_parts']) < len(PART_TOPICS) and time.time() - start_time < 10:
        time.sleep(0.5)
    print(f"🔍 Получено {len(result_dict['received_parts'])}/{len(PART_TOPICS)} деталей. "
          f"Состояние: {result_dict['received_parts']}")

    missing = []

    for part_name in PART_TOPICS:
        part_data = result_dict['received_parts'].get(part_name)
        if not part_data:
            missing.append({
                "name": part_name,
                "required": PART_REQUIRED_QUANTITY.get(part_name, 1),
                "present": 0
            })
        else:
            try:
                required = part_data.get("required", 1)
                present = part_data.get("present", 0)

                if present < required:
                    missing.append({
                        "name": part_name,
                        "required": required,
                        "present": present
                    })
            except Exception as e:
                print(f"Ошибка обработки детали {part_name}: {e}")
                missing.append({
                    "name": part_name,
                    "required": PART_REQUIRED_QUANTITY.get(part_name, 1),
                    "present": 0
                })

    result_dict["status"] = "completed"
    result_dict["missing"] = missing

    all_parts = []
    for part_name in PART_TOPICS:
        part_data = result_dict['received_parts'].get(part_name, {})
        all_parts.append({
            "name": part_name,
            "required": part_data.get("required", PART_REQUIRED_QUANTITY.get(part_name, 1)),
            "present": part_data.get("present", 0)
        })
    result_dict["all_parts"] = all_parts
    #print("Сформированные all_parts:", all_parts)
    print(f"✅ Проверка завершена. Отсутствуют: {missing}")


# Основная функция запуска клиента
def run_mqtt_client(result_dict):
    result_dict["status"] = "in_progress"
    result_dict["missing"] = []
    result_dict["received_parts"] = {}
    result_dict["all_parts"] = PART_TOPICS

    connected_event = threading.Event()  # Событие для ожидания подключения

    def on_connect_wrapper(client, userdata, flags, rc):
        on_connect(client, userdata, flags, rc)
        connected_event.set()  # Сигнализируем, что подключение установлено

    client = mqtt.Client(userdata=result_dict) # создание mqtt-клиента
    client.on_connect = on_connect_wrapper
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, MQTT_KEEP_ALIVE_INTERVAL)
    client.loop_start() # запуск цикла

    # ожидание подключения (максимум 5 секунд)
    if not connected_event.wait(5):
        print("⚠️ Не удалось подключиться к брокеру")
        result_dict["status"] = "failed"
        return client

    # запуск потока публикации только после подключения
    thread = threading.Thread(target=publish_all_parts, args=(client,))
    thread.daemon = True
    thread.start()

    threading.Timer(10.0, check_completeness, args=(result_dict,)).start()  # првоерка комплектности по таймеру 10 сек
    return client
