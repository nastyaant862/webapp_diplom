async function logout() {
    await fetch("/logout", {
        method: "GET",
        credentials: "include"
    });
    window.location.href = "/login";
}

function openModal1() {
    document.getElementById("warehouseModal").style.display = "flex";
    renderShelf();
}

function closeModal1() {
    document.getElementById("warehouseModal").style.display = "none";
}

async function renderShelf() {
    const base = document.getElementById("rackSelect").value; // например, A-01
    const grid = document.getElementById("shelfGrid");
    grid.innerHTML = ""; // Очистка перед отрисовкой

    for (let row = 1; row <= 6; row++) {
        for (let col = 1; col <= 6; col++) {
            const address = `${base}-${row.toString().padStart(2, '0')}-${col.toString().padStart(2, '0')}`;

            // Получаем реальные данные с сервера
            const res = await fetch(`/api/get_cell_data?address=${address}`);
            const data = await res.json();

            const content = data.details.map(d => `${d.название} (${d.количество} шт.)`).join("<br>");
            const reducers = data.reducers.map(r => `Редуктор: ${r.название}`).join("<br>");

            const cell = document.createElement("div");
            cell.className = "cell";

            // Добавляем класс для пустой или занятой ячейки
            if (data.details.length > 0 || data.reducers.length > 0) {
                cell.classList.add("occupied");
            } else {
                cell.classList.add("empty");
            }

            // Наполнение ячейки
            cell.innerHTML = `
                <h4>${address}</h4>
                <div class="cell-content">${content}</div>
                <div class="cell-content">${reducers}</div>
            `;
            grid.appendChild(cell);
        }
    }
}


function openModal2() {
    document.getElementById("findModal").style.display = "flex";
    toggleDateFields(); // сразу применим отображение/скрытие даты
}

function closeModal2() {
    document.getElementById("findModal").style.display = "none";
}

document.getElementById("objectType").addEventListener("change", toggleDateFields);

function toggleDateFields() {
    const objectType = document.getElementById("objectType").value;
    document.getElementById("reducerCriteria").style.display = objectType === "reducer" ? "flex" : "none";
    document.getElementById("detCriteria").style.display = objectType === "det" ? "flex" : "none";

    // 👇 скрываем поля дат, если выбран "деталь"
    const dateInputs = document.querySelectorAll("#dateFrom, #dateTo");
    dateInputs.forEach(input => {
        input.parentElement.style.display = (objectType === "reducer" || objectType === "all") ? "flex" : "none";
    });
}

async function performSearch() {
    const objectType = document.getElementById("objectType").value;

    const searchCriteria = {
        objectType,
        reducerType: document.getElementById("reducerType").value,
        detType: document.getElementById("detType").value,
        cell: document.getElementById("cell").value,
        dateFrom: objectType === "reducer" || objectType === "all" ? document.getElementById("dateFrom").value : null,
        dateTo: objectType === "reducer" || objectType === "all" ? document.getElementById("dateTo").value : null
    };

    try {
        const response = await fetch("/api/search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(searchCriteria),
        });

        if (!response.ok) {
            throw new Error('Ошибка при выполнении поиска');
        }

        const results = await response.json();
        displaySearchResults(results);
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById("searchResults").innerHTML = `<p style="color: red;">Ошибка при выполнении поиска: ${error.message}</p>`;
    }
}

