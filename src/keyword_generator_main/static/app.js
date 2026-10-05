/**
 * Event Keyword & Hashtag Search System - Frontend Application
 *
 * Implements:
 * 1. Form validation for Event, Location, and Description.
 * 2. POST /generate API call to trigger Wigolo search + deterministic Python processing.
 * 3. Comma-separated display: Hashtags first, Keywords second.
 * 4. Read-only view by default.
 * 5. Edit mode toggle (✎ -> ✓) allowing inline edit, add, and remove.
 * 6. "Create Event" flow to reset UI and call POST /create-event (Wigolo cache clear).
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  const state = {
    hashtags: [],
    keywords: [],
    sources: [],
    isEditMode: false,
    isLoading: false,
  };

  // DOM Elements
  const eventInput = document.getElementById("event-input");
  const locationInput = document.getElementById("location-input");
  const descriptionInput = document.getElementById("description-input");
  const includeSocialCheckbox = document.getElementById("include-social-checkbox");

  const sourcesSection = document.getElementById("sources-section");
  const sourcesList = document.getElementById("sources-list");

  const generateBtn = document.getElementById("generate-btn");
  const generateBtnText = document.getElementById("generate-btn-text");
  const generateSpinner = document.getElementById("generate-spinner");
  const enginesDisplay = document.getElementById("engines-display");

  const editToggleBtn = document.getElementById("edit-toggle-btn");
  const editIcon = document.getElementById("edit-icon");

  const createEventBtn = document.getElementById("create-event-btn");
  const statusBanner = document.getElementById("status-banner");

  // Read-only view elements
  const readOnlyView = document.getElementById("read-only-view");
  const readonlyHashtags = document.getElementById("readonly-hashtags");
  const readonlyKeywords = document.getElementById("readonly-keywords");

  // Edit view elements
  const editView = document.getElementById("edit-view");
  const editableHashtagsContainer = document.getElementById("editable-hashtags-container");
  const editableKeywordsContainer = document.getElementById("editable-keywords-container");

  const newHashtagInput = document.getElementById("new-hashtag-input");
  const addHashtagBtn = document.getElementById("add-hashtag-btn");

  const newKeywordInput = document.getElementById("new-keyword-input");
  const addKeywordBtn = document.getElementById("add-keyword-btn");

  // --- Helper Functions ---

  function showBanner(message, type = "info", autoHideMs = 6000) {
    statusBanner.className = `status-banner ${type}`;
    statusBanner.textContent = message;
    statusBanner.classList.remove("hidden");

    if (autoHideMs > 0) {
      setTimeout(() => {
        // Only hide if the message hasn't changed
        if (statusBanner.textContent === message) {
          statusBanner.classList.add("hidden");
        }
      }, autoHideMs);
    }
  }

  function hideBanner() {
    statusBanner.classList.add("hidden");
  }

  function setLoading(loading, initialText = "") {
    state.isLoading = loading;
    generateBtn.disabled = loading;
    createEventBtn.disabled = loading;
    if (loading) {
      generateSpinner.classList.remove("hidden");
      if (initialText) {
        generateBtnText.textContent = initialText;
        if (enginesDisplay) {
          enginesDisplay.textContent = initialText;
          enginesDisplay.className = "engines-display active";
          enginesDisplay.classList.remove("hidden");
        }
      }
    } else {
      generateSpinner.classList.add("hidden");
      generateBtnText.textContent = "Generate";
    }
  }

  // --- Rendering Functions ---

  function renderReadOnlyView() {
    // 1. Render Hashtags FIRST
    if (state.hashtags.length > 0) {
      readonlyHashtags.textContent = state.hashtags.join(", ");
      readonlyHashtags.classList.remove("empty-placeholder");
    } else {
      readonlyHashtags.textContent = "No hashtags generated yet. Click \"Generate\" to search and extract.";
      readonlyHashtags.classList.add("empty-placeholder");
    }

    // 2. Render Keywords SECOND
    if (state.keywords.length > 0) {
      readonlyKeywords.textContent = state.keywords.join(", ");
      readonlyKeywords.classList.remove("empty-placeholder");
    } else {
      readonlyKeywords.textContent = "No keywords generated yet. Click \"Generate\" to search and extract.";
      readonlyKeywords.classList.add("empty-placeholder");
    }
  }

  function renderSources(sources) {
    if (!sourcesSection || !sourcesList) return;
    sourcesList.innerHTML = "";
    if (sources && sources.length > 0) {
      sources.forEach((src) => {
        const li = document.createElement("li");
        li.className = "source-item";
        li.innerHTML = `
          <a href="${src.url}" target="_blank" rel="noopener noreferrer">${src.title || src.url}</a>
          <div class="source-snippet">${src.snippet || ""}</div>
        `;
        sourcesList.appendChild(li);
      });
      sourcesSection.classList.remove("hidden");
    } else {
      sourcesSection.classList.add("hidden");
    }
  }

  function renderEditView() {
    // 1. Render Editable Hashtags
    editableHashtagsContainer.innerHTML = "";
    state.hashtags.forEach((tag, index) => {
      const tagEl = document.createElement("div");
      tagEl.className = "tag-item";

      const input = document.createElement("input");
      input.type = "text";
      input.value = tag;
      input.dataset.index = index;
      input.addEventListener("input", (e) => {
        state.hashtags[index] = e.target.value.trim();
      });

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "tag-remove-btn";
      removeBtn.innerHTML = "&times;";
      removeBtn.title = "Remove hashtag";
      removeBtn.addEventListener("click", () => {
        state.hashtags.splice(index, 1);
        renderEditView();
      });

      tagEl.appendChild(input);
      tagEl.appendChild(removeBtn);
      editableHashtagsContainer.appendChild(tagEl);
    });

    // 2. Render Editable Keywords
    editableKeywordsContainer.innerHTML = "";
    state.keywords.forEach((kw, index) => {
      const tagEl = document.createElement("div");
      tagEl.className = "tag-item";

      const input = document.createElement("input");
      input.type = "text";
      input.value = kw;
      input.dataset.index = index;
      input.addEventListener("input", (e) => {
        state.keywords[index] = e.target.value.trim();
      });

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.className = "tag-remove-btn";
      removeBtn.innerHTML = "&times;";
      removeBtn.title = "Remove keyword";
      removeBtn.addEventListener("click", () => {
        state.keywords.splice(index, 1);
        renderEditView();
      });

      tagEl.appendChild(input);
      tagEl.appendChild(removeBtn);
      editableKeywordsContainer.appendChild(tagEl);
    });
  }

  function setEditMode(enable) {
    state.isEditMode = enable;
    if (enable) {
      editIcon.textContent = "✓";
      editToggleBtn.title = "Save and exit edit mode";
      editToggleBtn.classList.add("active");
      renderEditView();
      readOnlyView.classList.add("hidden");
      editView.classList.remove("hidden");
    } else {
      // Collect latest inputs from edit view before exiting
      const tagInputs = editableHashtagsContainer.querySelectorAll("input");
      state.hashtags = Array.from(tagInputs)
        .map((inp) => inp.value.trim())
        .filter((val) => val.length > 0);

      const kwInputs = editableKeywordsContainer.querySelectorAll("input");
      state.keywords = Array.from(kwInputs)
        .map((inp) => inp.value.trim())
        .filter((val) => val.length > 0);

      editIcon.textContent = "✎";
      editToggleBtn.title = "Enable edit mode";
      editToggleBtn.classList.remove("active");
      renderReadOnlyView();
      editView.classList.add("hidden");
      readOnlyView.classList.remove("hidden");
    }
  }

  // --- Add Items (in Edit Mode) ---

  function addNewHashtag() {
    let val = newHashtagInput.value.trim();
    if (!val) return;
    if (!val.startsWith("#")) {
      val = "#" + val;
    }
    state.hashtags.push(val);
    newHashtagInput.value = "";
    renderEditView();
  }

  function addNewKeyword() {
    const val = newKeywordInput.value.trim();
    if (!val) return;
    state.keywords.push(val);
    newKeywordInput.value = "";
    renderEditView();
  }

  addHashtagBtn.addEventListener("click", addNewHashtag);
  newHashtagInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addNewHashtag();
    }
  });

  addKeywordBtn.addEventListener("click", addNewKeyword);
  newKeywordInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      addNewKeyword();
    }
  });

  // --- Toggle Edit Mode ---

  editToggleBtn.addEventListener("click", () => {
    setEditMode(!state.isEditMode);
  });

  // --- Generate Action ---

  generateBtn.addEventListener("click", async () => {
    hideBanner();

    const eventVal = eventInput.value.trim();
    const locationVal = locationInput.value.trim();
    const descVal = descriptionInput.value.trim();

    // Strict Validation
    const missing = [];
    if (!eventVal) missing.push("an event");
    if (!locationVal) missing.push("a location");
    if (!descVal) missing.push("a description");

    if (missing.length > 0) {
      if (missing.length === 1) {
        showBanner(`Please enter ${missing[0]}.`, "error");
      } else if (missing.length === 2) {
        showBanner(`Please enter ${missing[0]} and ${missing[1]}.`, "error");
      } else {
        showBanner("Please enter an event, location, and description.", "error");
      }
      return;
    }

    // Exit edit mode if active before generating
    if (state.isEditMode) {
      setEditMode(false);
    }

    const includeSocial = includeSocialCheckbox ? includeSocialCheckbox.checked : false;

    // Set loading state with initial feedback
    setLoading(true, "Connecting to search...");

    try {
      const response = await fetch("/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream",
        },
        body: JSON.stringify({
          event: eventVal,
          location: locationVal,
          description: descVal,
          include_social: includeSocial,
        }),
      });

      if (!response.ok) {
        let errorDetail = `Server returned error (${response.status})`;
        try {
          const errData = await response.json();
          if (errData.detail) errorDetail = errData.detail;
        } catch (_) {}
        throw new Error(errorDetail);
      }

      const contentType = response.headers.get("content-type") || "";

      if (contentType.includes("text/event-stream") && response.body) {
        // Real-time Server-Sent Events stream from backend
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = "";
        let resultReceived = false;

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop(); // Keep incomplete fragment

          for (const rawLine of lines) {
            const line = rawLine.trim();
            if (!line.startsWith("data:")) continue;

            const jsonStr = line.replace(/^data:\s*/, "");
            if (!jsonStr) continue;

            let payload;
            try {
              payload = JSON.parse(jsonStr);
            } catch (err) {
              console.error("JSON parse error on stream payload:", err, jsonStr);
              continue;
            }

            if (payload.type === "status") {
              // Real-time search engine or processing message from Wigolo backend
              generateBtnText.textContent = payload.message;
              if (enginesDisplay) {
                enginesDisplay.textContent = payload.message;
                enginesDisplay.className = "engines-display active";
                enginesDisplay.classList.remove("hidden");
              }
            } else if (payload.type === "result") {
              resultReceived = true;
              state.hashtags = payload.hashtags || [];
              state.keywords = payload.keywords || [];
              state.sources = payload.sources || [];

              renderReadOnlyView();
              renderSources(state.sources);

              if (enginesDisplay) {
                const engines = (payload.engines_used && payload.engines_used.length > 0)
                  ? payload.engines_used
                  : ["Bing", "DuckDuckGo", "Wikipedia"];
                enginesDisplay.textContent = "Searched: " + engines.join(", ");
                enginesDisplay.className = "engines-display completed";
                enginesDisplay.classList.remove("hidden");
              }

              showBanner("Keywords and hashtags successfully retrieved and processed!", "success");
            } else if (payload.type === "error") {
              throw new Error(payload.detail || "An error occurred during generation.");
            }
          }
        }

        if (!resultReceived) {
          showBanner("Search stream completed.", "info");
        }
      } else {
        // Fallback for non-streaming response
        const data = await response.json();
        state.hashtags = data.hashtags || [];
        state.keywords = data.keywords || [];
        state.sources = data.sources || [];

        renderReadOnlyView();
        renderSources(state.sources);

        if (enginesDisplay) {
          const engines = (data.engines_used && data.engines_used.length > 0)
            ? data.engines_used
            : ["Bing", "DuckDuckGo", "Wikipedia"];
          enginesDisplay.textContent = "Searched: " + engines.join(", ");
          enginesDisplay.className = "engines-display completed";
          enginesDisplay.classList.remove("hidden");
        }

        showBanner("Keywords and hashtags successfully retrieved and processed!", "success");
      }
    } catch (err) {
      console.error("Generate error:", err);
      if (enginesDisplay) {
        enginesDisplay.className = "engines-display hidden";
        enginesDisplay.textContent = "";
      }
      showBanner(err.message || "An unexpected error occurred during generation.", "error");
    } finally {
      setLoading(false);
    }
  });

  // --- Create Event Action (Reset & Clear Cache) ---

  createEventBtn.addEventListener("click", async () => {
    hideBanner();

    // 1. Clear input fields
    eventInput.value = "";
    locationInput.value = "";
    descriptionInput.value = "";

    // 2. Clear state
    state.hashtags = [];
    state.keywords = [];
    state.sources = [];

    // 3. Exit edit mode and reset views
    setEditMode(false);
    renderReadOnlyView();
    renderSources([]);
    if (enginesDisplay) {
      enginesDisplay.textContent = "";
      enginesDisplay.className = "engines-display hidden";
    }

    // 4. Call backend to clear Wigolo cache
    try {
      const response = await fetch("/create-event", {
        method: "POST",
      });
      const rawText = await response.text();
      let data = {};
      try {
        data = JSON.parse(rawText);
      } catch (parseErr) {
        throw new Error(rawText || `Server returned error (${response.status})`);
      }

      if (!response.ok) {
        throw new Error(data.detail || rawText || "Failed to clear Wigolo cache.");
      }

      showBanner(data.message || "New event created and Wigolo cache cleared.", "success");
    } catch (err) {
      console.error("Create event error:", err);
      showBanner(`Event reset, but cache clear failed: ${err.message}`, "error");
    }
  });

  // Initial render (Empty state, Edit mode off)
  renderReadOnlyView();
});
