(function () {
  function isFormControl(element) {
    return (
      element instanceof HTMLInputElement ||
      element instanceof HTMLTextAreaElement ||
      element instanceof HTMLSelectElement
    );
  }

  function shouldValidateControl(control) {
    if (!isFormControl(control)) {
      return false;
    }
    if (control.disabled) {
      return false;
    }
    if (control.type === "hidden" || control.type === "submit" || control.type === "button") {
      return false;
    }
    return true;
  }

  function findControlLabel(control) {
    if (control.labels && control.labels.length > 0) {
      return control.labels[0];
    }
    if (control.id) {
      return document.querySelector('label[for="' + control.id + '"]');
    }
    var formGroup = control.closest(".pf-v5-c-form__group");
    return formGroup ? formGroup.querySelector(".pf-v5-c-form__label-text, label") : null;
  }

  function findIndicatorHost(control) {
    var label = findControlLabel(control);
    if (!(label instanceof HTMLElement)) {
      return null;
    }

    return label.querySelector(".pf-v5-c-form__label-text") || label;
  }

  function isRequiredControl(control) {
    if (control.required || control.getAttribute("aria-required") === "true") {
      return true;
    }

    var label = findControlLabel(control);
    return (
      label instanceof HTMLElement &&
      label.querySelector(".pf-v5-c-form__label-required") instanceof HTMLElement
    );
  }

  function isControlFilled(control) {
    if (control instanceof HTMLSelectElement) {
      return (control.value || "").trim() !== "";
    }

    if (control instanceof HTMLInputElement) {
      if (control.type === "checkbox" || control.type === "radio") {
        return control.checked;
      }
      if (control.type === "file") {
        return (control.files && control.files.length > 0) || false;
      }
    }

    return (control.value || "").trim() !== "";
  }

  function isControlCompleted(control) {
    var nativeValid = control.checkValidity();
    if (!isRequiredControl(control)) {
      return nativeValid;
    }

    return isControlFilled(control) && nativeValid;
  }

  function syncRequiredIndicator(control, valid) {
    if (!isRequiredControl(control)) {
      return;
    }

    var host = findIndicatorHost(control);
    if (!(host instanceof HTMLElement)) {
      return;
    }

    host.classList.add("aod-required-label");

    var indicator = host.querySelector(".aod-required-indicator");
    if (!(indicator instanceof HTMLElement)) {
      indicator = document.createElement("span");
      indicator.className = "aod-required-indicator";
      indicator.setAttribute("aria-hidden", "true");
      host.appendChild(indicator);
    }

    indicator.classList.toggle("aod-required-indicator--valid", valid);
    indicator.classList.toggle("aod-required-indicator--invalid", !valid);
    indicator.textContent = valid ? "\u2713" : "!";
    indicator.title = valid
      ? "\u041f\u043e\u043b\u0435 \u0437\u0430\u043f\u043e\u043b\u043d\u0435\u043d\u043e \u0432\u0435\u0440\u043d\u043e"
      : "\u041e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u043e\u0435 \u043f\u043e\u043b\u0435";
  }

  function setControlValidityState(control) {
    if (!shouldValidateControl(control)) {
      return true;
    }
    var valid = isControlCompleted(control);
    control.setAttribute("aria-invalid", valid ? "false" : "true");
    syncRequiredIndicator(control, valid);
    return valid;
  }

  function initRegisterValidation() {
    var form = document.getElementById("kc-register-form");
    if (!(form instanceof HTMLFormElement)) {
      return;
    }

    var controls = Array.prototype.slice.call(form.querySelectorAll("input, textarea, select"));

    controls.forEach(function (control) {
      if (!shouldValidateControl(control)) {
        return;
      }

      syncRequiredIndicator(control, isControlCompleted(control));

      control.addEventListener("input", function () {
        setControlValidityState(control);
      });
      control.addEventListener("change", function () {
        setControlValidityState(control);
      });
      control.addEventListener("blur", function () {
        setControlValidityState(control);
      });
    });

    form.addEventListener("submit", function (event) {
      var firstInvalid = null;

      controls.forEach(function (control) {
        var valid = setControlValidityState(control);
        if (!valid && firstInvalid === null && shouldValidateControl(control)) {
          firstInvalid = control;
        }
      });

      if (firstInvalid !== null) {
        event.preventDefault();
        firstInvalid.focus();
        firstInvalid.reportValidity();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initRegisterValidation);
  } else {
    initRegisterValidation();
  }
})();
