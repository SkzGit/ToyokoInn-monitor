const hotelSelect = document.getElementById("hotelSelect");
const roomSelect = document.getElementById("roomSelect");
const dateSections = {};
let hotels = [];

fetch("/data/hotels.json")
  .then(res => res.json())
  .then(data => {

    hotels = data;

    hotelSelect.innerHTML = "";

    hotels.forEach(hotel => {
      const option = document.createElement("option");
      option.value = hotel.id;
      option.textContent = hotel.name;
      hotelSelect.appendChild(option);
    });

    function updateRooms() {
      roomSelect.innerHTML = "";

      const hotel = hotels.find(h => h.id === hotelSelect.value);

      hotel.rooms.forEach(room => {
        const option = document.createElement("option");
        option.value = room.search;
        option.textContent = room.display;
        roomSelect.appendChild(option);
      });
    }

    hotelSelect.addEventListener("change", updateRooms);

    updateRooms();

    initializeIntervalSelects();

    loadSettingsFromServer();

    updateMonitorStatus();

    updateMonitorLog();
    updateHistory();

    setInterval(() => {
        updateMonitorLog();
        updateHistory();
    }, 3000);

  });


const addButton = document.getElementById("addTarget");
const targetList = document.getElementById("targetList");

// 候補を追加
addButton.addEventListener("click", addCandidate);

function updateDateTitle(section) {

    const content = section.querySelector(".date-content");
    const title = section.querySelector("h3");

    const date = section.dataset.date;

    const count = content.querySelectorAll(".candidate").length;

    const mark =
        content.style.display === "none" ? "▶" : "▼";

    const week = ["日", "月", "火", "水", "木", "金", "土"];
    const d = new Date(date);
    const weekday = week[d.getDay()];

    title.textContent =
        `${mark} ${date}（${weekday}）　候補${count}件`;
}

function createCandidateElement(hotelId, roomSearch) {

  const hotel = hotels.find(h => h.id === hotelId);

  const room = hotel.rooms.find(
    r => r.search === roomSearch
  );
    
  const item = document.createElement("div");
  item.className = "candidate";

  item.innerHTML = `
      <div class="candidateGrid">

          <label>🏨 ホテル</label>
          <div class="hotel" data-id="${hotelId}">
              ${hotel.name}
          </div>

          <label>🛏 部屋タイプ</label>
          <div class="room" data-search="${roomSearch}">
              ${room.display}
          </div>

          <label>🚭 喫煙</label>
          <select class="smoking">
              <option selected>指定なし</option>
              <option>禁煙</option>
              <option>喫煙</option>
          </select>

      </div>
  `;

  // ↑ボタン
  const up = document.createElement("button");
  up.textContent = "⬆ 上へ";
  up.onclick = () => {

    let prev = item.previousElementSibling;

    while (prev && !prev.classList.contains("candidate")) {
      prev = prev.previousElementSibling;
    }

    if (!prev) return;

    item.parentNode.insertBefore(item, prev);
  };

  // ↓ボタン
  const down = document.createElement("button");
  down.textContent = "⬇ 下へ";
  down.onclick = () => {

    let next = item.nextElementSibling;

    while (next && !next.classList.contains("candidate")) {
      next = next.nextElementSibling;
    }

    if (!next) return;

    item.parentNode.insertBefore(next, item);
  };

  // 削除ボタン
  const del = document.createElement("button");
  del.textContent = "🗑 削除";
  del.onclick = () => {
      if (!confirm("この候補を削除しますか？")) {
          return;
      }
      const section = item.closest(".date-section");

      item.remove();

      updateDateTitle(section);

  };

  // ボタンをまとめる
  const buttonArea = document.createElement("div");
  buttonArea.className = "candidateButtons";

  buttonArea.appendChild(up);
  buttonArea.appendChild(down);
  buttonArea.appendChild(del);

  item.appendChild(buttonArea);

  return item;
}

