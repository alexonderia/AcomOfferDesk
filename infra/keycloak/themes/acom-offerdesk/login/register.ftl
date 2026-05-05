<#import "template.ftl" as layout>
<#import "field.ftl" as field>
<#import "user-profile-commons.ftl" as userProfileCommons>
<#import "register-commons.ftl" as registerCommons>
<#import "password-validation.ftl" as validator>
<@layout.registrationLayout displayMessage=messagesPerField.exists('global') displayRequiredFields=true; section>
    <#if section = "header">
        Регистрация в AcomOfferDesk
    <#elseif section = "form">
        <div class="aod-page-copy aod-page-copy--quiet">
          <p>
            Заполните форму и подтвердите почту.
          </p>
        </div>

        <form id="kc-register-form" class="${properties.kcFormClass!}" action="${url.registrationAction}" method="post">
            <@userProfileCommons.userProfileFormFields; callback, attribute>
                <#if callback = "afterField">
                    <#if passwordRequired?? && (attribute.name == 'username' || (attribute.name == 'email' && realm.registrationEmailAsUsername))>
                        <@field.password name="password" required=true label="Пароль" autocomplete="new-password" />
                        <@field.password name="password-confirm" required=true label="Повторите пароль" autocomplete="new-password" />
                    </#if>
                </#if>
            </@userProfileCommons.userProfileFormFields>

            <@registerCommons.termsAcceptance/>

            <#if recaptchaRequired?? && (recaptchaVisible!false)>
                <div class="form-group">
                    <div class="${properties.kcInputWrapperClass!}">
                        <div class="g-recaptcha" data-size="compact" data-sitekey="${recaptchaSiteKey}" data-action="${recaptchaAction}"></div>
                    </div>
                </div>
            </#if>

            <#if recaptchaRequired?? && !(recaptchaVisible!false)>
                <script>
                    function onSubmitRecaptcha(token) {
                        document.getElementById("kc-register-form").requestSubmit();
                    }
                </script>
                <div id="kc-form-buttons" class="${properties.kcFormActionGroupClass!}">
                    <button
                      class="${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!} aod-button aod-button--primary g-recaptcha"
                      data-sitekey="${recaptchaSiteKey}"
                      data-callback="onSubmitRecaptcha"
                      data-action="${recaptchaAction}"
                      type="submit"
                      id="kc-submit"
                      data-loading-text="Регистрируем..."
                    >
                        Зарегистрироваться
                    </button>
                </div>
            <#else>
                <div id="kc-form-buttons" class="${properties.kcFormActionGroupClass!}">
                    <button
                      class="${properties.kcButtonPrimaryClass!} ${properties.kcButtonBlockClass!} aod-button aod-button--primary"
                      type="submit"
                      data-loading-text="Регистрируем..."
                    >
                      Зарегистрироваться
                    </button>
                </div>
            </#if>

            <div class="${properties.kcFormGroupClass!}">
              <div id="kc-form-options" class="aod-form-links">
                <a class="aod-plain-link" href="${url.loginUrl}">Вернуться ко входу</a>
              </div>
            </div>
        </form>

        <@validator.templates/>
        <@validator.script field="password"/>
    </#if>
</@layout.registrationLayout>
