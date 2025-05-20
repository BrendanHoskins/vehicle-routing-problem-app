import { fileTypes } from "./config.js";

let currentFormData = new FormData();
let csvFileContent = null;
let selectedColumnsMap = {};
let columnMappings = {};
let delimiter = ",";

function handleFileUpload(event, fileType) {
  const fileInput = document.createElement("input");
  fileInput.setAttribute("id", "fileInput");
  fileInput.type = "file";
  fileInput.accept = ".csv";
  fileInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Store the file content
    csvFileContent = file;

    // Validate file type
    if (!file.name.endsWith(".csv")) {
      alert("Please upload a CSV file");
      return;
    }

    const formData = new FormData();
    formData.append("csv", file);

    try {
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
      selectedColumnsMap[fileType] = data.columns;
      delimiter = data.delimiter || ",";
      setupColumnMappingUI(data.columns, fileType);

      currentFormData.append(fileType, file);
    } catch (error) {
      console.error("Error:", error);
      alert("Error uploading CSV: " + error.message);
    }
  });
  fileInput.click();
}

function createMappingSelect(columns, fileType) {
  const select = document.createElement("select");
  select.innerHTML = '<option value="">Select mapping...</option>';

  // Add mapping options based on file type
  if (fileTypes[fileType] && fileTypes[fileType].mappings) {
    fileTypes[fileType].mappings.forEach((mapping) => {
      select.innerHTML += `<option value="${mapping.value}">${mapping.label}</option>`;
    });
  }

  return select;
}

function setupColumnMappingUI(columns, fileType) {
  // Create mapping container if it doesn't exist
  let mappingContainer = document.querySelector(
    `.mapping-container-${fileType}`
  );
  if (!mappingContainer) {
    mappingContainer = document.createElement("div");
    mappingContainer.className = `mapping-container mapping-container-${fileType}`;

    const fileUploadCard = document.getElementById(`${fileType}Div`);
    fileUploadCard.appendChild(mappingContainer);
  }

  mappingContainer.innerHTML = "";

  columns.forEach((column) => {
    const row = document.createElement("div");
    row.className = "mapping-row";
    row.innerHTML = `<span>${column}:</span>`;

    const select = createMappingSelect(columns, fileType);
    select.dataset.column = column;
    select.dataset.fileType = fileType;
    row.appendChild(select);
    mappingContainer.appendChild(row);
  });

  // Add default mapping button
  addDefaultMappingButton(fileType, mappingContainer);

  setupMappingValidation();
}

function setupMappingValidation() {
  const selects = document.querySelectorAll(".mapping-container select");
  const submitButton = document.getElementById("submitButton");

  selects.forEach((select) => {
    select.addEventListener("change", () => {
      // Update the column mappings
      const column = select.dataset.column;
      const mapping = select.value;
      const fileType = select.dataset.fileType;

      if (!columnMappings[fileType]) {
        columnMappings[fileType] = {};
      }

      if (mapping) {
        columnMappings[fileType][mapping] = column;
      }

      // Check if required mappings exist for each file type
      let allValid = true;
      Object.values(fileTypes).forEach((fileTypeConfig) => {
        if (fileTypeConfig.required && fileTypeConfig.validationKey) {
          const fileTypeMappings = columnMappings[fileTypeConfig.id] || {};
          if (!fileTypeMappings[fileTypeConfig.validationKey]) {
            allValid = false;
          }
        }
      });

      submitButton.disabled = !allValid;
    });
  });
}

