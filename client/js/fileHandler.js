let csvFileContent = null;
let selectedColumns = [];
let columnMappings = {};
let delimiter = ",";

function createMappingSelect(columns) {
  const select = document.createElement("select");
  select.innerHTML = `
    <option value="">Select mapping...</option>
    <option value="address">Address</option>
    <option value="identifier">Unique Identifier</option>
    <option value="depot">Depot?</option>
  `;
  return select;
}

function setupColumnMappingUI(columns) {
  const mappingContainer = document.querySelector(".mapping-container");
  mappingContainer.innerHTML = "";

  columns.forEach((column) => {
    const row = document.createElement("div");
    row.className = "mapping-row";
    row.innerHTML = `<span>${column}:</span>`;

    const select = createMappingSelect();
    select.dataset.column = column;
    row.appendChild(select);
    mappingContainer.appendChild(row);
  });

  // Show mapping section and setup validation
  document.getElementById("columnMapping").style.display = "block";
  setupMappingValidation();
}

function setupMappingValidation() {
  const selects = document.querySelectorAll(".mapping-container select");
  const calculateButton = document.getElementById("calculateButton");

  selects.forEach((select) => {
    select.addEventListener("change", () => {
      // Validate that at least one address mapping exists
      const addressMapped = Array.from(selects).some(
        (s) => s.value === "address"
      );
      calculateButton.disabled = !addressMapped;
    });
  });
}

async function handleCSVFile(event) {
  const file = event.target.files[0];
  if (!file) return;

  // Store the file content
  csvFileContent = file; // Store the actual file object

  // Validate file type
  if (!file.name.endsWith(".csv")) {
    alert("Please upload a CSV file");
    return;
  }

  const formData = new FormData();
  formData.append("csv", file); // Changed back to "csv" to match backend expectation

  const uploadButton = event.target.nextElementSibling;
  uploadButton.textContent = "Uploading...";
  uploadButton.disabled = true;

  try {
    console.log("Sending request to /api/csv/upload");
    const response = await fetch("/api/csv/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data = await response.json();
    if (!data.success) {
      throw new Error(data.error || "Failed to upload CSV");
    }

    console.log("Received response:", data);
    selectedColumns = data.columns;
    delimiter = data.delimiter || ",";
    setupColumnMappingUI(data.columns);
  } catch (error) {
    console.error("Error:", error);
    alert("Error uploading CSV: " + error.message);
  } finally {
    uploadButton.textContent = "Choose CSV File";
    uploadButton.disabled = false;
  }
}

function getCsvData() {
  // Gather the column mappings
  const selects = document.querySelectorAll(".mapping-container select");
  columnMappings = {};
  selects.forEach((select) => {
    const column = select.dataset.column;
    const mapping = select.value;
    if (mapping) {
      columnMappings[mapping] = column;
    }
  });

  return {
    file: csvFileContent, // Now returning the stored file object
    selectedColumns,
    columnMappings,
    delimiter,
  };
}

export { handleCSVFile, getCsvData };
