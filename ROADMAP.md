# PyPost: roadmap стабилизации и архитектурного оздоровления

Дата аудита: 2026-09-09.

Статусы:

- `[ ]` — задача не начата;
- `[~]` — задача начата, но не завершена;
- `[x]` — задача завершена и подтверждена проверкой.

## Цели

1. Устранить воспроизводимый native crash редактора переменных окружения.
2. Закрыть найденные сценарии тихой потери данных и отката настроек.
3. Сделать persistence и lifecycle предсказуемыми при ошибках и завершении приложения.
4. Восстановить заявленные границы между composition root, core, Qt-адаптерами и UI.
5. Добавить проверки, которые воспроизводят условия реального desktop runtime, а не только
   `offscreen`-окружение.

Этапы ниже расположены в порядке выполнения. Следующий этап начинается после выполнения
критериев завершения предыдущего, кроме явно независимых исследовательских подпунктов.

## [~] 0. Зафиксировать исходное состояние и доказательства

- [x] Воспроизвести падение в `EnvironmentDialog` на WSLg/Wayland с PySide6/Qt 6.11.1.
  - [x] Подтвердить exit code `139` / `SIGSEGV`.
  - [x] Зафиксировать native call chain:
    `QAbstractItemView::edit -> QWidget::setFocus -> inputMethodEvent -> edit`.
  - [x] Подтвердить, что падение вызывают повторные клики, открывающие редактор ячейки.
- [x] Отделить непосредственный триггер от непричастных компонентов.
  - [x] Подтвердить, что отключение Python-сигналов таблицы не устраняет падение.
  - [x] Подтвердить, что предварительное создание пустых `QTableWidgetItem` не устраняет
    падение.
  - [x] Подтвердить, что `StyleManager` не является необходимым условием падения.
  - [x] Подтвердить, что `QT_QPA_PLATFORM=offscreen` скрывает дефект.
  - [x] Локализовать провоцирующую конструкцию: редактируемый `QTableWidget` вместе с
    `QWidget/QCheckBox`, установленным через `setCellWidget`.
  - [x] Проверить безопасную альтернативу: checkable `QTableWidgetItem` без cell widget
    выдерживает повторные циклы редактирования.
- [x] Воспроизвести независимые дефекты целостности данных.
  - [x] Переименование `B` в существующий ключ `A` молча превращает
    `{"A": "1", "B": "2"}` в `{"A": "2"}`.
  - [x] После сохранения новых preferences запись UI-state может вернуть старые preferences.
  - [x] При неуспешной записи config-файла revision увеличивается, хотя файл не сохранён.
- [~] Получить полный baseline качества.
  - [x] Запустить environment UI/presenter tests: 105 тестов прошли.
  - [x] Запустить flake8: замечаний нет.
  - [x] Проверить архитектурные LOC-caps: лимиты соблюдены.
  - [x] Проверить mypy baseline: gate проходит, но разрешает 180 известных ошибок.
  - [ ] Запустить полный test suite в окружении, где разрешено создание локальных сокетов.
  - [ ] Сохранить итоговые версии Python, PySide6, Qt, QPA backend и результаты suite в
    отдельном regression report.

Критерий завершения этапа: полный baseline воспроизводим одной документированной командой,
а native crash запускается только в дочернем процессе и не обрушает основной test runner.

## [x] 1. Устранить native crash таблицы переменных окружения

### [x] 1.1. Добавить изолированный regression harness

- [x] Создать минимальный subprocess-repro для Wayland-сценария.
  - [x] Открыть `EnvironmentDialog` с минимум одной переменной.
  - [x] Несколько раз открыть редактор пустой key/value-ячейки кликами.
  - [x] Классифицировать normal exit, timeout и signal exit отдельно.
  - [x] Включить `PYTHONFAULTHANDLER=1` и сохранять ограниченный stderr/native stack.
- [x] Добавить безопасный обычный тест, запрещающий возврат к `setCellWidget` в hidden-колонке.
- [x] Пометить Wayland integration test отдельно от быстрого `offscreen` suite, если CI не
  предоставляет compositor.

### [x] 1.2. Заменить хрупкую реализацию hidden-колонки

- [x] Убрать `QWidget/QCheckBox` и `setCellWidget` из строк переменных.
- [x] Представлять hidden-флаг через `Qt.CheckStateRole` либо через
  `QAbstractTableModel` и delegate.
