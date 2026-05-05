(function () {
  const TEXT_ATTR = "data-loading-text";

  function resolveSubmitter(event) {
    if (event.submitter) {
      return event.submitter;
    }

    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return null;
    }

    return form.querySelector('button[type="submit"], input[type="submit"]');
  }

  function swapLabel(element, nextText) {
    if (!nextText) {
      return;
    }

    if (!element.dataset.originalText) {
      element.dataset.originalText = element.tagName === "INPUT" ? element.value : element.textContent || "";
    }

    if (element.tagName === "INPUT") {
      element.value = nextText;
      return;
    }

    element.textContent = nextText;
  }

  document.addEventListener("submit", function (event) {
    const form = event.target;
    if (!(form instanceof HTMLFormElement)) {
      return;
    }

    const submitter = resolveSubmitter(event);
    const submitControls = form.querySelectorAll('button[type="submit"], input[type="submit"]');
    submitControls.forEach(function (control) {
      control.disabled = true;
      control.setAttribute("aria-disabled", "true");
      control.classList.add("is-loading");
      if (control === submitter) {
        swapLabel(control, control.getAttribute(TEXT_ATTR));
      }
    });
  });
})();
