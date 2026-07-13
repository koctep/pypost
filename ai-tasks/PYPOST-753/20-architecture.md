# PYPOST-753: Architecture

`HTTPClient._read_response_body` tracks raw byte count per chunk. When
`max_response_bytes` exceeded, truncate final chunk, close response, append notice.
Setting flows: `AppSettings` → `TabsPresenter` → `RequestWorker` → `RequestService` →
`HTTPClient`.