- [x] Удалить поиск checkbox через `findChild` и определение строки перебором всех widgets.
- [x] Сохранить существующие пользовательские контракты.
  - [x] Клик и клавиатура переключают hidden-флаг.
  - [x] Hidden value отображается маской, но реальное значение не теряется при rename/move.
  - [x] Пустая последняя строка продолжает добавлять новую переменную.
  - [x] Контекстные действия delete/move продолжают работать.
  - [x] Логи не раскрывают имя hidden-переменной без явного opt-in.
- [x] Проверить accessibility: check state должен читаться экранными средствами и меняться с
  клавиатуры.

### [x] 1.3. Подтвердить исправление

- [x] Прогнать существующие тесты `EnvironmentDialog` и `EnvironmentVariablesWidget`.
- [x] Выполнить не менее 100 циклов crash-repro на Wayland без signal exit.
- [x] Выполнить тот же сценарий на `offscreen`, чтобы не сломать CI.
- [x] Проверить пользовательский сценарий:
  `Manage -> пустая строка -> повторные клики -> ввод -> Save`.
- [x] Зафиксировать результат и удалить временные диагностические обходы, если они появятся.

Результат проверки 2026-09-09: 100 циклов завершились с exit code `0` на фактическом
QPA backend `wayland`, ещё 100 — на `offscreen`; cell widgets в hidden-колонке отсутствуют.
Связанный набор из 120 тестов: 119 passed, 1 Wayland opt-in test skipped в offscreen-запуске.

Критерий завершения этапа: повторные клики и редактирование не приводят к native crash на
Wayland, а hidden-переменные сохраняют прежнее поведение.

## [x] 2. Закрыть потерю данных в редакторе environment variables

### [x] 2.1. Ввести единый доменный контракт ключей

- [x] Дополнить domain-level validation проверкой уникальности нормализованного имени в рамках
  одного environment.
- [x] Возвращать типизированную причину отказа: empty, invalid syntax или duplicate.
- [x] Использовать один и тот же validator для добавления, rename, import и программного
  обновления переменных.

### [x] 2.2. Сделать редактирование транзакционным

- [x] Не пересобирать `env.variables` из всей визуальной таблицы на каждый `itemChanged`.
- [x] Хранить редактируемые строки в table model/working copy с устойчивой идентичностью строки.
- [x] Применять валидное изменение атомарно; при ошибке оставлять исходный ключ и значение.
- [x] Показывать понятную ошибку при duplicate key и возвращать фокус в проблемную ячейку.
- [x] Явно определить поведение очистки существующего ключа: подтверждённое удаление либо
  откат, но не неявная потеря записи.

### [x] 2.3. Добавить регрессии целостности

- [x] Покрыть rename ключа в существующий ключ.
- [x] Покрыть добавление duplicate key в последней строке.
- [x] Покрыть duplicate hidden key без раскрытия или потери secret value.
- [x] Покрыть invalid rename с сохранением порядка, значения и hidden-флага.
- [x] Покрыть cancel/close диалога и явно закрепить, какие изменения должны сохраняться.

Результат проверки 2026-09-09: связанный environment-набор — 383 passed, 1 Wayland opt-in
test skipped; повторный native Wayland harness — 100 циклов, exit code `0`. Flake8 и mypy
baseline (179 известных ошибок) проходят. Полный suite вне sandbox дошёл до 13% без ошибок, после чего завис в
существующем collection-import UI-тесте; тот же тест отдельно проходит за 17 ms.

Критерий завершения этапа: никакое невалидное или конфликтующее редактирование не изменяет
domain model и не удаляет существующую переменную.

## [ ] 3. Исправить split-brain настроек и persistence

### [ ] 3.1. Сначала закрепить найденный откат тестом

- [ ] Добавить integration test:
  `изменить theme -> сохранить Settings -> изменить open_tabs -> дождаться debounce`.
- [ ] Проверять, что новый theme и остальные preferences остаются на диске.
- [ ] Добавить аналогичные проверки для `last_environment_id` и `expanded_collections`.
- [ ] Проверить object identity или эквивалентный single-source-of-truth invariant между
  `MainWindow`, `StateManager` и composition root.

### [ ] 3.2. Создать одного владельца состояния настроек

