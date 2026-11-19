
const $ = (id) => document.getElementById(id);

let activeId = null;
let busy = false;
let sessions = [];

const apiKeyInput = $("api-key");
const messageInput = $("message");
const sendButton = $("send");
const sendLabel = $("send-label");
const sessionList = $("session-list");
const messagesContainer = $("messages");
const usageDisplay = $("usage");

// Restore the locally saved API key.
apiKeyInput.value = localStorage.getItem("chat_api_key") || "";

function headers() {
    return {
        "X-API-Key": apiKeyInput.value.trim()
    };
}

function setNotice(message = "", type = "") {
    const notice = $("notice");
    notice.textContent = message;
    notice.className = `notice ${type}`;
}

function setBusy(value) {
    busy = value;
    sendButton.disabled = value;
    $("new-session").disabled = value;
    sendLabel.textContent = value ? "Thinking..." : "Send";
}

function formatCost(value) {
    return Number(value || 0).toFixed(6);
}

function updateUsage(session) {
    if (!session) {
        usageDisplay.textContent = "No usage yet";
        return;
    }

    const totalTokens =
        Number(session.total_prompt_tokens || 0) +
        Number(session.total_completion_tokens || 0);

    usageDisplay.textContent =
        `${totalTokens.toLocaleString()} tokens · $${formatCost(session.total_cost_usd)}`;
}

function showWelcome(title = "What would you like to explore?") {
    messagesContainer.replaceChildren();

    const welcome = document.createElement("div");
    welcome.className = "welcome";

    const icon = document.createElement("div");
    icon.className = "welcome-icon";
    icon.textContent = "✦";

    const heading = document.createElement("h1");
    heading.textContent = title;

    const description = document.createElement("p");
    description.textContent = "Start a conversation with your AI assistant.";

    welcome.append(icon, heading, description);
    messagesContainer.append(welcome);
}

function scrollToBottom() {
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addMessage(role, content = "") {
    messagesContainer.querySelector(".welcome")?.remove();

    const row = document.createElement("div");
    row.className = `message ${role}`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = role === "user" ? "You" : "✦";

    const body = document.createElement("div");
    body.className = "message-content";
    body.textContent = content;

    row.append(avatar, body);
    messagesContainer.append(row);

    scrollToBottom();

    return body;
}

async function readError(response) {
    try {
        const data = await response.json();
        return data.detail || data.message || `Request failed (${response.status})`;
    } catch {
        return `Request failed (${response.status})`;
    }
}

function requireApiKey() {
    if (!apiKeyInput.value.trim()) {
        setNotice("Enter your application API key in the sidebar.", "error");
        apiKeyInput.focus();
        return false;
    }

    return true;
}

// Load sessions and update the sidebar.
async function loadSessions() {
    if (!requireApiKey()) {
        return;
    }

    try {
        const response = await fetch("/sessions", {
            headers: headers()
        });

        if (!response.ok) {
            throw new Error(await readError(response));
        }

        sessions = await response.json();

        renderSessions();

        const activeSession = sessions.find(
            (session) => session.id === activeId
        );

        if (activeSession) {
            updateUsage(activeSession);
        } else if (!activeId) {
            updateUsage(null);
        }

        return sessions;
    } catch (error) {
        setNotice(error.message, "error");
        throw error;
    }
}

function renderSessions() {
    sessionList.replaceChildren();

    if (sessions.length === 0) {
        const empty = document.createElement("p");
        empty.className = "sidebar-empty";
        empty.textContent = "No conversations yet. Start a new chat!";
        sessionList.append(empty);
        return;
    }

    sessions.forEach((session) => {
        const item = document.createElement("div");
        item.className = "session-item";

        if (session.id === activeId) {
            item.classList.add("active");
        }

        const openButton = document.createElement("button");
        openButton.className = "session-open";
        openButton.type = "button";
        openButton.textContent = session.title || "New conversation";
        openButton.title = session.title || "New conversation";
        openButton.addEventListener("click", () => {
            openSession(session.id);
        });

        const deleteButton = document.createElement("button");
        deleteButton.className = "delete-session";
        deleteButton.type = "button";
        deleteButton.textContent = "×";
        deleteButton.title = "Delete conversation";
        deleteButton.setAttribute("aria-label", "Delete conversation");

        deleteButton.addEventListener("click", (event) => {
            event.stopPropagation();
            deleteSession(session.id);
        });

        item.append(openButton, deleteButton);
        sessionList.append(item);
    });
}

// Create a new conversation.
async function createSession() {
    if (!requireApiKey()) {
        throw new Error("API key is required.");
    }

    const response = await fetch("/sessions", {
        method: "POST",
        headers: {
            ...headers(),
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            title: "New conversation"
        })
    });

    if (!response.ok) {
        throw new Error(await readError(response));
    }

    const session = await response.json();

    activeId = session.id;
    showWelcome("Start a new conversation");
    updateUsage(session);
    setNotice("");

    await loadSessions();

    return session;
}

// Open an existing conversation.
async function openSession(id) {
    if (busy) {
        return;
    }

    if (!requireApiKey()) {
        return;
    }

    try {
        setNotice("Loading conversation...");

        const response = await fetch(
            `/sessions/${id}/messages`,
            { headers: headers() }
        );

        if (!response.ok) {
            throw new Error(await readError(response));
        }

        const history = await response.json();

        activeId = id;

        if (history.length === 0) {
            showWelcome("Continue your conversation");
        } else {
            messagesContainer.replaceChildren();

            history.forEach((message) => {
                addMessage(message.role, message.content);
            });
        }

        await loadSessions();

        setNotice("");
        renderSessions();
    } catch (error) {
        setNotice(error.message, "error");
    }
}

