import { calculateRoutes } from "./routeCalculator.js";
import { handleCSVFile } from "./fileHandler.js";
import { mapVisualizer } from "./mapVisualizer.js";

// **Attach mapVisualizer to the global window object**
window.mapVisualizer = mapVisualizer;

// Wait for Google Maps to load before initializing
function initializeMap() {
  if (!window.googleMapsLoaded) {
    setTimeout(initializeMap, 100);
    return;
  }
  try {
    mapVisualizer.initMap();
  } catch (error) {
    console.error("Error initializing map:", error);
    setTimeout(initializeMap, 100);
  }
}

// Make initMap available globally
window.initMap = initializeMap;

// Wait for both DOM and Google Maps to be ready
function init() {
  const csvFileInput = document.getElementById("csvFile");
  if (!csvFileInput) {
    console.error("CSV file input element not found!");
  } else {
    console.log("Adding change event listener to CSV input");
    csvFileInput.addEventListener("change", handleCSVFile);
  }

  const calculateButton = document.getElementById("calculateButton");
  if (calculateButton) {
    calculateButton.addEventListener("click", calculateRoutes);
  }

  // Initialize map if Google Maps is already loaded
  if (window.googleMapsLoaded) {
    initializeMap();
  }
}

// Only start initialization after DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}

async function handleCalculateRoute() {
  // Get your mapped data
  const mappedData = getMappedData(); // You'll need to implement this

  try {
    const response = await fetch("/api/vrp/", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(mappedData),
    });

    const result = await response.json();
    if (result.success) {
      // Minimize file upload section
      document.querySelector(".file-upload-section").classList.remove("active");
      // Maximize results section
      const resultsSection = document.querySelector(".results-section");
      resultsSection.classList.add("active");

      // Display routes on map
      await window.mapVisualizer.displayRoutes(result.routes);
    } else {
      throw new Error(result.error || "Failed to calculate route");
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Error calculating route: " + error.message);
  }
}
