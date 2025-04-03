// static/exp.js

// Function to show a modal
function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "flex";
    } else {
        console.error(`Modal with ID "${modalId}" not found.`);
    }
}

// Function to close a modal
function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.style.display = "none";
    } else {
        console.error(`Modal with ID "${modalId}" not found.`);
    }
}

// Fetch and display features from the backend
async function loadFeatures() {
    try {
        const response = await fetch("http://127.0.0.1:8000/api/features");
        if (!response.ok) {
            throw new Error("Failed to fetch features");
        }
        const features = await response.json();
        const container = document.getElementById("features-container");

        features.forEach((feature) => {
            const box = document.createElement("div");
            box.className = "box";
            box.innerHTML = `
                <h2>${feature.title}</h2>
                <p>${feature.description}</p>
                <button class="btn" onclick="viewFeature(${feature.id})">View Details</button>
            `;
            container.appendChild(box);
        });
    } catch (error) {
        console.error("Error loading features:", error);
    }
}

// Fetch and display details of a specific feature
async function viewFeature(featureId) {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/features/${featureId}`);
        if (!response.ok) {
            throw new Error("Failed to fetch feature details");
        }
        const feature = await response.json();
        alert(`Feature: ${feature.title}\nDescription: ${feature.description}`);
    } catch (error) {
        console.error("Error fetching feature details:", error);
    }
}

// Handle newsletter subscription
async function subscribeNewsletter() {
    const email = prompt("Enter your email to subscribe:");
    if (!email) {
        alert("Subscription canceled.");
        return;
    }

    try {
        const response = await fetch("http://127.0.0.1:8000/api/newsletter", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email }),
        });

        if (response.ok) {
            const data = await response.json();
            alert(data.message);
        } else {
            const error = await response.json();
            alert(`Error: ${error.detail[0].msg}`);
        }
    } catch (error) {
        console.error("Error subscribing to newsletter:", error);
        alert("An error occurred while subscribing to the newsletter.");
    }
}

// Load features on page load
document.addEventListener("DOMContentLoaded", loadFeatures);