# Пользовательские памятки

Рабочая версия контента — `web/src/shared/content/roleGuides.ts`. UI использует её без обращения к исходным DOCX или debug JSON.

Единственный действующий генератор принимает исходный согласованный DOCX явным аргументом:

```powershell
python scripts/generate_role_guides_from_docx.py path/to/approved-guides.docx
```

По умолчанию обновляется `roleGuides.ts`. Для проверки без изменения приложения:

```powershell
python scripts/generate_role_guides_from_docx.py path/to/approved-guides.docx --output artifacts/docx/roleGuides.ts --debug-output artifacts/docx/role-guides.json
python scripts/inspect_docx.py path/to/approved-guides.docx --output artifacts/docx/structure-sample.json
```

Нужен Python-пакет `python-docx`. Сначала просмотрите diff и соответствие текущим permissions/ролям, затем запускайте frontend lint/build. Архивные выгрузки не считаются согласованным актуальным источником; автоматическая перегенерация из них не выполняется.
