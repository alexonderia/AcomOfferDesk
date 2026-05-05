<#import "template.ftl" as layout>
<#import "field.ftl" as field>
<@layout.registrationLayout displayInfo=true displayMessage=!messagesPerField.existsError('username'); section>
    <#if section = "header">
        Восстановление доступа
    <#elseif section = "form">
        <div class="aod-page-copy aod-page-copy--quiet">
          <p>
            Введите логин или email. Мы отправим письмо для восстановления, если аккаунт найден.
          </p>
        </div>
        <form id="kc-reset-password-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post">
            <#assign label>
                <#if !realm.loginWithEmailAllowed>Логин<#elseif !realm.registrationEmailAsUsername>Логин или email<#else>Email</#if>
            </#assign>
            <@field.input name="username" label=label value=auth.attemptedUsername!'' autofocus=true />

            <div class="${properties.kcFormGroupClass!}">
              <div class="${properties.kcFormActionGroupClass!}">
                <button
                  id="kc-submit"
                  type="submit"
                  class="${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!} aod-button aod-button--primary"
                  data-loading-text="Отправляем письмо..."
                >
                  Отправить инструкцию
                </button>
                <a class="aod-plain-link" href="${url.loginUrl}">
                  Вернуться ко входу
                </a>
              </div>
            </div>
        </form>
    <#elseif section = "info">
        <span class="aod-helper-note">
            <#if realm.duplicateEmailsAllowed>
                Введите логин или email. Если учётная запись существует, мы отправим письмо с дальнейшими действиями.
            <#else>
                Введите логин или email. Если учётная запись существует, письмо для восстановления придёт на привязанный адрес.
            </#if>
        </span>
    </#if>
</@layout.registrationLayout>
