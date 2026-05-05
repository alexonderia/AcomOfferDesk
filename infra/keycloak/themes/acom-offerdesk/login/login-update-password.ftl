<#import "template.ftl" as layout>
<#import "password-commons.ftl" as passwordCommons>
<#import "field.ftl" as field>
<#import "password-validation.ftl" as validator>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('password','password-confirm'); section>
    <#if section = "header">
        Новый пароль
    <#elseif section = "form">
        <form id="kc-passwd-update-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post" novalidate="novalidate">
            <@field.password name="password-new" label="Новый пароль" fieldName="password" autocomplete="new-password" autofocus=true />
            <@field.password name="password-confirm" label="Повторите пароль" autocomplete="new-password" />

            <div class="${properties.kcFormGroupClass!}">
                <@passwordCommons.logoutOtherSessions/>
            </div>

            <div class="${properties.kcFormGroupClass!}">
              <div class="${properties.kcFormActionGroupClass!}">
                <#if isAppInitiatedAction??>
                  <button
                    id="kc-submit"
                    name="login"
                    type="submit"
                    class="${properties.kcButtonPrimaryClass!} aod-button aod-button--primary"
                    data-loading-text="Сохраняем пароль..."
                  >
                    Сохранить пароль
                  </button>
                  <button class="${properties.kcButtonSecondaryClass!} aod-button aod-button--secondary" id="kc-cancel" name="cancel-aia" type="submit">
                    Отмена
                  </button>
                <#else>
                  <button
                    id="kc-submit"
                    name="login"
                    type="submit"
                    class="${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!} aod-button aod-button--primary"
                    data-loading-text="Сохраняем пароль..."
                  >
                    Сохранить пароль
                  </button>
                </#if>
              </div>
            </div>
        </form>

        <@validator.templates/>
        <@validator.script field="password-new"/>
    </#if>
</@layout.registrationLayout>