- [ ] Загружать `AppSettings` ровно один раз в composition root.
- [ ] Передавать загруженный snapshot в `StateManager`, а не разрешать ему повторный load.
- [ ] После сохранения `SettingsDialog` обновлять тот же authoritative snapshot.
- [ ] Удалить либо исправить stale `ComposedApp.settings`, чтобы он не ссылался на другой объект.
- [ ] Не позволять `MainWindow` создавать собственные `ConfigManager/StateManager` в production
  path; тестовые defaults заменить явными fixtures/factories.

### [ ] 3.3. Сделать запись настроек атомарной и честной

- [ ] Записывать JSON во временный файл в том же каталоге.
- [ ] Flush/fsync данные перед `os.replace`, где это поддерживается.
- [ ] Увеличивать revision только для snapshot, который действительно будет сохранён.
- [ ] При ошибке не изменять in-memory revision и не оставлять обрезанный основной файл.
- [ ] Возвращать явный результат либо выбрасывать типизированную persistence-ошибку вместо
  проглатывания `Exception`.
- [ ] На UI-уровне показывать пользователю ошибку сохранения preferences.
- [ ] Добавить recovery policy для повреждённого JSON: backup/quarantine и явное сообщение,
  а не молчаливый переход к defaults.

### [ ] 3.4. Устранить гонку полных перезаписей

- [ ] Сериализовать обновления preferences и debounced UI-state через один repository/store.
- [ ] Перед записью UI-state объединять только принадлежащие ему поля с актуальными
  preferences.
- [ ] Покрыть случай, когда debounce был запланирован до открытия SettingsDialog, а срабатывает
  после сохранения новых preferences.
- [ ] Покрыть flush pending state при завершении приложения.

Критерий завершения этапа: все пути записи используют один актуальный snapshot, запись атомарна,
ошибка видима вызывающему коду, а UI-state не может откатить preferences.

## [ ] 4. Сделать lifecycle ресурсов полным и симметричным

### [ ] 4.1. Назначить владельцев ресурсов

- [ ] Включить `AlertManager` в объектный граф `ComposedApp` и общий shutdown contract.
- [ ] Определить единственного владельца для metrics server, MCP registry, alert handlers,
  history workers, storage workers и attach host.
- [ ] Останавливать владельцев в обратном порядке их создания.
- [ ] Сделать shutdown идемпотентным для normal close, startup failure и частично созданного
  приложения.

### [ ] 4.2. Закрыть утечки и нарушение изоляции

- [ ] Вызывать `AlertManager.close()` при каждом штатном и аварийном завершении session.
- [ ] При переданном `data_dir` направлять default alert log в изолированный data directory
  либо принимать отдельный `alert_log_path` в composition API.
- [ ] Не писать в реальный пользовательский home из `AgentAppSession` и тестовых fixtures.
- [ ] Если `compose_app` падает после запуска metrics server, гарантированно остановить уже
  созданные ресурсы.

### [ ] 4.3. Проверить lifecycle стресс-тестами

- [ ] Выполнить серию start/ready/shutdown в одном процессе.
- [ ] Проверять отсутствие роста logging handlers, открытых файлов, Qt top-level widgets и
  фоновых threads после каждого цикла.
- [ ] Покрыть исключение на каждом шаге composition и проверить rollback ранее созданных
  ресурсов.
- [ ] Проверить normal desktop close, agent shutdown и attach-host failure одним контрактом.

Критерий завершения этапа: после shutdown не остаётся принадлежащих приложению handlers,
файловых дескрипторов, listener threads или Qt owners; partial startup полностью откатывается.

## [ ] 5. Восстановить архитектурные границы core/Qt/UI

### [ ] 5.1. Разделить `MCPServerRegistry`

- [ ] Вынести Qt-независимую модель registry и state transitions в `core`.
- [ ] Ввести protocol/factory для server runtime вместо импорта конкретного
  `core.qt.MCPServerManager`.
- [ ] Перенести `QObject` и Qt signals в тонкий Qt/UI adapter.
- [ ] Отделить проверку конфигурации и ссылок от управления сокетами и процессом сервера.
- [ ] Определить thread-affinity всех state transitions.
- [ ] Защитить registry state от одновременного изменения watcher thread и UI thread либо
  маршалить все мутации на одного владельца event loop.

### [ ] 5.2. Завершить composition root

- [ ] Создавать concrete adapters, repositories, managers и lifecycle owner только в
  `compose_app`.
- [ ] Передавать `MainWindow` готовые presenter dependencies без fallback-конструкторов
  production-сервисов.
