async function handleFileUpload(file) {
  if (!file) {
    return new Promise((resolve, reject) => {
      const fileInput = document.createElement("input");
      fileInput.setAttribute("id", "fileInputHandler");
      fileInput.type = "file";
      fileInput.accept = ".xls, .xlsx";
      fileInput.addEventListener("change", async (event) => {
        const selectedFile = event.target.files[0];
        if (selectedFile) {
          try {
            const formData = new FormData();
            formData.append("file", selectedFile);
            const response = await fetch("/api/upload", {
              method: "POST",
              body: formData,
            });
            if (!response.ok) {
              const errorBody = await response
                .json()
                .catch(() => ({ error: "Unknown upload error" }));
              throw new Error(
                errorBody.error ||
                  `/api/upload error status: ${response.status}`
              );
            }
            resolve(await response.json());
          } catch (error) {
            console.error("Error in handleFileUpload (internal input):", error);
            reject(error);
          }
        }
      });
      fileInput.click();
    });
  }

  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorBody = await response
        .json()
        .catch(() => ({ error: "Unknown upload error" }));
      throw new Error(
        errorBody.error || `/api/upload error status: ${response.status}`
      );
    }
    return await response.json();
  } catch (error) {
    console.error("Error in handleFileUpload (file provided):", error);
    throw error;
  }
}

async function handleFileSubmit(mappings, fileId) {
  const reqData = new FormData();
  reqData.append("mappings", mappings);
  reqData.append("file_id", fileId);
  const response = await fetch("/api/solve", {
    method: "POST",
    body: reqData,
  });

  return response;
}

export { handleFileUpload, handleFileSubmit };
