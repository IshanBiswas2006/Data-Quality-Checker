document.addEventListener("DOMContentLoaded", () => {
  const dropZone = document.getElementById("dropZone");
  const fileInput = document.getElementById("fileInput");
  const uploadForm = document.getElementById("uploadForm");
  const uploadBtn = document.getElementById("uploadBtn");
  const selectedFileInfo = document.getElementById("selectedFileInfo");
  const fileNameDisplay = document.getElementById("fileNameDisplay");
  const fileSizeDisplay = document.getElementById("fileSizeDisplay");
  const sampleBtn = document.getElementById("loadSampleBtn");

  if (!dropZone || !fileInput) return;

  const MAX_SIZE_BYTES = 16 * 1024 * 1024; // 16 MB

  // Drag and drop events
  ["dragenter", "dragover"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.add("drag-over");
    });
  });

  ["dragleave", "drop"].forEach((eventName) => {
    dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.classList.remove("drag-over");
    });
  });

  dropZone.addEventListener("drop", (e) => {
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileSelected(files[0]);
    }
  });

  dropZone.addEventListener("click", () => {
    fileInput.click();
  });

  fileInput.addEventListener("change", () => {
    if (fileInput.files.length > 0) {
      handleFileSelected(fileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith(".csv")) {
      showToast("Only .csv files are supported. Please select a CSV file.", "error");
      fileInput.value = "";
      selectedFileInfo.style.display = "none";
      return;
    }

    if (file.size === 0) {
      showToast("Selected file is empty (0 bytes).", "error");
      fileInput.value = "";
      selectedFileInfo.style.display = "none";
      return;
    }

    if (file.size > MAX_SIZE_BYTES) {
      showToast("File size exceeds 16 MB limit. Please select a smaller CSV.", "error");
      fileInput.value = "";
      selectedFileInfo.style.display = "none";
      return;
    }

    // Update UI
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = formatBytes(file.size);
    selectedFileInfo.style.display = "flex";
    uploadBtn.disabled = false;
  }

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  }

  // Handle form submission with spinner
  if (uploadForm) {
    uploadForm.addEventListener("submit", () => {
      uploadBtn.disabled = true;
      uploadBtn.innerHTML = `<span class="spinner"></span> Processing CSV...`;
    });
  }

  // Load sample dataset
  if (sampleBtn) {
    sampleBtn.addEventListener("click", async (e) => {
      e.preventDefault();
      sampleBtn.disabled = true;
      sampleBtn.textContent = "Loading sample...";
      
      const sampleCsv = `TransactionID,CustomerName,Age,Email,Product,Amount,PurchaseDate
TX1001,John Doe,29,john@example.com,Wireless Headphones,129.99,2026-01-15
TX1002,Jane Smith,34,jane.smith@service.net,Smart Watch,199.50,2026-01-16
TX1003,Bob Johnson,,bob@corp.org,Mechanical Keyboard,89.00,2026-01-16
TX1004,Alice Brown,22,alice@domain,USB-C Hub,-15.00,2026-01-17
TX1005,Charlie Black,-5,charlie@email.com,4K Monitor,349.00,invalid-date
TX1001,John Doe,29,john@example.com,Wireless Headphones,129.99,2026-01-15
TX1006,Eve Wilson,41,eve@test.com,Noise Cancelling Earbuds,149.99,2026-01-18
TX1007,Frank Miller,58,frank@mail.org,,79.95,2026-01-19
TX1008,Grace Hopper,85,grace@navy.mil,Compiler Manual,45.00,1952-09-09
TX1008,Grace Hopper,85,grace@navy.mil,Compiler Manual,45.00,1952-09-09
TX1009,Hannah Abbott,19,hannah@hogwarts.edu,Herbology Kit,N/A,2026-01-20`;

      const blob = new Blob([sampleCsv], { type: "text/csv" });
      const file = new File([blob], "sample_ecommerce_data.csv", { type: "text/csv" });
      
      const dataTransfer = new DataTransfer();
      dataTransfer.items.add(file);
      fileInput.files = dataTransfer.files;
      handleFileSelected(file);
      
      sampleBtn.disabled = false;
      sampleBtn.textContent = "Loaded Sample Data";
    });
  }
});