- [ ] Убрать повторные чтения config и скрытое создание storage/history/registry из UI-классов.
- [ ] Добавить архитектурный import-test, запрещающий `core -> core.qt` и `core -> ui`, кроме
  явно задокументированных adapter modules.

### [ ] 5.3. Не допустить обхода шифрования новым repository-слоем

- [ ] Перед подключением текущих `pypost/ports` и `pypost/adapters` определить migration plan
  со старого storage format.
- [ ] Не сохранять `Environment.model_dump()` напрямую, если environment содержит hidden values.
- [ ] Пропустить environment persistence через существующий secrets codec/encryption policy.
- [ ] Добавить contract tests, запрещающие plaintext hidden values в repository output.
- [ ] Подключить repositories к runtime либо удалить неиспользуемый параллельный persistence
  path; не поддерживать две расходящиеся реализации без явной миграционной границы.

Критерий завершения этапа: `core` не зависит от Qt, UI не создаёт infrastructure services,
а все environment repositories соблюдают единый encryption contract.

## [ ] 6. Сократить внешнюю поверхность metrics/MCP

### [ ] 6.1. Безопасные defaults и UX

- [ ] Сохранить loopback (`127.0.0.1`) безопасным default bind address.
- [ ] Перед применением `0.0.0.0` или другого non-loopback адреса показывать явное
  подтверждение с перечнем доступных endpoints.
- [ ] Отображать в Settings текущий authentication status и фактический bind address.

### [ ] 6.2. Разделить или защитить listener

- [ ] Разделить Prometheus `/metrics` и MCP endpoints по listener/configuration либо оформить
  единый явный security boundary.
- [ ] Добавить authentication для MCP resource transport при non-loopback bind.
- [ ] Решить судьбу legacy SSE: отключить по умолчанию, удалить после migration window либо
  защищать тем же policy, что и `/mcp`.
- [ ] Добавить integration tests, проверяющие доступность и отказ в доступе для loopback и
  non-loopback конфигураций.
- [ ] Не включать секреты, URL credentials и значения environment variables в metrics/resources.

Критерий завершения этапа: удалённый bind нельзя включить незаметно, а каждый опубликованный
endpoint имеет задокументированный и проверяемый trust/authentication contract.

## [ ] 7. Усилить quality gates и документацию

### [ ] 7.1. Тестовая матрица desktop runtime

- [ ] Оставить быстрый `offscreen` suite для основной логики.
- [ ] Добавить отдельный Linux Wayland smoke job для item views, dialogs, focus и input method.
- [ ] При возможности добавить X11/xcb smoke, чтобы различать backend-specific regressions.
- [ ] Запускать native-crash tests только в subprocess и считать любой signal exit провалом.
- [ ] Зафиксировать поддерживаемые версии Python/PySide6/Qt; не считать `requires-python >=3.11`
  достаточной compatibility matrix.

### [ ] 7.2. Сократить статический долг

- [ ] Запретить рост mypy baseline выше текущих 180 ошибок.
- [ ] Разделить ошибки stubs/API enum migrations и реальные ошибки типов.
- [ ] Устранить реальные нарушения Optional/return contracts в persistence и UI boundaries.
- [ ] Поэтапно снизить baseline до нуля либо до отдельно обоснованных vendor-stub suppressions.

### [ ] 7.3. Синхронизировать архитектурные документы

- [ ] Обновить документы, утверждающие, что settings представлены одним общим объектом.
- [ ] Обновить layer map: до исправления явно отразить зависимость
  `core.mcp_server_registry -> core.qt`.
- [ ] Добавить описание table model/delegate ownership для environment variables.
- [ ] Задокументировать единый lifecycle order и ответственность composition root.
- [ ] Удалить или пометить устаревшие выводы прошлых аудитов, которые уже не соответствуют
  runtime-коду.

### [ ] 7.4. Финальная приёмка

- [ ] Полный lint, typecheck и test suite проходят в поддерживаемой матрице.
- [ ] Все crash, data-loss, persistence и lifecycle regression tests проходят.
- [ ] Ручной smoke основных сценариев завершён на Wayland.
- [ ] Security smoke подтверждает безопасный loopback default и защищённый remote bind.
- [ ] Для каждого временного compatibility workaround назначены владелец и срок удаления.

Критерий завершения roadmap: все пункты отмечены `[x]`, известные native crash и сценарии
потери данных закрыты regression tests, а документация совпадает с фактическими границами и
lifecycle приложения.
