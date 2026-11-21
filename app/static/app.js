const countrySelect = document.getElementById("countrySelect");
const monthInput = document.getElementById("monthInput");
const btnToday = document.getElementById("btnToday");
const calendar = document.getElementById("calendar");
const detailSection = document.getElementById("holidayDetails");
const detailDate = document.getElementById("detailDate");
const detailList = document.getElementById("detailList");

let selectedCountry = "US";
let selectedDate = new Date();

async function loadCountries() {
    const res = await fetch("/api/countries");
    const countries = await res.json();
    countrySelect.innerHTML = countries
        .map((c) => `<option value="${c.code}">${c.name} (${c.code})</option>`)
        .join("");
    selectedCountry = countries[0]?.code || "US";
}

countrySelect.addEventListener("change", (e) => {
    selectedCountry = e.target.value;
    renderCalendar();
});

monthInput.addEventListener("change", (e) => {
    const [y, m] = e.target.value.split("-").map(Number);
    selectedDate = new Date(y, m - 1, 1);
    renderCalendar();
});

btnToday.addEventListener("click", () => {
    selectedDate = new Date();
    monthInput.value = selectedDate.toISOString().slice(0, 7);
    renderCalendar();
});

async function renderCalendar() {
    const year = selectedDate.getFullYear();
    const month = selectedDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay(); // 0 = Вс
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const holidays = await fetch(
        `/api/holidays/${selectedCountry}/${year}`
    )
        .then((r) => r.json())
        .catch(() => []);

    const holidayMap = {};
    holidays.forEach((h) => {
        const d = new Date(h.date + "T00:00:00");
        if (d.getMonth() === month && d.getFullYear() === year) {
            holidayMap[d.getDate()] = holidayMap[d.getDate()] || [];
            holidayMap[d.getDate()].push(h);
        }
    });

    calendar.innerHTML = "";

    const weekdays = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];
    weekdays.forEach((w) => {
        const div = document.createElement("div");
        div.className = "weekday";
        div.textContent = w;
        calendar.appendChild(div);
    });

    // Смещение: неделя начинается с Пн (getDay: 0=Вс, 1=Пн ...)
    const startOffset = (firstDay + 6) % 7;
    for (let i = 0; i < startOffset; i++) {
        calendar.appendChild(document.createElement("div"));
    }

    for (let d = 1; d <= daysInMonth; d++) {
        const dayDiv = document.createElement("div");
        dayDiv.className = "day";
        dayDiv.textContent = d;

        const fullDate = new Date(year, month, d);
        if (fullDate.getTime() === today.getTime()) {
            dayDiv.classList.add("today");
        }

        if (holidayMap[d]) {
            dayDiv.classList.add("holiday");
            const badge = document.createElement("span");
            badge.className = "holiday-badge";
            badge.textContent = holidayMap[d].length;
            dayDiv.appendChild(badge);
        }

        dayDiv.addEventListener("click", () => {
            document
                .querySelectorAll(".day.selected")
                .forEach((el) => el.classList.remove("selected"));
            dayDiv.classList.add("selected");
            showDetails(year, month, d, holidayMap[d] || []);
        });

        calendar.appendChild(dayDiv);
    }
}

function showDetails(year, month, day, holidays) {
    const dateStr = `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    detailDate.textContent = `${day}.${String(month + 1).padStart(2, "0")}.${year}`;
    detailList.innerHTML = "";

    if (holidays.length === 0) {
        detailList.innerHTML = "<li>Праздников не найдено</li>";
    } else {
        holidays.forEach((h) => {
            const li = document.createElement("li");
            li.innerHTML = `<strong>${h.localName || h.name}</strong>${
                h.name ? ` — ${h.name}` : ""
            }`;
            detailList.appendChild(li);
        });
    }

    detailSection.style.display = "block";
}

monthInput.value = new Date().toISOString().slice(0, 7);
loadCountries().then(renderCalendar);