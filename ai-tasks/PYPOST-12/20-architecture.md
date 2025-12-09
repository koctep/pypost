# PYPOST-12: Сохранение состояния дерева вызовов

## Исследования

В `PySide6` `QTreeView` имеет методы `expand(index)`, `collapse(index)` и `isExpanded(index)`.
Модель данных (`QStandardItemModel`) хранит данные. Элементы верхнего уровня (коллекции) имеют `Qt.UserRole` с ID коллекции (UUID).

Для отслеживания изменений состояния разворачивания/сворачивания можно использовать сигналы `expanded(QModelIndex)` и `collapsed(QModelIndex)` самого `QTreeView`.

Хранение настроек уже реализовано через `AppSettings` и `ConfigManager`. Нам нужно добавить новое поле в `AppSettings`.

## План реализации

1.  **Модель данных**:
    *   Обновить `pypost/models/settings.py`: добавить поле `expanded_collections: List[str] = []` в класс `AppSettings`.

2.  **UI Логика (`MainWindow`)**:
    *   В `__init__` или `load_collections`:
        *   После загрузки данных пройтись по элементам модели.
        *   Если ID коллекции есть в `settings.expanded_collections`, вызвать `self.collections_view.expand(index)`.
    *   Подключить сигналы `QTreeView.expanded` и `QTreeView.collapsed` к новым слотам.
    *   В слотах обработки сигналов:
        *   Получить ID коллекции из индекса.
        *   Обновить список `expanded_collections` в `self.settings`.
        *   Сохранить настройки через `self.config_manager.save_config(self.settings)`.

## Архитектура

### 1. Модели (`pypost/models/settings.py`)

Изменение схемы настроек для хранения списка ID развернутых коллекций.

```python
class AppSettings(BaseModel):
    # ... existing fields
    expanded_collections: List[str] = Field(default_factory=list) 
```

### 2. MainWindow (`pypost/ui/main_window.py`)

Добавление логики обработки сигналов дерева и восстановления состояния.

*   **Новые методы**:
    *   `on_tree_expanded(index: QModelIndex)`: Добавляет ID в настройки.
    *   `on_tree_collapsed(index: QModelIndex)`: Удаляет ID из настроек.
    *   `restore_tree_state()`: Применяет настройки к дереву после загрузки.

*   **Изменения в `load_collections`**:
    *   Вызов `restore_tree_state()` после заполнения модели.

### 3. Взаимодействие

1.  **Start/Load**: `MainWindow` -> `StorageManager` (load collections) -> `ConfigManager` (load settings) -> `QTreeView.expand(...)`.
2.  **User Action**: User clicks expand -> `QTreeView` emits `expanded` -> `MainWindow` updates `AppSettings` -> `ConfigManager.save_config`.

## Вопросы и ответы

*   **Q: Как быть, если ID коллекции в настройках есть, а самой коллекции уже нет?**
    *   A: `restore_tree_state` будет просто игнорировать ID, которых нет в модели. При следующем сохранении (если пользователь что-то свернет/развернет) список перезапишется актуальными данными (или можно делать очистку при загрузке, но проще "лениво" обновлять при сохранении).
*   **Q: Когда сохранять настройки?**
    *   A: Можно сохранять сразу при каждом клике (просто и надежно для desktop app с локальным конфигом).

