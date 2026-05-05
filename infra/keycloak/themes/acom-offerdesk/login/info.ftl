<#import "template.ftl" as layout>
<@layout.registrationLayout displayMessage=false; section>
    <#if section = "header">
        Статус операции
    <#elseif section = "form">
        <div id="kc-info-message" class="aod-status-card">
            <p class="aod-status-card__title">${message.summary}</p>
            <#if requiredActions??>
              <p class="aod-status-card__text">
                Следующие шаги: <strong><#items as reqActionItem>${kcSanitize(msg("requiredAction.${reqActionItem}"))?no_esc}<#sep>, </#items></strong>
              </p>
            </#if>

            <div class="aod-status-card__actions">
              <#if !skipLink??>
                <#if pageRedirectUri?has_content>
                  <a class="aod-link-button aod-link-button--primary" href="${pageRedirectUri}">${msg("backToApplication")}</a>
                <#elseif actionUri?has_content>
                  <a class="aod-link-button aod-link-button--primary" href="${actionUri}">${msg("proceedWithAction")}</a>
                <#elseif (client.baseUrl)?has_content>
                  <a class="aod-link-button aod-link-button--primary" href="${client.baseUrl}">${msg("backToApplication")}</a>
                <#else>
                  <a class="aod-link-button aod-link-button--primary" href="/">Вернуться в приложение</a>
                </#if>
              </#if>
              <a class="aod-link-button" href="${url.loginUrl}">К странице входа</a>
            </div>
        </div>
    </#if>
</@layout.registrationLayout>
