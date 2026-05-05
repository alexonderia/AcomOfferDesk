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

  function setControlValidityState(control) {
    if (!shouldValidateControl(control)) {
      return true;
    }
    const valid = control.checkValidity();
    control.setAttribute("aria-invalid", valid ? "false" : "true");
    return valid;
  }

  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("kc-register-form");
    if (!(form instanceof HTMLFormElement)) {
      return;
    }

    var controls = Array.prototype.slice.call(
      form.querySelectorAll("input, textarea, select")
    );

    controls.forEach(function (control) {
      if (!shouldValidateControl(control)) {
        return;
      }

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
  });
})();