async function handleFileSubmit() {
  // First, read all files
  const fileReadPromises = [];
  const dataToSend = {};

  for (const fileType of Object.keys(columnMappings)) {
    if (currentFormData.has(fileType)) {
      const fileBlob = currentFormData.get(fileType);

      // Create a promise to read each file
      const filePromise = new Promise((resolve, reject) => {
        const fileReader = new FileReader();

        fileReader.onload = () => {
          const fileContent = fileReader.result;
          dataToSend[fileType] = {
            content: fileContent,
            selectedColumns: selectedColumnsMap[fileType],
            columnMappings: columnMappings[fileType],
            delimiter: delimiter,
          };
          resolve();
        };

        fileReader.onerror = () => reject(new Error("Failed to read file"));
        fileReader.readAsText(fileBlob);
      });

      fileReadPromises.push(filePromise);
    }
  }

  // Wait for all files to be read
  await Promise.all(fileReadPromises);

  // Now send the data
  const response = await fetch("/api/vrp/solve", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ csv_data: dataToSend }),
  });

  return response;
}

export { handleFileUpload, handleFileSubmit };

// Add event listener for Calculate Route button
document.getElementById("submitButton").addEventListener("click", async () => {
  try {
    const response = await handleFileSubmit();
    if (response.ok) {
      const data = await response.json();
      console.log("VRP solution:", data);
      // Add code here to display the solution
    } else {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    console.error("Error:", error);
    alert("Error calculating route: " + error.message);
  }
});

function addDefaultMappingButton(fileType, mappingContainer) {
  // Create the default mapping button
  const defaultButton = document.createElement("button");
  defaultButton.textContent = "Set Default Mappings";
  defaultButton.className = "default-mapping-button";

  // Insert before mapping container
  mappingContainer.parentNode.insertBefore(defaultButton, mappingContainer);

  // Add click event to apply default mappings
  defaultButton.addEventListener("click", () => {
    const selects = mappingContainer.querySelectorAll("select");
    const alreadyMappedValues = new Set(); // Track already mapped internal values

    selects.forEach((select) => {
      const column = select.dataset.column.toLowerCase().trim();
      let bestMapping = null;

      if (fileTypes[fileType] && fileTypes[fileType].mappings) {
        let potentialMappings = [];

        for (const mapping of fileTypes[fileType].mappings) {
          if (alreadyMappedValues.has(mapping.value)) {
            continue; // This internal value is already mapped, skip
          }

          const mappingValueLower = mapping.value.toLowerCase().trim();
          const mappingLabelLower = mapping.label.toLowerCase().trim();

          // Scoring: Higher is better
          let score = 0;
          if (column === mappingValueLower) score = 10; // Exact match to value
          else if (column === mappingLabelLower)
            score = 9; // Exact match to label
          else if (
            mappingValueLower.includes(column) &&
            column.includes(mappingValueLower)
          )
            score = 8; // Strong bi-directional partial match
          else if (
            mappingLabelLower.includes(column) &&
            column.includes(mappingLabelLower)
          )
            score = 7; // Strong bi-directional partial match for label
          else if (column.includes(mappingValueLower)) score = 6;
          else if (column.includes(mappingLabelLower)) score = 5;
          else if (mappingValueLower.includes(column)) score = 4;
          else if (mappingLabelLower.includes(column)) score = 3;
          // Specific check for "uid" to avoid mapping "Truck UID" to employee "uid" if "UID" column is present
          if (mapping.value === "uid" && column.includes("truck")) score = 0; // Penalize mapping "uid" to "Truck UID" like columns for employees
          if (mapping.value === "truck_uid" && !column.includes("truck"))
            score = 0; // Penalize mapping "truck_uid" to non-truck-related columns

          if (score > 0) {
            potentialMappings.push({ value: mapping.value, score: score });
          }
        }

        if (potentialMappings.length > 0) {
          potentialMappings.sort((a, b) => b.score - a.score); // Sort by score descending
          bestMapping = potentialMappings[0].value;
        }
      }

      if (bestMapping) {
        select.value = bestMapping;
        alreadyMappedValues.add(bestMapping); // Mark this internal value as mapped

        // Trigger change event to update mappings
        const event = new Event("change");
        select.dispatchEvent(event);
      } else {
        // If no mapping found, ensure it's reset or set to default
        if (select.value !== "") {
          select.value = ""; // Reset if previously set
          const event = new Event("change");
          select.dispatchEvent(event);
        }
      }
    });
  });
}