function addCandidate() {

  const date = document.getElementById("stayDate").value;

  if (!dateSections[date]) {
    alert("先に宿泊日を追加してください");
    return;
  }

  const hotelId = hotelSelect.value;
  const roomSearch = roomSelect.value;

  const item = createCandidateElement(
      hotelId,
      roomSearch
  );

  const content = dateSections[date].querySelector(".date-content");

  content.appendChild(item);
  updateDateTitle(dateSections[date]);
}

function createNumberOptions(max, selected, start = 1) {

  return Array.from({ length: max - start + 1 }, (_, i) => {

    const n = i + start;

    return `
      <option value="${n}" ${selected === n ? "selected" : ""}>
        ${n}
      </option>
    `;

  }).join("");

}

function initializeIntervalSelects() {

    const hourSelect = document.getElementById("intervalHours");
    const minuteSelect = document.getElementById("intervalMinutes");

    if (!hourSelect || !minuteSelect) {
        return;
    }

    hourSelect.innerHTML = createNumberOptions(23, 0, 0);

    const minuteValues = Array.from({ length: 60 }, (_, i) => i);

    minuteSelect.innerHTML = minuteValues.map(m => `
        <option value="${m}" ${m === 30 ? "selected" : ""}>
            ${m}
        </option>
    `).join("");

}

const addDateButton = document.getElementById("addDate");

// 宿泊日を追加
addDateButton.addEventListener("click", addDate);

function addDate(dateData = null) {

  // ボタンクリック時は Event が渡されるので無視する
  if (dateData instanceof Event) {
    dateData = null;
  }

  const date = dateData
    ? dateData.date
    : document.getElementById("stayDate").value;

  if (!date) {
    alert("宿泊日を選択してください");
    return;
  }

  if (dateSections[date]) {
    if (!dateData) {
      alert("その宿泊日は追加済みです");
    }
    return;
  }

const section = document.createElement("div");
section.className = "date-section";
section.dataset.date = date;
section.dataset.collapsed = "false";

const content = document.createElement("div");
content.className = "date-content";

const title = document.createElement("h3");

  title.style.cursor = "pointer";

  title.addEventListener("click", () => {
      // 次のSTEPでここに折りたたみ処理を書く
  });

  const header = document.createElement("div");
  header.className = "date-header";

  const delDate = document.createElement("button");
  delDate.textContent = "×";
  delDate.className = "removeDateButton";

  delDate.onclick = () => {
      if (!confirm("この宿泊日と、その候補をすべて削除しますか？")) {
          return;
      }
      section.remove();
      delete dateSections[date];
  };

  header.appendChild(title);
  header.appendChild(delDate);

  section.appendChild(header);

  header.style.cursor = "pointer";

  title.addEventListener("click", (e) => {

      // ×ボタンを押した時は折りたたまない
      if (e.target === delDate) {
          return;
      }

      if (content.style.display === "none") {

          content.style.display = "block";
          section.dataset.collapsed = "false";

          updateDateTitle(section);

      } else {

          content.style.display = "none";
          section.dataset.collapsed = "true";

          updateDateTitle(section);

      }

  });

  const settings = document.createElement("div");
  settings.className = "date-settings";

  const people = dateData ? dateData.people : 2;
  const rooms = dateData ? dateData.rooms : 1;
  const nights = dateData ? dateData.nights : 1;

  const nightOptions = createNumberOptions(10, nights);
  const peopleOptions = createNumberOptions(4, people);
  const roomOptions = createNumberOptions(4, rooms);

settings.innerHTML = `
<div class="settingItem">
  <label>宿泊日数</label>
  <select>
    ${nightOptions}
  </select>
</div>

<div class="settingItem">
  <label>人数</label>
  <select>
    ${peopleOptions}
  </select>
</div>

<div class="settingItem">
  <label>部屋数</label>
  <select>
    ${roomOptions}
  </select>
</div>
`;

  content.appendChild(settings);

  section.appendChild(content);
  targetList.appendChild(section);

  dateSections[date] = section;
  updateDateTitle(section);
}

