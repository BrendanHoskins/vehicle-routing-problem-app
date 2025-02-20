import { getCsvData } from "./fileHandler.js";
import { displayResults, displayError } from "./displayManager.js";

async function calculateRoutes() {
  const csvData = getCsvData();

  if (!csvData.file) {
    displayError("No CSV file selected");
    return;
  }

  const calculateButton = document.getElementById("calculateButton");
  calculateButton.disabled = true;
  calculateButton.textContent = "Calculating...";

  try {
    // Read the file content
    const fileContent = await csvData.file.text();

    const response = await fetch("/api/vrp/solve", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        num_vehicles: 1,
        csv_data: {
          content: fileContent,
          selectedColumns: csvData.selectedColumns,
          columnMappings: csvData.columnMappings,
          delimiter: csvData.delimiter,
        },
      }),
    });

    const data = await response.json();
    console.log(data)
    if (!data.success) {
      throw new Error(data.error || "Failed to calculate routes");
    }

    // Initialize map visualization
    const resultsSection = document.querySelector(".results-section");
    resultsSection.classList.add("active");

    // Display the results
    displayResults(data);

    // Visualize on map if mapVisualizer is available
    if (window.mapVisualizer && data.data.routes) {
      await window.mapVisualizer.displayRoutes(data.data.routes);
    }
  } catch (error) {
    console.error("Error:", error);
    displayError(error.message);
  } finally {
    calculateButton.disabled = false;
    calculateButton.textContent = "Calculate Routes";
  }
}

export { calculateRoutes };
