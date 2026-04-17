const API_BASE_URL = "http://127.0.0.1:8203";

const chatBody = document.getElementById("chat-body");
const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const questionInputEl = document.getElementById("question-input");
const toggleButtonEl = document.getElementById("toggle-chat");

let loadingMessageEl = null;

function appendUserMessage(question) {
  const bubble = document.createElement("article");
  bubble.className =
    "ml-auto max-w-[90%] rounded-2xl rounded-br-sm bg-sky-600 px-3 py-2 text-sm text-white sm:max-w-[85%]";
  bubble.textContent = question;
  messagesEl.appendChild(bubble);
  scrollToBottom();
}

function appendAssistantMessage(answer, sources) {
  const wrapper = document.createElement("article");
  wrapper.className =
    "max-w-[90%] rounded-2xl rounded-tl-sm border border-slate-200 bg-white px-3 py-3 text-sm text-slate-800 sm:max-w-[85%]";

  const answerEl = document.createElement("p");
  answerEl.className = "whitespace-pre-wrap leading-relaxed text-slate-800";
  answerEl.textContent = answer || "No answer returned.";
  wrapper.appendChild(answerEl);

  const sourcesBlock = renderSources(sources);
  wrapper.appendChild(sourcesBlock);

  messagesEl.appendChild(wrapper);
  scrollToBottom();
}

function appendErrorMessage() {
  const errorEl = document.createElement("article");
  errorEl.className =
    "max-w-[90%] rounded-2xl rounded-tl-sm border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700 sm:max-w-[85%]";
  errorEl.textContent = "Something went wrong while preparing an answer. Please try again.";
  messagesEl.appendChild(errorEl);
  scrollToBottom();
}

function showLoadingMessage() {
  loadingMessageEl = document.createElement("article");
  loadingMessageEl.className =
    "max-w-[90%] rounded-2xl rounded-tl-sm border border-slate-200 bg-slate-100 px-3 py-2 text-sm text-slate-600 sm:max-w-[85%]";
  loadingMessageEl.innerHTML =
    'Preparing an answer <span class="loading-dots" aria-hidden="true"><span>.</span><span>.</span><span>.</span></span>';

  messagesEl.appendChild(loadingMessageEl);
  scrollToBottom();
}

function removeLoadingMessage() {
  if (loadingMessageEl && messagesEl.contains(loadingMessageEl)) {
    messagesEl.removeChild(loadingMessageEl);
  }
  loadingMessageEl = null;
}

function renderSources(sources) {
  const box = document.createElement("section");
  box.className = "mt-3 rounded-lg border border-slate-200 bg-slate-50 p-2.5";

  const heading = document.createElement("p");
  heading.className = "text-xs font-semibold uppercase tracking-wide text-slate-500";
  heading.textContent = "Sources";
  box.appendChild(heading);

  if (!Array.isArray(sources) || sources.length === 0) {
    const empty = document.createElement("p");
    empty.className = "mt-1 text-xs text-slate-500";
    empty.textContent = "No sources returned for this answer.";
    box.appendChild(empty);
    return box;
  }

  const list = document.createElement("ul");
  list.className = "mt-2 space-y-2";

  sources.forEach((source) => {
    const item = document.createElement("li");
    item.className = "rounded-md border border-slate-200 bg-white p-2";

    const link = document.createElement("a");
    link.href = source.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.className = "block break-words text-sm font-medium text-sky-700 underline hover:text-sky-600";
    link.textContent = source.title || source.url;

    const meta = document.createElement("p");
    meta.className = "mt-1 text-xs text-slate-500";
    const sourceType = source.source_type || "unknown";
    const section = source.section ? ` • section: ${source.section}` : "";
    meta.textContent = `type: ${sourceType}${section}`;

    item.appendChild(link);
    item.appendChild(meta);
    list.appendChild(item);
  });

  box.appendChild(list);
  return box;
}

function autoResizeInput() {
  questionInputEl.style.height = "auto";
  questionInputEl.style.height = `${Math.min(questionInputEl.scrollHeight, 160)}px`;
}

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function toggleChat() {
  const isHidden = chatBody.classList.toggle("hidden");
  toggleButtonEl.textContent = isHidden ? "Expand" : "Collapse";
  toggleButtonEl.setAttribute("aria-expanded", String(!isHidden));
}

async function askQuestion(question) {
  const response = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ question }),
  });

  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }

  return response.json();
}

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInputEl.value.trim();

  if (!question) {
    return;
  }

  appendUserMessage(question);
  questionInputEl.value = "";
  autoResizeInput();
  showLoadingMessage();

  try {
    const result = await askQuestion(question);
    removeLoadingMessage();
    appendAssistantMessage(result.answer, result.sources);
  } catch (error) {
    removeLoadingMessage();
    appendErrorMessage();
  }
});

questionInputEl.addEventListener("input", autoResizeInput);
questionInputEl.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    formEl.requestSubmit();
  }
});

toggleButtonEl.addEventListener("click", toggleChat);

autoResizeInput();
