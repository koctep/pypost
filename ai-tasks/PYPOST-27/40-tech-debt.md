# PYPOST-27: Technical Debt Analysis

## Shortcuts Taken

- **Синхронная генерация метрик**: Метод `prometheus_client.generate_latest` вызывается синхронно внутри асинхронного хендлера `read_resource`. Хотя эта операция быстрая (работа в памяти), при очень большом количестве метрик это может кратковременно блокировать event loop.
- **Отсутствие конфигурации**: Имя сервера (`pypost-metrics`) и endpoint'ы жестко заданы в коде.

## Code Quality Issues

- **Дублирование логики запуска сервера**: Код запуска `uvicorn` в отдельном потоке в `MetricsManager` очень похож на аналогичный код в `MCPServerManager`. Имеет смысл в будущем вынести общую логику управления uvicorn-сервером в отдельный класс-утилиту.

## Missing Tests

- **Unit Tests**: Отсутствуют автоматические тесты для проверки корректности возвращаемых данных через MCP ресурс.
- **Integration Tests**: Нет тестов, проверяющих одновременную работу Prometheus endpoint и MCP SSE endpoint.

## Performance Concerns

- **Event Loop Overhead**: Использование `uvicorn` + `starlette` вместо простого `wsgiref` добавляет небольшой оверхед, но это оправдано функциональностью.

## Follow-up Tasks

- Создать абстракцию `UvicornThreadServer` для устранения дублирования кода между `MetricsManager` и `MCPServerManager`.
- Добавить тесты для проверки MCP ресурсов в `MetricsManager`.
