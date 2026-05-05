<#import "template.ftl" as layout>
<@layout.registrationLayout displayInfo=true; section>
    <#if section = "header">
        Подтверждение email
    <#elseif section = "form">
        <div class="aod-status-card">
            <p class="aod-status-card__title">
                <#if verifyEmail??>
                    Мы отправили письмо на ${verifyEmail}.
                <#else>
                    Мы отправили письмо на ${user.email}.
                </#if>
            </p>
            <p class="aod-status-card__text">
              Подтвердите адрес, чтобы завершить вход или регистрацию. Без подтверждения почты дальнейшие действия недоступны.
            </p>

            <#if isAppInitiatedAction??>
                <form id="kc-verify-email-form" class="${properties.kcFormClass!}" action="${url.loginAction}" method="post">
                    <div class="${properties.kcFormGroupClass!}">
                        <div id="kc-form-buttons" class="${properties.kcFormActionGroupClass!}">
                            <#if verifyEmail??>
                                <button
                                  class="${properties.kcButtonSecondaryClass!} aod-button aod-button--secondary"
                                  type="submit"
                                  data-loading-text="Отправляем повторно..."
                                >
                                  Отправить письмо повторно
                                </button>
                            <#else>
                                <button
                                  class="${properties.kcButtonPrimaryClass!} aod-button aod-button--primary"
                                  type="submit"
                                  data-loading-text="Отправляем письмо..."
                                >
                                  Отправить письмо
                                </button>
                            </#if>
                            <button class="${properties.kcButtonSecondaryClass!} aod-button aod-button--secondary" type="submit" name="cancel-aia" value="true" formnovalidate>
                              Отмена
                            </button>
                        </div>
                    </div>
                </form>
            </#if>
        </div>
    <#elseif section = "info">
        <#if !isAppInitiatedAction??>
            <div class="aod-inline-note">
              <p class="aod-inline-note__title">Письмо не пришло?</p>
              <p class="aod-inline-note__text">
                Проверьте папку «Спам» и, если нужно, запросите новую отправку по кнопке ниже.
              </p>
              <a class="aod-link-button" href="${url.loginAction}">Запросить письмо ещё раз</a>
            </div>
        </#if>
    </#if>
</@layout.registrationLayout>
