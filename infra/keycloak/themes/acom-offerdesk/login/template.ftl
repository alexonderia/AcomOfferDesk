<#import "field.ftl" as field>
<#import "footer.ftl" as loginFooter>
<#macro username>
  <#assign label>
    <#if !realm.loginWithEmailAllowed>Логин<#elseif !realm.registrationEmailAsUsername>Логин или email<#else>Email</#if>
  </#assign>
  <@field.group name="username" label=label>
    <div class="${properties.kcInputGroup}">
      <div class="${properties.kcInputGroupItemClass} ${properties.kcFill}">
        <span class="${properties.kcInputClass} ${properties.kcFormReadOnlyClass}">
          <input id="kc-attempted-username" value="${auth.attemptedUsername}" readonly>
        </span>
      </div>
      <div class="${properties.kcInputGroupItemClass}">
        <button
          id="reset-login"
          class="${properties.kcFormPasswordVisibilityButtonClass} aod-inline-icon-button"
          type="button"
          aria-label="${msg('restartLoginTooltip')}"
          onclick="location.href='${url.loginRestartFlowUrl}'"
        >
          <span aria-hidden="true">↻</span>
        </button>
      </div>
    </div>
  </@field.group>
</#macro>

<#macro registrationLayout bodyClass="" displayInfo=false displayMessage=true displayRequiredFields=false>
<!DOCTYPE html>
<html class="${properties.kcHtmlClass!}" lang="${lang}"<#if realm.internationalizationEnabled> dir="${(locale.rtl)?then('rtl','ltr')}"</#if>>
<head>
    <meta charset="utf-8">
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>${msg("loginTitle",(realm.displayName!''))}</title>
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet" />
    <link rel="icon" href="${url.resourcesPath}/img/brand-mark.svg?v=${properties.aodAssetVersion!'dev'}" type="image/svg+xml" />
    <#if properties.stylesCommon?has_content>
        <#list properties.stylesCommon?split(' ') as style>
            <link href="${url.resourcesCommonPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <#if properties.styles?has_content>
        <#list properties.styles?split(' ') as style>
            <link href="${url.resourcesPath}/${style}" rel="stylesheet" />
        </#list>
    </#if>
    <link href="${url.resourcesPath}/css/acom-offerdesk.css?v=${properties.aodAssetVersion!'dev'}" rel="stylesheet" />
    <script type="importmap">
        {
            "imports": {
                "rfc4648": "${url.resourcesCommonPath}/vendor/rfc4648/rfc4648.js"
            }
        }
    </script>
    <#if properties.scripts?has_content>
        <#list properties.scripts?split(' ') as script>
            <script src="${url.resourcesPath}/${script}" type="text/javascript" defer></script>
        </#list>
    </#if>
    <#if scripts??>
        <#list scripts as script>
            <script src="${script}" type="text/javascript"></script>
        </#list>
    </#if>
    <script type="module" src="${url.resourcesPath}/js/passwordVisibility.js"></script>
    <script type="module">
        <#outputformat "JavaScript">
        import { startSessionPolling } from "${url.resourcesPath}/js/authChecker.js";

        startSessionPolling(
            ${url.ssoLoginInOtherTabsUrl?c}
        );
        </#outputformat>
    </script>
    <script type="module">
        document.addEventListener("click", (event) => {
            const link = event.target.closest("a[data-once-link]");

            if (!link) {
                return;
            }

            if (link.getAttribute("aria-disabled") === "true") {
                event.preventDefault();
                return;
            }

            const { disabledClass } = link.dataset;

            if (disabledClass) {
                link.classList.add(...disabledClass.trim().split(/\s+/));
            }

            link.setAttribute("role", "link");
            link.setAttribute("aria-disabled", "true");
        });
    </script>
    <#if authenticationSession??>
        <script type="module">
             <#outputformat "JavaScript">
            import { checkAuthSession } from "${url.resourcesPath}/js/authChecker.js";

            checkAuthSession(
                ${authenticationSession.authSessionIdHash?c}
            );
            </#outputformat>
        </script>
    </#if>