function restoreConfig(config) {

  // 画面をクリア
  targetList.innerHTML = "";

  for (const key in dateSections) {
    delete dateSections[key];
  }

  // 宿泊日ごとに復元
  config.dates.forEach(dateData => {

    addDate(dateData);

    const section = dateSections[dateData.date];

    if (dateData.collapsed) {

        const content = section.querySelector(".date-content");

        content.style.display = "none";
        section.dataset.collapsed = "true";

        updateDateTitle(section);
    }

    dateData.candidates.forEach(candidate => {

      const item = createCandidateElement(
          candidate.hotelId,
          candidate.roomSearch
      );

      // 喫煙設定を復元
      item.querySelector(".smoking").value = candidate.smoking;

      section.querySelector(".date-content").appendChild(item);
      updateDateTitle(section);

    });

  });

}

document.getElementById("saveSettings").addEventListener("click", saveSettings);

function getConfig() {

  const settings = [];

  const intervalHours =
    Number(document.getElementById("intervalHours").value);

  const intervalMinutes =
      Number(document.getElementById("intervalMinutes").value);

  if (intervalHours === 0 && intervalMinutes === 0) {
      alert("監視間隔は1分以上にしてください。");
      return null;
  }

  for (const [date, section] of Object.entries(dateSections)) {

    const candidateElements = section.querySelectorAll(".candidate");

    const candidates = [];

    candidateElements.forEach(item => {

      candidates.push({
        hotelId: item.querySelector(".hotel").dataset.id,
        roomSearch: item.querySelector(".room").dataset.search,
        smoking: item.querySelector(".smoking").value,
      });

    });

    const selects = section.querySelectorAll(".date-settings select");

    settings.push({
        date,
        collapsed: section.dataset.collapsed === "true",
        nights: Number(selects[0].value),
        people: Number(selects[1].value),
        rooms: Number(selects[2].value),
        candidates
    });
  }

  const config = {
      version: 1,
      intervalHours,
      intervalMinutes,
      dates: settings
  };

  return config;
}  

async function saveSettings() {

  const config = getConfig();

  if (config === null) {
    return;
  }

  const response = await fetch("/settings", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(config)
  });

  if (response.ok) {
    alert("保存しました");
  } else {
    alert("保存に失敗しました");
  }

}

document
  .getElementById("importFile")
  .addEventListener("change", importSettings);

async function importSettings(event) {

  const file = event.target.files[0];

  if (!file) return;

  const reader = new FileReader();

  reader.onload = async e => {

    try {

      const config = JSON.parse(e.target.result);

      // サーバーへ保存
      const response = await fetch("/import-settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(config)
      });

      if (!response.ok) {
        throw new Error("復元に失敗しました。");
      }

      // 画面更新
      restoreConfig(config);

      alert("復元しました。");

    } catch (err) {

      console.error(err);
      alert(err.message);

    }

  };

  reader.readAsText(file);

}

async function loadSettingsFromServer() {

  try {

    const response = await fetch("/settings");

    if (!response.ok) {
      throw new Error("設定を読み込めませんでした。");
    }

    const config = await response.json();

    document.getElementById("intervalHours").value =
        config.intervalHours ?? 0;

    document.getElementById("intervalMinutes").value =
        config.intervalMinutes ?? 30;

    restoreConfig(config);

  } catch (err) {

    console.error(err);

  }

}

document
  .getElementById("startMonitor")
  .addEventListener("click", startMonitor);

document
  .getElementById("stopMonitor")
  .addEventListener("click", stopMonitoring);

document
  .getElementById("exportSettings")
  .addEventListener("click", exportSettings);

