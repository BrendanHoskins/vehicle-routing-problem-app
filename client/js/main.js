import { fileTypes } from "./config.js";
import { handleFileUpload, handleFileSubmit } from "./fileHandler.js";

document.addEventListener("DOMContentLoaded", () => {
  const getStartedBtn = document.getElementById("get-started-btn");
  const initialView = document.getElementById("initial-view");
  const fileUploadView = document.getElementById("file-upload-view");
  const mappingsConfigView = document.getElementById("mappings-config-view");
  const visualizeExportView = document.getElementById("visualize-export-view");
  const filePickerBtn = document.getElementById("file-picker-btn");
  const dropZone = document.getElementById("drop-zone");
  const fileUploadLoader = document.getElementById("file-upload-loader");
  const sheetTabsContainer = document.getElementById("sheet-tabs-container");
  const sheetContentContainer = document.getElementById(
    "sheet-content-container"
  );
  const calculateRouteBtn = document.getElementById("calculate-route-btn");
  const calculateLoader = document.getElementById("calculate-loader");
  const visualizeLoader = document.getElementById("visualize-loader");
  const fileInput = document.getElementById("fileInput"); // Get the persistent file input
  const mapDefaultsBtn = document.getElementById("map-defaults-btn"); // Added

  let uploadedFileData = null;
  let currentFileId = null; // Added to store the file_id
  let currentMappings = {}; // { sheetName: { mappingId: excelColumn } }
  let sheetsConfig = {}; // To store which fileType config corresponds to which sheet

  function switchView(viewToShow, viewToHide = null) {
    if (viewToHide) {
      viewToHide.classList.remove("visible");
      // Wait for hide animation to mostly complete
      setTimeout(() => {
        viewToHide.classList.add("hidden");
        viewToShow.classList.remove("hidden");
        setTimeout(() => viewToShow.classList.add("visible"), 50); // Slight delay to trigger animation
      }, 400);
    } else {
      // For initial transition or when no specific view is being hidden in sequence
      document.querySelectorAll(".view.visible, #initial-view").forEach((v) => {
        v.classList.remove("visible");
        if (v.id !== "initial-view") v.classList.add("hidden");
      });
      initialView.classList.add("hidden"); // Ensure initial view is also hidden
      viewToShow.classList.remove("hidden");
      setTimeout(() => viewToShow.classList.add("visible"), 50);
    }
  }

  getStartedBtn.addEventListener("click", () => {
    switchView(fileUploadView, initialView);
    getStartedBtn.classList.add("hidden");
  });

  filePickerBtn.addEventListener("click", () => {
    fileInput.click(); // Directly click the persistent input
  });

  // Add change listener to the persistent file input
  fileInput.addEventListener("change", processFile);

  // Setup file input listener from handleFileUpload
  // Ensure handleFileUpload is called to setup its internal listener, or integrate its logic here.
  // For now, assuming handleFileUpload sets up a global input or we create one.
  // The handleFileUpload function in fileHandler.js creates its own input and clicks it.
  // We need to intercept the file processing part.

  async function processFile(eventOrFile) {
    const file = eventOrFile.target ? eventOrFile.target.files[0] : eventOrFile;
    if (!file) return;

    fileUploadLoader.classList.remove("hidden");
    dropZone.classList.add("hidden");
    filePickerBtn.classList.add("hidden");

    try {
      const responseData = await handleFileUpload(file);

      fileUploadLoader.classList.add("hidden");

      if (
        !responseData ||
        !responseData.file_id ||
        !responseData.excel_sheets_and_columns_to_be_mapped
      ) {
        throw new Error("Invalid data structure received from file upload.");
      }

      currentFileId = responseData.file_id; // Store file_id
      uploadedFileData = responseData.excel_sheets_and_columns_to_be_mapped; // Store the actual sheet data

      console.log("Uploaded File ID:", currentFileId);
      console.log("Uploaded Sheets Data:", uploadedFileData);

      setupMappingUI();
      switchView(mappingsConfigView, fileUploadView);
    } catch (error) {
      console.error("Error processing file:", error);
      alert(`Error: ${error.message}`);
      fileUploadLoader.classList.add("hidden");
      dropZone.classList.remove("hidden"); // Reset UI
      filePickerBtn.classList.remove("hidden");
    }
  }

  // Add event listener to the file input created by handleFileUpload
  // Since handleFileUpload creates a new input each time, we need to ensure we re-attach or use a persistent one.
  // The approach below is to listen for a custom event or directly call processFile after file selection.
  // For simplicity, let's modify handleFileUpload to emit an event or call a callback.
  // Or, we can just rely on the user clicking our button which calls processFile directly.
  // The `handleFileUpload` in `fileHandler.js` creates its own input and calls `click()`.
  // To make this work with the current structure, we'll let the `filePickerBtn` directly handle file input creation for now.
  // And then call `processFile`.

  // Drag and Drop
  dropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropZone.style.borderColor = "#0056b3"; // Highlight effect
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.style.borderColor = "#007bff"; // Reset highlight
  });

  dropZone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropZone.style.borderColor = "#007bff";
    const files = event.dataTransfer.files;
    if (files.length > 0) {
      if (files[0].name.endsWith(".xls") || files[0].name.endsWith(".xlsx")) {
        processFile(files[0]); // Pass the file object directly
      } else {
        alert("Please upload an Excel file (.xls or .xlsx).");
      }
    }
  });

  // This is to ensure the file input created by `fileHandler.js` `handleFileUpload` can be used by `main.js`
  // We will make `handleFileUpload` in `fileHandler.js` attach the event listener to a callback passed to it
  // Or, more simply, we just trigger our own input.
  // For now, the `filePickerBtn` in `index.html` will use `processFile`.
  // And we need to ensure `handleFileUpload` in `fileHandler.js` isn't used directly for the button, or modify it.
  // Let's assume we adjust `handleFileUpload` in `fileHandler.js` not to create an input OR it calls a global callback.
  // Given the constraints, we'll use the `processFile` function directly for the button and drag/drop.
  // The `handleFileUpload` in `fileHandler.js` is now effectively bypassed by this local `processFile`.

  function setupMappingUI() {
    sheetTabsContainer.innerHTML = "";
    sheetContentContainer.innerHTML = "";
    currentMappings = {};
    sheetsConfig = {};

    const sortedSheets = Object.entries(uploadedFileData).sort(
      (a, b) => a[1].sheetIndex - b[1].sheetIndex
    );

    sortedSheets.forEach(([sheetName, sheetData], index) => {
      currentMappings[sheetName] = {};
      // Simple heuristic: map sheet name to fileType key or use a selection later
      let sheetTypeKey = sheetName.toLowerCase().replace(/s$/, ""); // e.g., "Deliveries" -> "delivery"
      if (sheetTypeKey.endsWith("y"))
        sheetTypeKey = sheetTypeKey.slice(0, -1) + "ies"; // e.g. delivery -> deliveries
      if (!fileTypes[sheetTypeKey] && fileTypes[sheetName.toLowerCase()])
        sheetTypeKey = sheetName.toLowerCase();

      // Fallback or allow user to select if no direct match
      // For now, we will try to find a match or use the first fileType as a placeholder if not found.
      const foundFileTypeKey = Object.keys(fileTypes).find((ftKey) =>
        sheetName.toLowerCase().includes(ftKey.slice(0, -1))
      ); // trucks -> truck
      const configKey = fileTypes[sheetTypeKey]
        ? sheetTypeKey
        : foundFileTypeKey ||
          Object.keys(fileTypes)[index % Object.keys(fileTypes).length];
      sheetsConfig[sheetName] = fileTypes[configKey];

      const tabButton = document.createElement("button");
      tabButton.classList.add("tab-btn");
      tabButton.textContent = sheetName;
      tabButton.dataset.sheetName = sheetName;
      tabButton.innerHTML = `${sheetName} <span class="checkmark" style="display:none;">✔</span>`;

      if (index === 0) {
        tabButton.classList.add("active");
        renderSheetContent(sheetName);
      }

      tabButton.addEventListener("click", () => {
        document
          .querySelectorAll(".tab-btn.active")
          .forEach((btn) => btn.classList.remove("active"));
        tabButton.classList.add("active");
        renderSheetContent(sheetName);
      });
      sheetTabsContainer.appendChild(tabButton);
    });
    checkAllMappings(); // Initial check
  }

  function renderSheetContent(sheetName) {
    sheetContentContainer.innerHTML = "";
    const sheetData = uploadedFileData[sheetName];
    const config = sheetsConfig[sheetName];

    if (!config) {
      sheetContentContainer.innerHTML = `<p>Configuration for "${sheetName}" not found. Please check config.js</p>`;
      return;
    }

    const columnsHeader = document.createElement("div");
    columnsHeader.classList.add("sheet-columns-header");
    columnsHeader.innerHTML =
      "<p><strong>Your Excel Columns (Drag to map):</strong></p>";
    sheetData.columns.forEach((col) => {
      const colDiv = document.createElement("div");
      colDiv.classList.add("column-draggable");
      colDiv.textContent = col;
      colDiv.draggable = true;
      colDiv.addEventListener("dragstart", (event) => {
        event.dataTransfer.setData("text/plain", col);
      });
      columnsHeader.appendChild(colDiv);
    });
    sheetContentContainer.appendChild(columnsHeader);

    const mappingsList = document.createElement("ul");
    mappingsList.classList.add("mappings-list");

    config.mappings.forEach((mapping) => {
      const listItem = document.createElement("li");
      listItem.classList.add("mapping-item");

      const label = document.createElement("span");
      label.classList.add("mapping-label");
      label.textContent = mapping.label;

      const dropTarget = document.createElement("div");
      dropTarget.classList.add("drop-target");
      dropTarget.dataset.mappingId = mapping.value;
      dropTarget.textContent = "Drop column here";

      if (currentMappings[sheetName][mapping.value]) {
        dropTarget.textContent = currentMappings[sheetName][mapping.value];
        dropTarget.classList.add("mapped-column");
      }

      dropTarget.addEventListener("dragover", (event) => {
        event.preventDefault();
        dropTarget.style.backgroundColor = "#cce5ff";
      });
      dropTarget.addEventListener("dragleave", (event) => {
        dropTarget.style.backgroundColor = "#ddeeff"; // Reset
      });
      dropTarget.addEventListener("drop", (event) => {
        event.preventDefault();
        dropTarget.style.backgroundColor = "#ddeeff";
        const excelColumn = event.dataTransfer.getData("text/plain");
        currentMappings[sheetName][mapping.value] = excelColumn;
        dropTarget.textContent = excelColumn;
        dropTarget.classList.add("mapped-column");
        checkSheetMappings(sheetName);
        checkAllMappings();
      });

      listItem.appendChild(label);
      listItem.appendChild(dropTarget);
      mappingsList.appendChild(listItem);
    });
    sheetContentContainer.appendChild(mappingsList);
  }

  function checkSheetMappings(sheetName) {
    const config = sheetsConfig[sheetName];
    if (!config) return;
    const allSheetMappingsDone = config.mappings.every(
      (m) => currentMappings[sheetName][m.value]
    );
    const tabButton = document.querySelector(
      `.tab-btn[data-sheet-name="${sheetName}"] .checkmark`
    );
    if (tabButton) {
      tabButton.style.display = allSheetMappingsDone ? "inline" : "none";
    }
  }

  function checkAllMappings() {
    const allDone = Object.keys(uploadedFileData).every((sheetName) => {
      const config = sheetsConfig[sheetName];
      if (!config) return false; // If a sheet has no config, it's not considered done.
      return config.mappings.every((m) => currentMappings[sheetName][m.value]);
    });

    if (allDone && Object.keys(uploadedFileData).length > 0) {
      calculateRouteBtn.classList.remove("hidden");
    } else {
      calculateRouteBtn.classList.add("hidden");
    }
  }

  calculateRouteBtn.addEventListener("click", async () => {
    calculateLoader.classList.remove("hidden");
    calculateRouteBtn.classList.add("hidden");

    if (!currentFileId) {
      alert("File ID is missing. Please try uploading the file again.");
      calculateLoader.classList.add("hidden");
      calculateRouteBtn.classList.remove("hidden");
      return;
    }

    const formattedMappings = Object.keys(currentMappings).map((sheetName) => {
      return {
        sheetName: sheetName,
        type: sheetsConfig[sheetName].id,
        maps: currentMappings[sheetName],
      };
    });

    console.log("Submitting mappings:", JSON.stringify(formattedMappings));
    console.log("Submitting with File ID:", currentFileId);

    try {
      // Pass the structured mappings and file_id
      const response = await handleFileSubmit(
        JSON.stringify(formattedMappings),
        currentFileId
      );

      calculateLoader.classList.add("hidden");

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.error || `API solve error: ${response.status}`
        );
      }

      // const resultData = await response.json(); // Process result data later
      console.log("VRP results received (raw response):", response);
      switchView(visualizeExportView, mappingsConfigView);
      visualizeLoader.classList.remove("hidden"); // Show loader for visualization part
      // TODO: Process and display VRP results. For now, just show loader.
      // setTimeout(() => visualizeLoader.classList.add("hidden"), 3000); // Simulate loading results
    } catch (error) {
      console.error("Error calculating route:", error);
      alert(`Error: ${error.message}`);
      calculateLoader.classList.add("hidden");
      calculateRouteBtn.classList.remove("hidden"); // Show button again on error
    }
  });

  mapDefaultsBtn.addEventListener("click", () => {
    if (!uploadedFileData) return;

    Object.keys(uploadedFileData).forEach((sheetName) => {
      const config = sheetsConfig[sheetName];
      const sheetData = uploadedFileData[sheetName];
      if (config && sheetData && sheetData.columns) {
        config.mappings.forEach((mapping, index) => {
          if (index < sheetData.columns.length) {
            // Map by index: config.mappings[0] -> sheetData.columns[0] (Column A)
            // config.mappings[1] -> sheetData.columns[1] (Column B), etc.
            currentMappings[sheetName][mapping.value] =
              sheetData.columns[index];
          }
        });
      }
    });

    // Re-render current view and update all checks
    const activeTab = document.querySelector(".tab-btn.active");
    if (activeTab) {
      renderSheetContent(activeTab.dataset.sheetName);
    }
    Object.keys(uploadedFileData).forEach((sheetName) => {
      checkSheetMappings(sheetName); // Update checkmarks for all tabs
    });
    checkAllMappings(); // Update visibility of Calculate Route button

    // Optionally, inform the user
    // alert("Default mappings applied where possible.");
  });

  // Initial setup if needed for fileInput from fileHandler.js
  // If handleFileUpload from fileHandler.js is intended to be the primary way to initiate upload,
  // it needs to be modified to callback or integrate with processFile.
  // For now, `filePickerBtn` and drag-drop directly call `processFile`.
});
