import { handleFileUpload } from "./fileHandler.js";
import { fileTypes } from "./config.js";

function init() {
  const fileUploadFlex = document.getElementById("fileUploadFlex");

  Object.values(fileTypes).forEach((file) => {
    const label = file.id;

    const divId = label + "Div";
    const h3Id = label + "H3";
    const buttonId = label + "UploadButton";

    const newDiv = document.createElement("div");
    const newH3 = document.createElement("h3");
    const newButton = document.createElement("button");

    newDiv.setAttribute("id", divId);
    newDiv.classList.add("file-upload-card");

    newH3.setAttribute("id", h3Id);
    newButton.setAttribute("id", buttonId);

    fileUploadFlex.appendChild(newDiv);

    newDiv.appendChild(newH3);
    newDiv.appendChild(newButton);

    newButton.textContent = "Upload";
    newH3.textContent = label[0].toUpperCase() + label.slice(1) + " File";

    document
      .getElementById(buttonId)
      .addEventListener("click", (event) => handleFileUpload(event, label));
  });
}

init();
