import { fileTypes } from "./config.js";

function handleFileUpload() {
  const fileInput = document.createElement("input");
  fileInput.setAttribute("id", "fileInput");
  fileInput.type = "file";
  fileInput.accept = ".xls, .xlsx";
  fileInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];

    try {
      const response = await fetch("/api/excel/upload", {
        method: "POST",
        body: { file: file },
      });

      if (response.status !== 200) {
        throw new Error(`/api/excel/upload error: ${response.body.error}`);
      }

      const fileData = await response.json();
      setupColumnMappingUI(fileData);
    } catch (error) {
      console.error("Error:", error);
      alert("Error in handleFileUpload: ", error.message);
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