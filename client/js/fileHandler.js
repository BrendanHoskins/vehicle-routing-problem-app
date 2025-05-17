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

    // Apply default mappings based on column names and fileType
    selects.forEach((select) => {
      const column = select.dataset.column.toLowerCase();
      let bestMapping = null;

      // Try to find the best match for this column
      if (fileTypes[fileType] && fileTypes[fileType].mappings) {
        // Match by exact column name
        const exactMatch = fileTypes[fileType].mappings.find(
          (m) =>
            column === m.label.toLowerCase() || column === m.value.toLowerCase()
        );

        if (exactMatch) {
          bestMapping = exactMatch.value;
        } else {
          // Match by contains
          const containsMatch = fileTypes[fileType].mappings.find(
            (m) =>
              column.includes(m.label.toLowerCase()) ||
              column.includes(m.value.toLowerCase()) ||
              m.label.toLowerCase().includes(column) ||
              m.value.toLowerCase().includes(column)
          );

          if (containsMatch) {
            bestMapping = containsMatch.value;
          }
        }
      }

      // Apply the mapping if found
      if (bestMapping) {
        select.value = bestMapping;

        // Trigger change event to update mappings
        const event = new Event("change");
        select.dispatchEvent(event);
      }
    });
  });
}
