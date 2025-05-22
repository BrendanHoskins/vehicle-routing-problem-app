import { handleFileUpload, handleFileSubmit } from "./fileHandler.js";

function init() {
  const fileUploadFlex = document.getElementById("fileUploadFlex");

  const divId = "uploadFileDiv";
  const h3Id = "UploadFileH3";
  const buttonId = "UploadFileButton";
  const submitButtonId = "submitButton";

  const newDiv = document.createElement("div");
  const newH3 = document.createElement("h3");
  const newButton = document.createElement("button");
  const submitButton = document.createElement("button");

  newDiv.setAttribute("id", divId);
  newDiv.classList.add("file-upload-card");

  newH3.setAttribute("id", h3Id);
  newButton.setAttribute("id", buttonId);
  submitButton.setAttribute("id", submitButtonId);

  fileUploadFlex.appendChild(newDiv);

  newDiv.appendChild(newH3);
  newDiv.appendChild(newButton);
  newDiv.appendChild(submitButton);

  newButton.textContent = "Upload Excel Workbook";
  submitButton.innerText = "Calculate Route";

  document
    .getElementById(buttonId)
    .addEventListener("click", (event) => handleFileUpload(event, label));

  document
    .getElementById("submitButton")
    .addEventListener("click", async () => {
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
}

init();
