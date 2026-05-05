// LEGACY_TELEGRAM: page is excluded from active routes and kept only for rollback.
import { zodResolver } from '@hookform/resolvers/zod';
import ArrowBackIosNewRoundedIcon from '@mui/icons-material/ArrowBackIosNewRounded';
import { Alert, Box, Button, IconButton, Paper, Stack, TextField, Typography } from '@mui/material';
import { useEffect, useMemo, useState } from 'react';
import { useForm } from 'react-hook-form';
import { useSearchParams } from 'react-router-dom';
import { z } from 'zod';
import { checkTgLoginAvailability, completeTgRegistration } from '@shared/api/auth/completeTgRegistration';

type RegistrationField = {
    label: string;
    name: keyof RegistrationFormValues;
    type?: string;
    multiline?: boolean;
    rows?: number;
};

type RegistrationStep = {
    subtitle: string;
    fields: RegistrationField[];
};

const stepTitles: RegistrationStep[] = [
    {
        subtitle: 'Придумайте данные для входа',
        fields: [
            { label: 'Логин', name: 'login' },
            { label: 'Пароль', name: 'password', type: 'password' },
            { label: 'Повторите пароль', name: 'password_confirm', type: 'password' }
        ]
    },
    {
        subtitle: 'Введите личные данные для связи',
        fields: [
            { label: 'ФИО', name: 'full_name' },
            { label: 'Телефон', name: 'phone' },
            { label: 'Электронная почта', name: 'mail' }
        ]
    },
    {
        subtitle: 'Введите юридические данные компании',
        fields: [
            { label: 'ИНН', name: 'inn' },
            { label: 'Наименование', name: 'company_name' },
            { label: 'Телефон', name: 'company_phone' },
            { label: 'Электронная почта', name: 'company_mail' },
            { label: 'Адрес', name: 'address' },
            { label: 'Дополнительная информация', name: 'note', multiline: true, rows: 3 }
        ]
    }
];

const normalizePhone = (value: string) => value.replace(/\D/g, '');
const byteLength = (value: string) => new TextEncoder().encode(value).length;
const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;

const schema = z
    .object({
        login: z.string().min(3, 'Минимум 3 символа').max(128, 'Максимум 128 символов'),
        password: z
            .string()
            .min(6, 'Минимум 6 символов')
            .max(72, 'Максимум 72 символа')
            .refine((value) => byteLength(value) <= 72, 'Пароль слишком длинный (до 72 байт)'),
        password_confirm: z
            .string()
            .min(6, 'Минимум 6 символов')
            .max(72, 'Максимум 72 символа')
            .refine((value) => byteLength(value) <= 72, 'Пароль слишком длинный (до 72 байт)'),
        full_name: z.string().min(1, 'Введите ФИО').max(256, 'Максимум 256 символов'),
        phone: z
            .string()
            .min(1, 'Введите телефон')
            .max(64, 'Максимум 64 символа')
            .refine((value) => {
                const normalized = normalizePhone(value);
                return normalized.length === 11 && (normalized.startsWith('7') || normalized.startsWith('8'));
            }, 'Некорректный телефон'),
        mail: z
            .string()
            .max(256, 'Максимум 256 символов')
            .optional()
            .refine((value) => !value?.trim() || emailRegex.test(value), 'Некорректный email'),
        company_name: z.string().min(1, 'Введите наименование').max(256, 'Максимум 256 символов'),
        inn: z
            .string()
            .min(1, 'Введите ИНН')
            .max(32, 'Максимум 32 символа')
            .regex(/^\d{10}$|^\d{12}$/, 'Некорректный ИНН'),
        company_phone: z
            .string()
            .min(1, 'Введите телефон')
            .max(64, 'Максимум 64 символа')
            .refine((value) => {
                const normalized = normalizePhone(value);
                return normalized.length === 11 && (normalized.startsWith('7') || normalized.startsWith('8'));
            }, 'Некорректный телефон'),
        company_mail: z
            .string()
            .max(256, 'Максимум 256 символов')
            .optional()
            .refine((value) => !value?.trim() || emailRegex.test(value), 'Некорректный email'),
        address: z.string().max(256, 'Максимум 256 символов').optional(),
        note: z.string().max(1024, 'Максимум 1024 символа').optional()
    })
    .refine((data) => data.password === data.password_confirm, {
        message: 'Пароли не совпадают',
        path: ['password_confirm']
    });

type RegistrationFormValues = z.infer<typeof schema>;

