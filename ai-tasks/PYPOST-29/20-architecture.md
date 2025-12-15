# PYPOST-29: Fix "Sending..." stuck on Transfer-Encoding: chunked

## Исследования

Проблема заключается в том, что стандартный вызов `requests.request()` с `stream=True` и последующее чтение `response.text` приводят к зависанию при работе с бесконечными потоками (например, SSE - Server-Sent Events). `requests` пытается вычитать весь поток до конца, которого может и не быть.

Для полноценного решения проблемы (включая поддержку SSE) необходимо переходить к потоковой обработке данных (streaming) во всей цепочке от `HTTPClient` до UI.

## План реализации

### 1. Изменения в архитектуре (Streaming)

#### Data Flow
1.  **`HTTPClient`**: Изменяется для поддержки механизма callback'ов. Вместо возврата полного тела ответа сразу, он будет читать ответ чанками (`response.iter_content()`) и вызывать callback для каждого чанка.
2.  **`RequestWorker`**: Предоставляет callback для `HTTPClient`, который эмитирует новый сигнал `chunk_received` в поток UI.
3.  **UI Layer**:
    -   `RequestTab`: Подписывается на сигнал `chunk_received` и обновляет `ResponseView`.
    -   `ResponseView`: Добавляет методы для инкрементального добавления текста.
    -   `RequestWidget`: Обновляет логику кнопки "Send" для поддержки "Cancel/Stop".

### 2. Этапы реализации

#### 2.1: Core Logic (Streaming)
-   **`pypost/core/http_client.py`**:
    -   Обновить `send_request` для приема опционального `stream_callback`.
    -   Реализовать цикл чтения `response.iter_content()`.
    -   Вызывать `stream_callback(chunk)` внутри цикла.
    -   Добавить проверку условия остановки (cancellation).
-   **`pypost/core/request_service.py`**:
    -   Пробрасывать `stream_callback` в `http_client`.
-   **`pypost/core/worker.py`**:
    -   Добавить сигнал `chunk_received = Signal(str)`.
    -   Передавать callback, эмитирующий этот сигнал, в `service.execute`.

#### 2.2: UI Updates (Display)
-   **`pypost/ui/widgets/response_view.py`**:
    -   Добавить метод `append_body(text)`.
    -   Добавить метод `clear_body()`.
-   **`pypost/ui/main_window.py`**:
    -   Подключить `worker.chunk_received` к слоту обновления UI.
    -   Реализовать логику кнопки "Stop/Cancel".

## Архитектура

### Модуль `pypost.core.http_client`

**Новый интерфейс:**
```python
def send_request(self, request_data: RequestData, variables: Dict[str, str] = None, stream_callback: Callable[[str], None] = None, stop_flag: Callable[[], bool] = None) -> ResponseData:
    # ...
    response = self.session.request(..., stream=True)
    
    content_parts = []
    for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
        if stop_flag and stop_flag():
             break
        if chunk:
            content_parts.append(chunk)
            if stream_callback:
                stream_callback(chunk)
                
    full_body = "".join(content_parts)
    return ResponseData(..., body=full_body, ...)
```

## Вопросы и ответы

**В:** Что делать с форматированием JSON при стриминге?
**О:** Во время стриминга отображаем сырой текст. По завершении запроса, если получен валидный JSON, форматируем его как обычно.

**В:** Как прервать запрос?
**О:** `RequestWorker` будет иметь флаг остановки, который проверяется в цикле чтения чанков в `HTTPClient`.