// Delete a conversation.
async function deleteSession(id) {
    if (busy) {
        return;
    }

    const confirmed = window.confirm(
        "Are you sure you want to delete this conversation? This cannot be undone."
    );

    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`/sessions/${id}`, {
            method: "DELETE",
            headers: headers()
        });

        if (!response.ok) {
            throw new Error(await readError(response));
        }

        if (activeId === id) {
            activeId = null;
            showWelcome();
            updateUsage(null);
        }

        await loadSessions();

        setNotice("Conversation deleted.", "success");
    } catch (error) {
        setNotice(error.message, "error");
    }
}

// Process server-sent events from the streaming response.
async function processStream(response, output) {
    if (!response.body) {
        throw new Error("Your browser does not support response streaming.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    let buffer = "";
    let streamError = null;
    let receivedDone = false;

    function processEvent(block) {
        const dataLines = block
            .split(/\r?\n/)
            .filter((line) => line.startsWith("data:"))
            .map((line) => line.slice(5).trimStart());

        if (dataLines.length === 0) {
            return;
        }

        const data = JSON.parse(dataLines.join("\n"));

        if (data.type === "token") {
            output.textContent += data.content || "";
            output.classList.add("streaming");
            scrollToBottom();
        }

        if (data.type === "done") {
            receivedDone = true;
            output.classList.remove("streaming");
        }

        if (data.type === "error") {
            streamError = data.message || "The AI service returned an error.";
            output.classList.remove("streaming");
        }
    }

    try {
        while (true) {
            const { value, done } = await reader.read();

            if (done) {
                break;
            }

            buffer += decoder.decode(value, { stream: true });

            const blocks = buffer.split(/\r?\n\r?\n/);
            buffer = blocks.pop() || "";

            for (const block of blocks) {
                if (block.trim()) {
                    processEvent(block);
                }
            }

            if (streamError) {
                break;
            }
        }

        buffer += decoder.decode();

        // Process a final event if the stream ends without a blank line.
        if (buffer.trim() && !streamError) {
            processEvent(buffer);
        }

        if (streamError) {
            throw new Error(streamError);
        }

        if (!receivedDone) {
            throw new Error(
                "The AI response ended unexpectedly. Please check your conversation."
            );
        }

        output.classList.remove("streaming");
    } finally {
        reader.releaseLock();
    }
}

// Send a message and receive the AI response.
async function sendMessage(event) {
    event.preventDefault();

    const message = messageInput.value.trim();

    if (!message || busy) {
        return;
    }

    if (!requireApiKey()) {
        return;
    }

    setBusy(true);
    setNotice("");

    try {
        // Automatically create a conversation if none is selected.
        if (!activeId) {
            await createSession();
        }

        const sessionId = activeId;

        messageInput.value = "";
        addMessage("user", message);

        const output = addMessage("assistant", "");
        output.classList.add("streaming");

        const response = await fetch(
            `/sessions/${sessionId}/chat`,
            {
                method: "POST",
                headers: {
                    ...headers(),
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ message })
            }
        );

        if (response.status === 429) {
            const retryAfter = response.headers.get("Retry-After");
            const detail = await readError(response);

            throw new Error(
                `${detail}. Retry after ${retryAfter || "a short time"} seconds.`
            );
        }

        if (!response.ok) {
            throw new Error(await readError(response));
        }

        await processStream(response, output);

        // Reload server-side usage totals and updated session title.
        await loadSessions();

        setNotice("");
    } catch (error) {
        setNotice(error.message, "error");
    } finally {
        setBusy(false);
        messageInput.focus();
        renderSessions();
    }
}

// Save the API key in this browser.
$("save-key").addEventListener("click", async () => {
    const key = apiKeyInput.value.trim();

    if (!key) {
        localStorage.removeItem("chat_api_key");
        setNotice("Enter your API key first.", "error");
        return;
    }

    localStorage.setItem("chat_api_key", key);
    activeId = null;
    showWelcome();
    updateUsage(null);

    try {
        await loadSessions();
        setNotice("API key saved and conversations loaded.", "success");
    } catch {
        // loadSessions already displays the error.
    }
});

// Create a new session.
$("new-session").addEventListener("click", async () => {
    if (busy) {
        return;
    }

    try {
        await createSession();
        setNotice("New conversation created.", "success");
    } catch (error) {
        setNotice(error.message, "error");
    }
});

// Refresh the conversation list.
$("refresh-sessions").addEventListener("click", async () => {
    try {
        await loadSessions();
        setNotice("Conversations refreshed.", "success");
    } catch {
        // Error is displayed by loadSessions.
    }
});

// Handle chat submission.
$("chat-form").addEventListener("submit", sendMessage);

// Enter sends; Shift + Enter creates a new line.
messageInput.addEventListener("keydown", (event) => {
    if (
        event.key === "Enter" &&
        !event.shiftKey &&
        !event.isComposing
    ) {
        event.preventDefault();
        $("chat-form").requestSubmit();
    }
});

// Initial application loading.
async function initializeApp() {
    if (apiKeyInput.value.trim()) {
        try {
            await loadSessions();
        } catch {
            // Authentication or connection error is displayed in the notice.
        }
    }
}

initializeApp();
