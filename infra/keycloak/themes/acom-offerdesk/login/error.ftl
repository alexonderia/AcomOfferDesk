<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=false; section>
    <#if section = "header">
        Не удалось завершить действие
    <#elseif section = "form">
        <div id="kc-error-message" class="aod-status-card aod-status-card--danger">
            <p class="aod-status-card__title">${kcSanitize(message.summary)?no_esc}</p>
            <div class="aod-status-card__actions">
              <#if !skipLink?? && client?? && client.baseUrl?has_content>
                <a id="backToApplication" class="aod-link-button aod-link-button--primary" href="${client.baseUrl}">
                  ${msg("backToApplication")}
                </a>
              <#else>
                <a class="aod-link-button aod-link-button--primary" href="/">Вернуться в приложение</a>
              </#if>
              <a class="aod-link-button" href="${url.loginUrl}">К странице входа</a>
            </div>
        </div>
    </#if>
</@layout.registrationLayout>
