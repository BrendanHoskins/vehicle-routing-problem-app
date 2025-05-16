import { fileTypes } from "./config.js";

let currentFormData = null;

function handleFileUpload(event, fileType) {
  const fileInput = document.createElement("input");
  fileInput.setAttribute("id", "fileInput");
  fileInput.type = "file";
  fileInput.accept = ".csv";
  fileInput.addEventListener("change", (event) => {
    console.log("FILE:", event.target.files[0]);
    const newFormData = {};
    const currentFormData = new FormData();
    
    newFormData.append('content', event.target.files[0]);
    newFormData.append()
    currentFormData.append(fileType, newFormData);

  });
  fileInput.click();
}

async function handleFileSubmit () {
  if (currentFormData.length === fileTypes.length) {
    const response = await fetch("/api/vrp/solve", {
      method : "POST",
      body : currentFormData
    });

    return response;
  }
}

export { handleFileUpload, handleFileSubmit };
