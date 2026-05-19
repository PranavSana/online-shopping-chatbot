function sendMessage() {
    const userInput = document.getElementById("userInput");
    const message = userInput.value.trim();

    if (message) {
        addMessage(message, "user");
        userInput.value = "";

        fetch("/get_response", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message }),
        })
        .then(res => res.json())
        .then(data => {
            addMessage(data.response, "bot", data.products);
        })
        .catch(error => {
            console.error("Error fetching bot response:", error);
            addMessage("Sorry, I'm having trouble connecting. Please try again later.", "bot");
        });
    }
}

function addMessage(text, sender, products = null) {
    const chatbox = document.getElementById("chatbox");

    const messageDiv = document.createElement("div");
    messageDiv.classList.add("message", sender === "user" ? "user-message" : "bot-message");

    const bubbleDiv = document.createElement("div");
    bubbleDiv.classList.add("bubble");

    if (sender === "bot") {
        bubbleDiv.innerHTML = `<strong>Shopping Assistant:</strong><br>${text.replace(/\n/g, "<br>")}`;
    } else {
        bubbleDiv.textContent = text;
    }

    messageDiv.appendChild(bubbleDiv);
    chatbox.appendChild(messageDiv);

    if (products && products.length > 0) {
        products.forEach(product => {
            const productCard = document.createElement("div");
            productCard.classList.add("product-card");
            productCard.style.margin = "10px 0";
            productCard.style.width = "auto";

            let sizeDropdownHTML = '';
            const requiresSize = ['shirts', 'tshirts', 'pants', 'shoes'].includes(product.category);

            if (requiresSize) {
                let options = '<option value="">Select Size</option>';
                if (['shirts', 'tshirts'].includes(product.category)) {
                    options += '<option value="S">S</option><option value="M">M</option><option value="L">L</option><option value="XL">XL</option><option value="XXL">XXL</option>';
                } else if (product.category === 'pants') {
                    options += '<option value="30">30</option><option value="32">32</option><option value="34">34</option><option value="36">36</option><option value="38">38</option>';
                } else if (product.category === 'shoes') {
                    options += '<option value="6">6</option><option value="7">7</option><option value="8">8</option><option value="9">9</option><option value="10">10</option><option value="11">11</option>';
                }

                sizeDropdownHTML = `
                    <div class="size-dropdown">
                        <select id="chatbot-size-select-${product.id}">${options}</select>
                    </div>
                `;
            }

            productCard.innerHTML = `
                <img src="${product.image_url}" alt="${product.name}" />
                <h3>${product.name}</h3>
                <p class="product-price">₹${parseFloat(product.price).toFixed(2)}</p>
                ${sizeDropdownHTML}
                <button class="btn-add-to-cart" onclick="addToCartFromChat(${product.id}, '${product.category}')">Add to Cart</button>
            `;
            chatbox.appendChild(productCard);
        });
    }

    chatbox.scrollTop = chatbox.scrollHeight;
}

// --- NEW addToCartFromChat function ---
// This function correctly handles getting the size from the chatbot's dropdown
function addToCartFromChat(productId, category) {
    let size = null;
    const requiresSize = ['shirts', 'tshirts', 'pants', 'shoes'].includes(category);
    
    if (requiresSize) {
        const sizeSelect = document.getElementById(`chatbot-size-select-${productId}`);
        if (!sizeSelect || sizeSelect.value === '') {
            showNotification("Please choose a size.", true);
            return;
        }
        size = sizeSelect.value;
    }

    // Now call the main addToCart function, passing the size explicitly
    addToCart(productId, category, true, size);
}

document.getElementById("userInput").addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});