</head>

<body id="keycloak-bg" class="aod-body ${bodyClass}" data-page-id="login-${pageId}">
  <div class="aod-page">
    <main class="aod-shell">
      <section class="aod-card" aria-label="${realm.displayName!msg("loginTitle",(realm.displayName!''))}">
        <div class="aod-card__header">
          <h1 class="aod-card__title" id="kc-page-title"><#nested "header"></h1>
          <#if realm.internationalizationEnabled && locale.supported?size gt 1>
            <label class="aod-locale-switch" for="login-select-toggle">
              <span>Язык</span>
              <select
                aria-label="${msg('languages')}"
                id="login-select-toggle"
                onchange="if (this.value) window.location.href=this.value"
              >
                <#list locale.supported?sort_by("label") as l>
                  <option value="${l.url}" ${(l.languageTag == locale.currentLanguageTag)?then('selected','')}>${l.label}</option>
                </#list>
              </select>
            </label>
          </#if>
        </div>

        <#if !(auth?has_content && auth.showUsername() && !auth.showResetCredentials())>
          <#if displayRequiredFields>
            <div class="aod-required-hint">
              <span class="aod-required-hint__mark">*</span>
              <span>${msg("requiredFields")}</span>
            </div>
          </#if>
        <#else>
          <#if displayRequiredFields>
            <div class="aod-required-hint">
              <span class="aod-required-hint__mark">*</span>
              <span>${msg("requiredFields")}</span>
            </div>
          </#if>
          <div class="aod-username-lock">
            <#nested "show-username">
            <@username />
          </div>
        </#if>

        <#if displayMessage && message?has_content && (message.type != 'warning' || !isAppInitiatedAction??)>
          <#assign alertSummary = message.summary>
          <#assign hideAlert = false>
          <#if alertSummary == "Please re-authenticate to continue">
            <#assign hideAlert = true>
          </#if>
          <#if alertSummary == "You need to change your password to activate your account.">
            <#assign alertSummary = "Чтобы активировать учётную запись, смените пароль.">
          </#if>
          <#if !hideAlert>
            <div class="aod-alert aod-alert--${message.type}">
              <span class="aod-alert__icon" aria-hidden="true">
                <#if message.type = "success">✓<#elseif message.type = "warning">!<#elseif message.type = "error">×<#else>i</#if>
              </span>
              <div class="aod-alert__content">${kcSanitize(alertSummary)?no_esc}</div>
            </div>
          </#if>
        </#if>

        <div class="aod-card__body">
          <#nested "form">

          <#if auth?has_content && auth.showTryAnotherWayLink()>
            <form id="kc-select-try-another-way-form" class="aod-try-another-way" action="${url.loginAction}" method="post" novalidate="novalidate">
              <input type="hidden" name="tryAnotherWay" value="on"/>
              <a
                id="try-another-way"
                href="javascript:document.forms['kc-select-try-another-way-form'].requestSubmit()"
                class="${properties.kcButtonSecondaryClass} ${properties.kcButtonBlockClass} aod-button aod-button--secondary"
                data-loading-text="Проверяем..."
              >
                ${msg("doTryAnotherWay")}
              </a>
            </form>
          </#if>

          <#if displayInfo || (auth?has_content && auth.showTryAnotherWayLink())>
            <div class="aod-card__footer">
              <#nested "socialProviders">
              <#if displayInfo>
                <div id="kc-info" class="aod-card__info">
                  <#nested "info">
                </div>
              </#if>
            </div>
          <#else>
            <#nested "socialProviders">
          </#if>
        </div>

        <div class="aod-card__meta">
          <p>Безопасный вход</p>
        </div>
      </section>
    </main>

    <@loginFooter.content/>
  </div>
</body>
</html>
</#macro>
