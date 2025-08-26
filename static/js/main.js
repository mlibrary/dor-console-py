

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
    triggerBtn.addEventListener("click", (event) => {
      lastTriggerBtn = triggerBtn;
      loadPageIntoModal(triggerBtn.dataset.modalHref, dialog)
      .then(() => {
        dialog.showModal();
        cancelBtn.focus();
      })
    });
  });
}

// FUNCTIONS
async function loadPageIntoModal(href, dialog) {
  // we could send an accept header for "application/json",
  // but then we'd have to build the UI, meh
  fetch(href, {
    credentials: "include",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Request error: ${response.status}`);
      }
      return response.text();
    })
    .then((text) => {
      const newDocument = new DOMParser().parseFromString(text, "text/html");

      detailEl = dialog.querySelector('[data-slot="dialog-detail"]');
      while (detailEl.firstChild) {
        detailEl.removeChild(detailEl.firstChild);
      }
      
      const newDetailEl = newDocument.querySelector('[data-slot="dialog-detail"]');
      detailEl.replaceWith(newDetailEl);
    });
}