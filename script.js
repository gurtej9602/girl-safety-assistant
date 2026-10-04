const input = document.getElementById("userInput");
const sendButton = document.getElementById("sendButton");
const chatBox = document.querySelector(".chat-box");

const conversation = [];

sendButton.addEventListener("click", sendMessage);
input.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendMessage();
});

async function sendMessage() {
    const message = input.value.trim();
    if (!message) return;

    appendMessage(message, "user-message");
    conversation.push({ role: "user", text: message });
    input.value = "";
    sendButton.disabled = true;

    try {
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                message,
                history: conversation.slice(-20)
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Gemini request failed");
        }

        appendMessage(data.reply, "bot-message");
        conversation.push({ role: "model", text: data.reply });
    } catch (error) {
        console.error(error);
        appendMessage(
            "I couldn't connect to Gemini. Please check the developer API key and make sure the server is running.",
            "bot-message"
        );
        conversation.pop();
    } finally {
        sendButton.disabled = false;
        input.focus();
    }
}

function appendMessage(text, cls) {
    const el = document.createElement("div");
    el.className = cls;
    el.textContent = text;
    el.style.marginBottom = "10px";

    if (cls === "user-message") {
        el.style.background = "#8e3a6b";
        el.style.color = "white";
        el.style.padding = "12px 15px";
        el.style.borderRadius = "12px";
        el.style.width = "fit-content";
        el.style.maxWidth = "80%";
        el.style.marginLeft = "auto";
    }

    chatBox.appendChild(el);
    chatBox.scrollTop = chatBox.scrollHeight;
}
