/**
 * MeetMind web app origin.
 * Change this when you deploy. The extension never calls the API and has no API keys.
 */
const WEB_APP_URL = "http://localhost:3010";

function openApp(query: string | null, autorun: boolean): void {
  const url = new URL(WEB_APP_URL);
  if (query) {
    url.searchParams.set("q", query);
    if (autorun) {
      url.searchParams.set("autorun", "1");
    }
  }
  void chrome.tabs.create({ url: url.toString() });
}

function init(): void {
  const form = document.querySelector("form");
  const input = document.querySelector<HTMLTextAreaElement>("#goal");
  const error = document.querySelector<HTMLElement>("[data-error]");
  const openButton = document.querySelector<HTMLButtonElement>("[data-open-app]");

  form?.addEventListener("submit", (event) => {
    event.preventDefault();
    const query = input?.value.trim() ?? "";
    if (query.length < 3) {
      if (error) {
        error.hidden = false;
        error.textContent = "Add a little more detail so MeetMind knows who you want to meet.";
      }
      input?.focus();
      return;
    }
    if (error) {
      error.hidden = true;
    }
    openApp(query, true);
  });

  openButton?.addEventListener("click", () => {
    const query = input?.value.trim() ?? "";
    openApp(query.length >= 3 ? query : null, false);
  });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", init);
} else {
  init();
}
