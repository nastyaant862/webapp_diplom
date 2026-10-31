async function logout() {
        await fetch("/logout", {
            method: "GET",
            credentials: "include"
        });
        window.location.href = "/login";
    }

function showConfig() {
    document.getElementById("configSection").style.display = "block";
}

function showSaveSection() {
    document.getElementById("saveResSection").style.display = "block";
}

function formatPartName(name) {
    const nameMap = {
        "PIN_12X50": "Штифт 12×50",
        "BALL_BEARING_1000908": "Подшипник шариковый 1000908",
        "RING_B40_05": "Кольцо В40.05",
        "PIN_12X30": "Штифт 12×30",
        "ROLLER_BEARING_2205": "Подшипник роликовый 2205",
        "BALL_BEARING_1000904": "Подшипник шариковый 1000904",
        "KEY_4X4X25": "Шпонка 4×4×25",
        "BALL_BEARING_101": "Подшипник шариковый 101",
        "RING_B12_05": "Кольцо В12.05",
        "RING_B37_05": "Кольцо В37.05",
        "SCREW_M6_6GX14_14H_05": "Винт M6-6gx14.14H.05",
        "SCREW_M6_6GX40_56_05": "Винт M6-6gx40.56.05",
        "SHAFT_PCR19_10_016": "Вал ПЦР19.10.016",
        "ECCENTRIC_PCR19_10_015": "Эксцентрик ПЦР19.10.015",
        "SATELLITE_PCR19_10_014": "Сателлит ПЦР19.10.014",
        "SHAFT_PCR19_10_022": "Вал ПЦР19.10.022",
        "BUSHING_PCR19_10_023": "Втулка ПЦР19.10.023",
        "RING_PCR19_10_011": "Кольцо ПЦР19.10.011",
        "RING_PCR19_10_012": "Кольцо ПЦР19.10.012",
        "RING_PCR19_10_013": "Кольцо ПЦР19.10.013",
        "RING_PCR19_10_017": "Кольцо ПЦР19.10.017",
        "COVER_PCR19_10_018": "Крышка ПЦР19.10.018",
        "RING_PCR19_10_019": "Кольцо ПЦР19.10.019",
        "BODY_PCR19_10_021": "Корпус ПЦР19.10.021"
    };
    return nameMap[name] || name;
}

let checkedParts = []; // Глобальная переменная для хранения информации о проверенных деталях

async function startCheck() {
    const statusEl = document.getElementById("status");
    statusEl.textContent = "🔄 Проверка запущена...";
    checkedParts = []; // Сбрасываем при новой проверке !!

    try {
        const res = await fetch("/api/start_check", { method: "POST" });
        const data = await res.json();
        statusEl.textContent = "⏳ Проверка выполняется...";

        // Ждём 6 сек и забираем результат
        setTimeout(async () => {
            const result = await fetch("/api/check_result");
            const check = await result.json();

            if (check.status === "completed") {
                checkedParts = check.all_parts.map(part => ({
                    name: part.name,
                    required: part.required,
                    present: part.present
                }));
                console.log("Сформированный checkedParts:", checkedParts);
                if (check.missing.length === 0) {
                    statusEl.textContent = "✅ Все детали на месте!";
                    showSaveSection();
                } else {
                    let missingDetails = check.missing.map(p =>
                        `• ${formatPartName(p.name)}: нужно ${p.required}, есть ${p.present}`
                    ).join("<br>");

                    statusEl.innerHTML = `
                        ❌ Отсутствуют детали:<br>
                        ${missingDetails}
                        <br><br>
                        Пожалуйста, проверьте набор и запустите повторную проверку по кнопке "Старт".
                    `;
                }
            } else {
                statusEl.textContent = "⚠️ Не удалось завершить проверку";
            }
        }, 14000);
    } catch (e) {
        statusEl.textContent = "❌ Ошибка при запуске проверки";
        console.error(e);
    }
}

async function saveResults() {
    const statusEl = document.getElementById("save");
    statusEl.textContent = "🔄 Сохранение результатов...";

    try {
        // Проверяем исходные данные
        console.log("Исходные checkedParts:", checkedParts);

        // Преобразуем в нужный формат
        const partsToSave = checkedParts.map(part => {
            // Добавляем проверку на существование свойств
            const partName = part.name || part.partName || part.id;
            const quantity = part.present || part.quantity || 0;

            return {
                name: partName,
                quantity: quantity
            };
        });

        console.log("Подготовленные к отправке данные:", partsToSave);

        const saveResponse = await fetch("/api/save_results", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(partsToSave)
        });

        if (!saveResponse.ok) {
            const error = await saveResponse.json();
            console.error("Ошибка сервера:", error);
            throw new Error(error.detail || "Ошибка сервера");
        }

        const result = await saveResponse.json();
        console.log("Ответ сервера:", result);
        statusEl.textContent = "✅ Успех. " + result.message;
    } catch (e) {
        statusEl.textContent = `❌ Ошибка: ${e.message}`;
        console.error("Ошибка сохранения:", e);
    }
}
