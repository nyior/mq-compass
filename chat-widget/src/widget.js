(function () {
  function mount(options) {
    const settings = {
      apiBaseUrl: options.apiBaseUrl || "http://127.0.0.1:8203",
      productName: options.productName || "your product",
    };

    const host = document.createElement("div");
    host.innerHTML = `
      <div class="fixed bottom-5 right-5 z-50 flex flex-col items-end gap-3">
        <section id="mq-compass-panel" class="hidden w-[min(24rem,calc(100vw-2rem))] overflow-hidden rounded-3xl border border-slate-700 bg-slate-900 shadow-2xl shadow-cyan-950/40">
          <header class="bg-gradient-to-r from-cyan-500 to-teal-400 px-5 py-4 text-slate-950">
            <p class="text-xs font-semibold uppercase tracking-[0.25em]">MQ Compass</p>
            <h2 class="mt-1 text-lg font-semibold">Ask about ${settings.productName}</h2>
          </header>
          <div id="mq-compass-messages" class="flex h-80 flex-col gap-3 overflow-y-auto px-4 py-4 text-sm">
            <div class="max-w-[85%] rounded-2xl rounded-tl-sm bg-slate-800 px-4 py-3 text-slate-100">
              Ask how LavinMQ works or what to check when something breaks.
            </div>
          </div>
          <form id="mq-compass-form" class="border-t border-slate-800 p-3">
            <label class="sr-only" for="mq-compass-input">Ask a question</label>
            <div class="flex items-end gap-2">
              <textarea id="mq-compass-input" rows="2" class="min-h-12 flex-1 resize-none rounded-2xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-slate-100 outline-none ring-0 placeholder:text-slate-500" placeholder="Why are messages backing up?"></textarea>
              <button class="rounded-2xl bg-cyan-400 px-4 py-3 text-sm font-semibold text-slate-950 transition hover:bg-cyan-300" type="submit">Send</button>
            </div>
          </form>
        </section>
        <button id="mq-compass-toggle" class="rounded-full bg-cyan-400 px-5 py-3 text-sm font-semibold text-slate-950 shadow-lg shadow-cyan-950/50 transition hover:-translate-y-0.5 hover:bg-cyan-300" type="button">
          Chat with MQ Compass
        </button>
      </div>
    `;

    document.body.appendChild(host);

    const panel = host.querySelector("#mq-compass-panel");
    const toggle = host.querySelector("#mq-compass-toggle");
    const form = host.querySelector("#mq-compass-form");
    const input = host.querySelector("#mq-compass-input");
    const messages = host.querySelector("#mq-compass-messages");

    toggle.addEventListener("click", function () {
      panel.classList.toggle("hidden");
    });

    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      const question = input.value.trim();
      if (!question) {
        return;
      }

      appendMessage(messages, question, "user");
      input.value = "";

      try {
        const response = await fetch(`${settings.apiBaseUrl}/ask`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        const data = await response.json();
        appendMessage(messages, data.answer, "assistant");
      } catch (error) {
        appendMessage(messages, "The assistant is unavailable. Check the retrieval API and try again.", "assistant");
      }
    });
  }

  function appendMessage(target, text, role) {
    const bubble = document.createElement("div");
    const baseClass = "max-w-[85%] rounded-2xl px-4 py-3";
    bubble.className =
      role === "user"
        ? `${baseClass} self-end rounded-br-sm bg-cyan-400 text-slate-950`
        : `${baseClass} rounded-tl-sm bg-slate-800 text-slate-100`;
    bubble.textContent = text;
    target.appendChild(bubble);
    target.scrollTop = target.scrollHeight;
  }

  window.MQCompassWidget = { mount };
})();