const stepFields: Array<Array<keyof RegistrationFormValues>> = [
    ['login', 'password', 'password_confirm'],
    ['full_name', 'phone', 'mail'],
    ['inn', 'company_name', 'company_phone', 'company_mail', 'address', 'note']
];

export const TgRegisterPage = () => {
    const [searchParams] = useSearchParams();
    const token = searchParams.get('token');
    const hasToken = Boolean(token);
    const [step, setStep] = useState(0);
    const currentStep = useMemo(() => stepTitles[step], [step]);
    const [stepValidationAttempts, setStepValidationAttempts] = useState<Record<number, boolean>>({});
    const [interactedFields, setInteractedFields] = useState<Partial<Record<keyof RegistrationFormValues, boolean>>>({});
    const [errorMessage, setErrorMessage] = useState<string | null>(null);
    const [isCompleted, setIsCompleted] = useState(false);
    const [loginStatus, setLoginStatus] = useState<{ available: boolean; detail: string } | null>(null);

    const {
        register,
        handleSubmit,
        trigger,
        watch,
        formState: { errors, isSubmitting },
        reset,
        setError,
        clearErrors
    } = useForm<RegistrationFormValues>({
        resolver: zodResolver(schema),
        mode: 'onChange',
        reValidateMode: 'onChange',
        defaultValues: {
            login: '',
            password: '',
            password_confirm: '',
            full_name: '',
            phone: '',
            mail: '',
            company_name: '',
            inn: '',
            company_phone: '',
            company_mail: '',
            address: '',
            note: ''
        }
    });

    const loginValue = watch('login');
    const watchedValues = watch();
    const isLastStep = step === stepTitles.length - 1;

    useEffect(() => {
        if (!token || loginValue.trim().length < 3) {
            setLoginStatus(null);
            return;
        }

        const timer = setTimeout(async () => {
            try {
                const result = await checkTgLoginAvailability(token, loginValue.trim());
                setLoginStatus(result);
            } catch {
                setLoginStatus({ available: false, detail: 'Не удалось проверить логин. Повторите позже.' });
            }
        }, 400);

        return () => clearTimeout(timer);
    }, [loginValue, token]);

    useEffect(() => {
        if (errorMessage) {
            setErrorMessage(null);
        }
    }, [watchedValues, errorMessage]);

    useEffect(() => {
        if (step !== 0 || !loginStatus) {
            return;
        }

        if (loginStatus.available) {
            clearErrors('login');
            if (errorMessage === 'Логин уже занят') {
                setErrorMessage(null);
            }
            return;
        }

        if (loginValue.trim().length >= 3) {
            setError('login', { type: 'manual', message: loginStatus.detail });
        }
    }, [loginStatus, step, loginValue, clearErrors, setError, errorMessage]);

    const handleNext = async () => {
        setStepValidationAttempts((prev) => ({ ...prev, [step]: true }));
        const fields = stepFields[step];
        const isValid = await trigger(fields, { shouldFocus: true });
        if (!isValid) {
            return;
        }

        if (step === 0 && loginStatus && !loginStatus.available) {
            setErrorMessage('Логин уже занят');
            return;
        }

        setStep((prev) => Math.min(prev + 1, stepTitles.length - 1));
    };

    const handleBack = () => {
        setStep((prev) => Math.max(prev - 1, 0));

    };

    const shouldShowFieldError = (fieldName: keyof RegistrationFormValues) => {
        if (!errors[fieldName]) {
            return false;
        }

        return Boolean(stepValidationAttempts[step]) || Boolean(interactedFields[fieldName]);
    };

    const onSubmit = async (values: RegistrationFormValues) => {
        if (!token) {
            setErrorMessage('Ссылка недействительна. Перейдите по новой регистрационной ссылке.');
            return;
        }
        setErrorMessage(null);

        try {
            await completeTgRegistration({
                token,
                login: values.login,
                password: values.password,
                password_confirm: values.password_confirm,
                full_name: values.full_name,
                phone: values.phone,
                mail: values.mail?.trim() ? values.mail.trim() : "Не указано",
                company_name: values.company_name,
                inn: values.inn,
                company_phone: values.company_phone,
                company_mail: values.company_mail?.trim() ? values.company_mail.trim() : 'Не указано',
                address: values.address?.trim() ? values.address : 'Не указано',
                note: values.note?.trim() ? values.note : 'Не указано'
            });
            setIsCompleted(true);
            setStepValidationAttempts({});
            setInteractedFields({});
            reset();
        } catch (error) {
            setErrorMessage(error instanceof Error ? error.message : 'Не удалось отправить данные регистрации');
        }
    };

    return (
        <Box
            sx={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: 3
            }}
        >
            <Paper
                elevation={0}
                sx={(theme) => ({
                    width: { xs: '90%', sm: 420 },
                    borderRadius: 4,
                    border: `1px solid ${theme.palette.divider}`,
                    backgroundColor: theme.palette.background.paper,
                    padding: { xs: 4, sm: 6 }
                })}
            >
                <Stack spacing={4} alignItems="center" component="form" onSubmit={handleSubmit(onSubmit)}>
                    {!isCompleted ? (
                        <Stack width="100%" spacing={2} alignItems="center">
                            <Stack width="100%" direction="row" justifyContent="space-between" alignItems="center">
                                {step > 0 && hasToken && !isCompleted ? (
                                    <IconButton aria-label="Назад" onClick={handleBack} sx={{ padding: 0, color: 'text.primary' }}>
                                        <ArrowBackIosNewRoundedIcon sx={{ fontSize: 20 }} />
                                    </IconButton>
                                ) : (
                                    <span />
                                )}
                                <Typography variant="body2" color="text.secondary">
                                    шаг {step + 1} / {stepTitles.length}
                                </Typography>
                            </Stack>
                            <Stack spacing={1} alignItems="center">
                                <Typography variant="h5" fontWeight={600} color="text.primary">
                                    Регистрация
                                </Typography>
                                <Typography variant="body2" color="text.secondary" textAlign="center">
                                    {currentStep.subtitle}
                                </Typography>
                            </Stack>
                        </Stack>
                    ) : null}

                    {!hasToken ? (
                        <Typography variant="body2" color="error" textAlign="center">
                            Ссылка недействительна. Пожалуйста, перейдите по новой регистрационной ссылке.
                        </Typography>
                    ) : isCompleted ? (
                        <Alert severity="success" sx={{ width: '100%', fontSize: 18, lineHeight: 1.4, py: 3, px: 2 }}>
                            Регистрация завершена. Данные отправлены на проверку. Уведомление о выдаче доступа придёт на вашу почту.
                        </Alert>
                    ) : (
                        <Stack spacing={2.5} width="100%" alignItems="center">
                            {currentStep.fields.map((field) => {
                                const registration = register(field.name);

                                return (
                                    <TextField
                                        key={field.label}
                                        fullWidth
                                        label={field.label}
                                        type={field.type ?? 'text'}
                                        variant="outlined"
                                        multiline={Boolean(field.multiline)}
                                        rows={field.rows}
                                        error={shouldShowFieldError(field.name)}
                                        helperText={shouldShowFieldError(field.name) ? errors[field.name]?.message : ''}
                                        InputProps={{
                                            sx: (theme) => ({
                                                borderRadius: field.multiline ? 3 : 999,
                                                backgroundColor: theme.palette.primary.light
                                            })
                                        }}
                                        name={registration.name}
                                        inputRef={registration.ref}
                                        onBlur={(event) => {
                                            registration.onBlur(event);
                                            setInteractedFields((prev) => ({ ...prev, [field.name]: true }));
                                        }}
                                        onChange={(event) => {
                                            registration.onChange(event);
                                            if (!interactedFields[field.name]) {
                                                setInteractedFields((prev) => ({ ...prev, [field.name]: true }));
                                            }
                                        }}
                                    />
                                );
                            })}
                            {step === 0 && loginStatus ? (
                                <Alert severity={loginStatus.available ? 'success' : 'warning'} sx={{ width: '100%' }}>
                                    {loginStatus.detail}
                                </Alert>
                            ) : null}
                            {errorMessage ? <Alert severity="error">{errorMessage}</Alert> : null}
                            <Button
                                variant="outlined"
                                onClick={
                                    isLastStep
                                        ? () => setStepValidationAttempts((prev) => ({ ...prev, [step]: true }))
                                        : () => void handleNext()
                                }
                                type={isLastStep ? 'submit' : 'button'}
                                disabled={isSubmitting || isCompleted}
                                sx={(theme) => ({
                                    width: '100%',
                                    borderRadius: 999,
                                    textTransform: 'none',
                                    backgroundColor: theme.palette.background.paper,
                                    paddingY: 1.3
                                })}
                            >
                                {isLastStep ? (isSubmitting ? 'Отправка...' : 'Зарегистрироваться') : 'Далее'}
                            </Button>
                        </Stack>
                    )}
                </Stack>
            </Paper>
        </Box>
    );
};
