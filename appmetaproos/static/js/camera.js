// Get DOM elements
const video = document.getElementById('video');
const captureBtn = document.getElementById('captureBtn');
const buttonText = document.getElementById('buttonText');
const spinner = document.getElementById('spinner');
const message = document.getElementById('message');

// Check for camera access support
if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    // Access the camera
    navigator.mediaDevices.getUserMedia({ video: true })
        .then(function(stream) {
            // Set the video source to the camera stream
            video.srcObject = stream;
        })
        .catch(function(error) {
            // Handle camera access error
            console.error("Camera access error:", error);
            showMessage("Unable to access camera. Please check permissions and try again.", "danger");
            captureBtn.disabled = true;
        });
} else {
    // Browser doesn't support getUserMedia
    showMessage("Your browser doesn't support camera access. Please try a modern browser.", "danger");
    captureBtn.disabled = true;
}

// Capture selfie when button is clicked
captureBtn.addEventListener('click', function() {
    // Show loading state
    captureBtn.disabled = true;
    buttonText.textContent = "Processing...";
    spinner.classList.remove('d-none');
    message.classList.add('d-none');
    
    // Create a canvas element to capture the image
    const canvas = document.createElement('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    
    // Draw the current video frame to the canvas
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    
    // Convert canvas to blob
    canvas.toBlob(function(blob) {
        // Create FormData to send the image
        const formData = new FormData();
        formData.append('selfie', blob, 'selfie.jpg');
        
        // Send the selfie to the server
        fetch('/search', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Redirect to gallery with photo URLs
            if (data.photo_urls && data.photo_urls.length > 0) {
                // Create URL with photo parameters
                const url = new URL('/gallery', window.location.origin);
                data.photo_urls.forEach(photo => {
                    url.searchParams.append('photos', photo);
                });
                window.location.href = url.toString();
            } else {
                // No matching photos found
                showMessage("No matching photos found. Please try again with a clearer selfie.", "warning");
                resetButton();
            }
        })
        .catch(error => {
            console.error("Error:", error);
            showMessage("An error occurred while processing your selfie. Please try again.", "danger");
            resetButton();
        });
    }, 'image/jpeg', 0.9);
});

// Show message to user
function showMessage(text, type) {
    message.textContent = text;
    message.className = `mt-3 text-${type} d-block`;
}

// Reset button to initial state
function resetButton() {
    captureBtn.disabled = false;
    buttonText.textContent = "Take Selfie";
    spinner.classList.add('d-none');
}