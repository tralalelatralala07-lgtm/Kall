const countrySelect = document.getElementById("countrySelect");
const btnLoad = document.getElementById("btnLoad");
const list = document.getElementById("holidayList");
const info = document.getElementById("info");

async function loadCountries() {
    const res = await fetch("/api/countries");
    const countries = await res.json();
    countrySelect.innerHTML = countries.map(c => `<option value="${c.code}">${c.name}</option>`).join("");
}

async function loadHolidays() {
    const country = countrySelect.value;
    btnLoad.disabled = true;
    btnLoad.textContent = "Загрузка...";
    list.innerHTML = "";
    info.textContent = "";

    try {
        const res = await fetch(`/api/slavic/forward?country=${country}&days=365`);
        const data = await res.json();
        if (!data || data.length === 0) {
            info.textContent = "Праздники не найдены.";
            return;
        }
        info.textContent = "Найдено " + data.length + " праздник(ов) на 365 дней вперёд.";
        list.innerHTML = data.map(h => `
            <div class="holiday-item">
                <span class="date">${h.date}</span>
                <span class="name">${h.name}</span>
            </div>
        `).join("");
    } catch (e) {
        info.textContent = "Ошибка загрузки праздника.";
        console.error(e);
    } finally {
        btnLoad.disabled = false;
        btnLoad.textContent = "Загрузить праздники";
    }
}

countrySelect.addEventListener("change", loadHolidays);
btnLoad.addEventListener("click", loadHolidays);

loadCountries().then(loadHolidays);
