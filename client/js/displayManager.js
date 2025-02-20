import { getAddresses } from "./addressManager.js";

function displayResults(data) {
  const resultsSection = document.getElementById("route-details");
  resultsSection.innerHTML = "";

  const totalDistance = document.createElement("h3");
  totalDistance.textContent = `Total Distance: ${(
    data.data.objective_value / 1000
  ).toFixed(2)} km`;
  resultsSection.appendChild(totalDistance);

  data.data.routes.forEach((route, vehicleIndex) => {
    const routeDiv = document.createElement("div");
    routeDiv.className = "route";

    const routeHeader = document.createElement("div");
    routeHeader.className = "route-header";
    routeHeader.textContent = `Vehicle ${vehicleIndex + 1} - Distance: ${(
      route.distance / 1000
    ).toFixed(2)} km`;
    routeDiv.appendChild(routeHeader);

    route.stop_details.forEach((stop) => {
      const stopDiv = document.createElement("div");
      stopDiv.className = "stop";
      stopDiv.textContent = `${stop.is_depot ? "📍 " : "🚩 "}${stop.address}`;
      routeDiv.appendChild(stopDiv);
    });

    resultsSection.appendChild(routeDiv);
  });
}

function displayError(message) {
  const resultsSection = document.getElementById("route-details");
  resultsSection.innerHTML = `
        <div class="error-message">
            ${message}
        </div>
    `;
}

export { displayResults, displayError };
