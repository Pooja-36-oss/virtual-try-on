// Handle image preview when user selects a file
function previewImage(input, previewElementId) {
    const previewContainer = document.getElementById(previewElementId);
    let imgElement = previewContainer.querySelector('img');
    const placeholder = previewContainer.querySelector('.placeholder-text');

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function (e) {
            // If image element doesn't exist yet, create it
            if (!imgElement) {
                imgElement = document.createElement('img');
                previewContainer.appendChild(imgElement);
            }
            imgElement.src = e.target.result;
            imgElement.style.display = 'block';
            if (placeholder) {
                placeholder.style.display = 'none';
            }
        }

        reader.readAsDataURL(input.files[0]);
    }
}

// Handle form submission
document.getElementById('tryon-form').addEventListener('submit', async function (e) {
    e.preventDefault();

    // UI Elements
    const btn = document.getElementById('generate-btn');
    const btnText = btn.querySelector('.btn-text');
    const spinner = document.getElementById('spinner');
    const resultContainer = document.getElementById('result-container');
    const waitingText = document.getElementById('waiting-text');
    let resultImage = document.getElementById('result-image');
    const downloadBtn = document.getElementById('download-btn');

    // Check if files are selected
    const userImage = document.getElementById('user_image').files[0];
    const garmentImage = document.getElementById('garment_image').files[0];

    if (!userImage || !garmentImage) {
        alert("Please upload both a person image and a garment image.");
        return;
    }

    // Set Loading State
    btn.disabled = true;
    downloadBtn.disabled = true; // Disable save button during processing
    btnText.textContent = "Processing...";
    spinner.style.display = "block";
    resultImage.style.display = "none";
    waitingText.textContent = "Synthesizing Try-On... This may take up to 20 seconds.";
    waitingText.style.display = "block";

    // Prepare FormData
    const formData = new FormData(this);

    try {
        // Assume API is hosted on same domain if running via FastAPI static mount
        // Or change to full URL if running separately: 'http://127.0.0.1:8000/api/v1/try-on'
        const apiUrl = window.location.origin + '/api/v1/try-on';

        const response = await fetch(apiUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'accept': 'application/json'
            }
        });

        const data = await response.json();

        if (response.ok) {
            // Success
            waitingText.style.display = "none";

            // Depending on the API result, result_image_url might be a full URL, or an absolute path.
            // Hugging Face spaces return a local path inside `/tmp/gradio/...` or an HTTP URL.
            // Ideally, the backend would host it or upload it to S3, but we use the returned URL directly.
            // If it returns a local path, the browser cannot read it unless backend exposes it. 
            // FastAPI file endpoint or direct Gradio file URL must be used. Let's assume URL.

            // Note: IF the URL is a local disk path, we can't display it directly. 
            // In a real prod environment, backend sends a route `/api/v1/image/{id}`. 
            // For now, if we receive an HTTP URL we display it.

            let imageUrl = data.result_image_url;

            // Note: the API now returns a relative path like /api/v1/results/...
            resultImage.src = imageUrl;
            resultImage.style.display = "block";

            // Enable download button
            const downloadBtn = document.getElementById('download-btn');
            downloadBtn.disabled = false;
            downloadBtn.onclick = () => downloadImage(imageUrl);

            // Scroll to bottom
            document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
        } else {
            // Error from API
            throw new Error(data.detail || "Server returned an error");
        }
    } catch (error) {
        console.error("Error:", error);

        let errorMessage = error.message;
        if (errorMessage.toLowerCase().includes("quota") || errorMessage.toLowerCase().includes("rate limit")) {
            errorMessage = "Daily Hugging Face Quota Reached. Please try again tomorrow or upgrade your HF account for more ZeroGPU access.";
        }

        waitingText.textContent = "Error: " + errorMessage;
        waitingText.style.color = "#ef4444";
    } finally {
        // Reset Loading State
        btn.disabled = false;
        btnText.textContent = "Generate Try-On";
        spinner.style.display = "none";
    }
});

// Function to download the generated image
async function downloadImage(url) {
    const downloadBtn = document.getElementById('download-btn');
    const originalContent = downloadBtn.innerHTML;

    try {
        downloadBtn.innerHTML = `
            <div class="loader-spinner" style="width: 16px; height: 16px; margin: 0;"></div>
            <span>Saving...</span>
        `;
        downloadBtn.disabled = true;

        const response = await fetch(url);
        const blob = await response.blob();
        const blobUrl = window.URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = blobUrl;
        link.download = `viton_result_${Date.now()}.png`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        // Clean up blob URL
        window.URL.revokeObjectURL(blobUrl);

        // Visual feedback for success
        downloadBtn.innerHTML = `
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6L9 17l-5-5"></path></svg>
            <span>Saved!</span>
        `;
        setTimeout(() => {
            downloadBtn.innerHTML = originalContent;
            downloadBtn.disabled = false;
        }, 2000);

    } catch (error) {
        console.error("Download failed:", error);
        alert("Failed to download image. Try right-clicking it and selecting 'Save Image As'.");
        downloadBtn.innerHTML = originalContent;
        downloadBtn.disabled = false;
    }
}
