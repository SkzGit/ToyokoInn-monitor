const hotelSelect = document.getElementById("hotelSelect");
const roomSelect = document.getElementById("roomSelect");

fetch("../data/hotels.json")
  .then(res => res.json())
  .then(hotels => {

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
  });