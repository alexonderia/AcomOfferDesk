<#import "template.ftl" as layout>
<#import "field.ftl" as field>
<#import "social-providers.ftl" as identityProviders>
<#import "passkeys.ftl" as passkeys>
<@layout.registrationLayout displayMessage=!messagesPerField.existsError('username','password') displayInfo=false; section>
    <#if section = "header">
        Вход в AcomOfferDesk
    <#elseif section = "form">
        <div id="kc-form">
          <div id="kc-form-wrapper">
            <#if realm.password>
              <form id="kc-form-login" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post" novalidate="novalidate">
                <#if !usernameHidden??>
                  <#assign usernameLabel>
                    <#if !realm.loginWithEmailAllowed>Логин<#elseif !realm.registrationEmailAsUsername>Логин или email<#else>Email</#if>
                  </#assign>
                  <@field.input
                    name="username"
                    label=usernameLabel
                    error=messagesPerField.getFirstError('username','password')
                    autofocus=true
                    autocomplete="${(enableWebAuthnConditionalUI?has_content)?then('username webauthn', 'username')}"
                    value=login.username!''
                  />
                  <@field.password
                    name="password"
                    label="Пароль"
                    error=""
                    forgotPassword=realm.resetPasswordAllowed
                    autofocus=usernameHidden??
                    autocomplete="current-password"
                  >
                    <#if realm.rememberMe && !usernameHidden??>
                      <@field.checkbox name="rememberMe" label="Запомнить меня" value=login.rememberMe?? />
                    </#if>
                  </@field.password>
                <#else>
                  <@field.password
                    name="password"
                    label="Пароль"
                    forgotPassword=realm.resetPasswordAllowed
                    autofocus=usernameHidden??
                    autocomplete="current-password"
                  >
                    <#if realm.rememberMe && !usernameHidden??>
                      <@field.checkbox name="rememberMe" label="Запомнить меня" value=login.rememberMe?? />
                    </#if>
                  </@field.password>
                </#if>

                <input
                  type="hidden"
                  id="id-hidden-input"
                  name="credentialId"
                  <#if auth.selectedCredential?has_content>value="${auth.selectedCredential}"</#if>
                />
                <div class="${properties.kcFormGroupClass!}">
                  <div class="${properties.kcFormActionGroupClass!}">
                    <button
                      id="kc-login"
                      name="login"
                      type="submit"
                      class="${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!} aod-button aod-button--primary"
                      data-loading-text="Входим..."
                    >
                      Войти
                    </button>
                  </div>
                </div>
              </form>
            </#if>
          </div>
        </div>
        <@passkeys.conditionalUIData />
    <#elseif section = "socialProviders">
        <#if realm.password && social.providers?? && social.providers?has_content>
          <div class="aod-social-block">
            <p class="aod-social-block__title">Альтернативные провайдеры входа</p>
            <@identityProviders.show social=social/>
          </div>
        </#if>
    </#if>
</@layout.registrationLayout>
