function handleFileUpload() {
  const fileInput = document.createElement("input");
  fileInput.setAttribute("id", "fileInput");
  fileInput.type = "file";
  fileInput.accept = ".xls, .xlsx";
  fileInput.addEventListener("change", async (event) => {
    const file = event.target.files[0];

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      if (response.status !== 200) {
        throw new Error(`/api/upload error: ${response.body.error}`);
      }

      const fileData = await response.json();
      console.log('fileData:', fileData);
    } catch (error) {
      console.error("Error:", error);
      alert("Error in handleFileUpload: ", error.message);
    }
  });
  fileInput.click();
}

async function handleFileSubmit(mappings) {
  const reqData = new FormData();
  reqData.append("mappings", mappings);
  const response = await fetch("/api/solve", {
    method: "POST",
    body: reqData,
  });

  return response;

}

export { handleFileUpload, handleFileSubmit };