document
  .getElementById("gitPush")
  .addEventListener("click", async () => {

    console.log("GitHubへ保存ボタンが押されました");

    const response = await fetch("/git-push", {
      method: "POST",
    });

    const result = await response.json();

    console.log(result);

    if (result.success) {
        alert(result.message);
    } else {
        alert(result.message);
    }

});

document
  .getElementById("importSettings")
  .addEventListener("click", () => {
    document
      .getElementById("importFile")
      .click();
});

async function startMonitor() {
    if (!confirm("監視を開始しますか？")) {
        return;
    }

    const clearHistory = confirm(
        "通知履歴をクリアしますか？"
    );

    const clearState = clearHistory;

    const configs = getConfig();

    if (configs === null) {
        return;
    }    
    
    const response = await fetch("/start", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            clearHistory,
            clearState
        })
    });

    const result = await response.json();

    if (result.result === "ok") {
        alert("監視を開始しました");
        updateMonitorStatus();
        updateMonitorLog();
        updateHistory();

    } else if (result.result === "already_running") {
        alert("すでに監視中です");

    } else {
        alert("監視開始に失敗しました");
    }

}

async function stopMonitoring() {

  const response = await fetch("/stop", {
    method: "POST"
  });

  const result = await response.json();

  if (result.result === "ok") {

    alert("監視を停止しました");

    updateMonitorStatus();

  } else if (result.result === "not_running") {

    alert("監視は開始されていません");

  } else {

    alert("停止に失敗しました");

  }

}

async function updateMonitorStatus() {

  const response = await fetch("/status");

  const result = await response.json();

  const status = document.getElementById("monitorStatus");

  if (result.running) {

      status.textContent = "状態：🟢 監視中";
      disableEditing(true);

  } else {

      status.textContent = "状態：⚪ 停止中";
      disableEditing(false);

  }

}

async function updateMonitorLog() {

    const response = await fetch("/logs");
    const result = await response.json();

    const log = document.getElementById("monitorLog");

    log.textContent = result.logs.join("\n");

    log.scrollTop = log.scrollHeight;

}

function disableEditing(disabled) {

  // 上部のボタン
  document.getElementById("addDate").disabled = disabled;
  document.getElementById("addTarget").disabled = disabled;
  document.getElementById("saveSettings").disabled = disabled;
  document.getElementById("exportSettings").disabled = disabled;
  document.getElementById("importSettings").disabled = disabled;

  // 上部入力
  document.getElementById("stayDate").disabled = disabled;
  document.getElementById("hotelSelect").disabled = disabled;
  document.getElementById("roomSelect").disabled = disabled;

  // 各宿泊日の設定
  document.querySelectorAll(".date-settings select")
    .forEach(e => e.disabled = disabled);

  // 喫煙設定
  document.querySelectorAll(".smoking")
    .forEach(e => e.disabled = disabled);

  // 各候補のボタン（↑ ↓ ×）
  document.querySelectorAll(".candidate button")
    .forEach(e => e.disabled = disabled);

  // 各宿泊日の削除ボタン（×）
  document.querySelectorAll("h3 + button")
    .forEach(e => e.disabled = disabled);

}

function exportSettings() {
    window.location.href = "/export-settings";
}

async function updateHistory() {

    const response = await fetch("/history");
    const result = await response.json();

    const history = document.getElementById("history");

    history.innerHTML = "";

    (result.history ?? []).slice().forEach(item => {

        const card = document.createElement("div");

        card.className = "historyCard";

        card.innerHTML = `
            <div>🕒 ${item.time}</div>
            <div>📅 ${item.date}</div>
            <div>🏨 ${item.hotel}</div>
            <div>🛏 ${item.room}</div>
            <div>${item.smoking === "禁煙" ? "🚭" : "🚬"} ${item.smoking}</div>
            <div>💰 ${item.price}円</div>
            <div>🟢 残り${item.remaining}室</div>
        `;

        history.appendChild(card);

    });

}