

// ---- MODAL HANDLING
const dialog = document.getElementById("dialog");
if ( dialog ) {
  let lastTriggerBtn;

  const cancelBtn = dialog.querySelector(`button[data-action="close-modal"]`);
    // Close dialog when close button clicked
  cancelBtn.addEventListener("click", () => {
    dialog.close();
  });

  // Close dialog when clicking outside of it
  dialog.addEventListener("click", (e) => {
    if (e.target === dialog) {
      dialog.close();
    }
  });

  dialog.addEventListener("close", () => {
    if ( lastTriggerBtn ) {
      lastTriggerBtn.focus();
    }
  });

  const triggerBtns = document.querySelectorAll(
    `button[data-action="open-modal"]`
  );
  triggerBtns.forEach((triggerBtn) => {
    triggerBtn.addEventListener("click", async (event) => {
      lastTriggerBtn = triggerBtn;
      await loadPageIntoModal(triggerBtn.dataset.modalHref, dialog);
      dialog.showModal();
      cancelBtn.focus();
    });
  });
}

// ---- FILESET CONTENTS DISPLAY
document.querySelectorAll(`button[data-action="toggle-view-all-files"]`).forEach((btn) => {
  btn.addEventListener('click', () => {
    const wrapper = btn.closest("[data-view-all-files]");
    wrapper.dataset.viewAllFiles = !!!(wrapper.dataset.viewAllFiles == "true");
    btn.classList.toggle("toggled", wrapper.dataset.viewAllFiles == 'true');
  })
})

// FUNCTIONS
async function loadPageIntoModal(href, dialog) {
  // we could send an accept header for "application/json",
  // but then we'd have to build the UI, meh

  const response = await fetch(href, {
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error(`Request error: ${response.status}`);
  }

  const text = await response.text();
  const newDocument = new DOMParser().parseFromString(text, "text/html");

  detailEl = dialog.querySelector('[data-slot="dialog-detail"]');
  while (detailEl.firstChild) {
    detailEl.removeChild(detailEl.firstChild);
  }

  const newDetailEl = newDocument.querySelector(
    '[data-slot="dialog-detail"]'
  );
  detailEl.replaceWith(newDetailEl);
}