function displaySearchResults(results) {
    const resultsContainer = document.getElementById("searchResults");
    resultsContainer.innerHTML = "";

    if (results.length === 0) {
        resultsContainer.innerHTML = "<p>Ничего не найдено</p>";
        return;
    }

    const table = document.createElement("table");
    table.style.width = "100%";
    table.style.borderCollapse = "collapse";
    table.style.marginTop = "20px";

    const thead = document.createElement("thead");
    const headerRow = document.createElement("tr");

    const headers = ["Тип", "Тип объекта", "Ячейка", "Дата поступления"];
    headers.forEach(headerText => {
        const th = document.createElement("th");
        th.textContent = headerText;
        th.style.padding = "10px";
        th.style.borderBottom = "1px solid #d1d1d1";
        th.style.textAlign = "left";
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");

    results.forEach(item => {
        const row = document.createElement("tr");
        row.style.borderBottom = "1px solid #d1d1d1";

        const typeCell = document.createElement("td");
        typeCell.textContent = item.type === "reducer" ? "Редуктор" : "Деталь";
        typeCell.style.padding = "10px";

        const subtypeCell = document.createElement("td");
        subtypeCell.textContent = item.subtype;
        subtypeCell.style.padding = "10px";

        const cellCell = document.createElement("td");
        cellCell.textContent = item.cell || "Не указана";
        cellCell.style.padding = "10px";

        const dateCell = document.createElement("td");
        dateCell.textContent = item.type === "reducer" ? (item.date || "Не указана") : "-";
        dateCell.style.padding = "10px";

        row.appendChild(typeCell);
        row.appendChild(subtypeCell);
        row.appendChild(cellCell);
        row.appendChild(dateCell);

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    resultsContainer.appendChild(table);
}
//сброс фильтров
function resetFilters() {
    document.getElementById("objectType").value = "all";
    document.getElementById("reducerType").value = "all";
    document.getElementById("detType").value = "all";
    document.getElementById("cell").value = "";
    document.getElementById("dateFrom").value = "";
    document.getElementById("dateTo").value = "";

    toggleDateFields(); // Обновить отображение полей после сброса
}
//очистка результатов поиска
function clearResults() {
    document.getElementById("searchResults").innerHTML = "";
}


function openManageModal() {
    document.getElementById("manageModal").style.display = "flex";
    loadExistingOptions(); // Загружаем список существующих при открытии
}

function closeManageModal() {
    document.getElementById("manageModal").style.display = "none";
}

// Переключение между добавлением и редактированием
document.getElementById("manageAction").addEventListener("change", function() {
    const action = this.value;
    document.getElementById("selectExistingGroup").style.display = (action === "edit") ? "flex" : "none";
});

// Загрузка существующих типов для редактирования
async function loadExistingOptions() {
    const type = document.getElementById("manageObjectType").value;
    const res = await fetch(`/api/get_types?objectType=${type}`);
    const types = await res.json();

    const select = document.getElementById("existingName");
    select.innerHTML = "";
    types.forEach(t => {
        const option = document.createElement("option");
        option.value = t.id;
        option.textContent = t.name;
        select.appendChild(option);
    });
}

// При изменении редактируемого объекта — подгружать заново список
document.getElementById("manageObjectType").addEventListener("change", loadExistingOptions);

// Отправка изменений на сервер
async function submitManage() {
    const type = document.getElementById("manageObjectType").value;
    const action = document.getElementById("manageAction").value;
    const id = document.getElementById("existingName").value;
    const name = document.getElementById("newName").value;
    const description = document.getElementById("description").value;

    const payload = {
        objectType: type,
        action: action,
        id: id,
        name: name,
        description: description
    };

    try {
        const res = await fetch("/api/manage_type", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error("Ошибка запроса");

        alert("Операция выполнена успешно!");
        closeManageModal();
    } catch (error) {
        console.error(error);
        alert("Ошибка выполнения операции!");
    }
}


// Открытие модального окна журналов
function openLogsModal() {
    document.getElementById('logsModal').style.display = 'flex';
    loadUsers(); // Загружаем список пользователей
}

// Закрытие модального окна журналов
function closeLogsModal() {
    document.getElementById('logsModal').style.display = 'none';
}

// Загрузка списка пользователей
async function loadUsers(selectorId = 'userFilter') {
    try {
        const response = await fetch('/api/get_users');
        if (!response.ok) throw new Error('Ошибка загрузки пользователей');

        const users = await response.json();
        const select = document.getElementById(selectorId);
        select.innerHTML = '<option value="all">Все пользователи</option>';

        users.forEach(user => {
            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.name;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Ошибка:', error);
        alert('Не удалось загрузить список пользователей');
    }
}

// Загрузка журналов
async function loadLogs() {
    try {
        const params = new URLSearchParams();
        const userFilter = document.getElementById('userFilter').value;
        const dateFrom = document.getElementById('dateFromLogs').value;
        const dateTo = document.getElementById('dateToLogs').value;

        if (userFilter !== 'all') params.append('user_id', userFilter);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);

        const response = await fetch(`/api/get_logs?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка загрузки журналов');

        const logs = await response.json();
        displayLogs(logs);
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('logsSearchResults').innerHTML =
            `<p style="color: red;">Ошибка загрузки журналов: ${error.message}</p>`;
    }
}

// Отображение журналов в таблице
function displayLogs(logs) {
    const container = document.getElementById('logsSearchResults');
    container.innerHTML = '';

    if (logs.length === 0) {
        container.innerHTML = '<p>Записи не найдены</p>';
        return;
    }

    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.marginTop = '20px';

    // Заголовок таблицы
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.style.backgroundColor = '#E7717D';
    headerRow.style.color = 'white';

    ['ID', 'Дата', 'Пользователь', 'Операция'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        th.style.padding = '10px';
        th.style.textAlign = 'left';
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Тело таблицы
    const tbody = document.createElement('tbody');
    logs.forEach(log => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #ddd';

        const cells = [
            log.id,
            formatDateTime(log.date_time), // Форматируем дату
            log.username,
            log.operation
        ];

        cells.forEach(text => {
            const td = document.createElement('td');
            td.textContent = text;
            td.style.padding = '10px';
            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}

function formatDateTime(dateTimeStr) {
    if (!dateTimeStr) return '';
    const date = new Date(dateTimeStr);
    // форматирование с датой и временем
    const pad = num => num.toString().padStart(2, '0');
    return `${pad(date.getDate())}.${pad(date.getMonth()+1)}.${date.getFullYear()} ${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
}

//очистка журнала
function clearLogResults() {
    document.getElementById("logsSearchResults").innerHTML = "";
}


function openRepsModal() {
    document.getElementById('repsModal').style.display = 'flex';
    loadUsers('userFilterReps'); // Загружаем список пользователей
}

function closeRepsModal() {
    document.getElementById('repsModal').style.display = 'none';
}

function clearRepResults() {
    document.getElementById("repsSearchResults").innerHTML = "";
}


// Отображение отчёта в таблице
async function loadReps() {
    try {
        const params = new URLSearchParams();
        const userFilter = document.getElementById('userFilterReps').value;
        const dateFrom = document.getElementById('dateFromReps').value;
        const dateTo = document.getElementById('dateToReps').value;

        if (userFilter !== 'all') params.append('user_id', userFilter);
        if (dateFrom) params.append('date_from', dateFrom);
        if (dateTo) params.append('date_to', dateTo);

        const response = await fetch(`/api/get_reps?${params.toString()}`);
        if (!response.ok) throw new Error('Ошибка загрузки отчётов');

        const reps = await response.json();
        displayReps(reps);
    } catch (error) {
        console.error('Ошибка:', error);
        document.getElementById('repsSearchResults').innerHTML =
            `<p style="color: red;">Ошибка загрузки отчётов: ${error.message}</p>`;
    }
}

// Отображение отчёта в таблице
function displayReps(reps) {
    const container = document.getElementById('repsSearchResults');
    container.innerHTML = '';

    if (!reps || reps.length === 0) {
        container.innerHTML = '<p>Записи не найдены</p>';
        return;
    }

    const table = document.createElement('table');
    table.style.width = '100%';
    table.style.borderCollapse = 'collapse';
    table.style.marginTop = '20px';

    // Заголовок таблицы
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headerRow.style.backgroundColor = '#E7717D';
    headerRow.style.color = 'white';

    ['ID', 'Пользователь', 'Дата', 'Тип редуктора', 'Статус', 'Комментарий'].forEach(text => {
        const th = document.createElement('th');
        th.textContent = text;
        th.style.padding = '10px';
        th.style.textAlign = 'left';
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);
    table.appendChild(thead);

    // Тело таблицы
    const tbody = document.createElement('tbody');
    reps.forEach(rep => {
        const row = document.createElement('tr');
        row.style.borderBottom = '1px solid #ddd';

        // Форматируем статус для читаемого отображения
        const statusText = rep.status === 1 ? 'Успешно' :
                         rep.status === 0 ? 'Ошибка' :
                         rep.status === 2 ? 'В процессе' :
                         rep.status;

        const cells = [
            rep.id || '-',
            rep.username || rep.user_id || '-',
            formatDateTime(rep.date_time || rep.датавремя), // Форматируем дату
            rep.red_type || rep.id_типа_редуктора || '-',
            statusText,
            rep.comment || rep.комментарий || '-'
        ];

        cells.forEach(text => {
            const td = document.createElement('td');
            td.textContent = text;
            td.style.padding = '10px';

            row.appendChild(td);
        });

        tbody.appendChild(row);
    });

    table.appendChild(tbody);
    container.appendChild(table);
}