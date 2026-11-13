# Контейнерная проверка

Дата проверки 13 ноября 2026.

[Успешный прогон GitHub Actions](https://github.com/lesopylka/BigDataNiFi/actions/runs/43436292964).

На чистом Ubuntu runner собраны Docker-образы и запущены настоящие Kafka, PostgreSQL 16.6, NiFi 1.28.1 и Metabase 0.51.4.

- Оба init-файла PostgreSQL выполнены без ошибок.
- Поток NiFi создан через REST API, JSON передан через Kafka и записан в PostgreSQL.
- Проверены 10000 уникальных продаж, 54623 единицы товара и сумма 2529852.12.
- Топы, средние и временные показатели совпали с независимым расчетом по CSV.
- Повторная доставка довела Kafka log end offset до 20000. В PostgreSQL осталось 10000 продаж.
- Проверены Kafka offsets и пустые очереди NiFi, включая очередь failure.
- Создан Metabase dashboard из 22 карточек. Запрос каждой карточки выполнен через Metabase API со статусом completed и непустым результатом.

Исправлены чтение descriptors процессоров из config.descriptors и преобразование строкового queuedCount в число при проверке очередей.

Команды воспроизводятся из [.github/workflows/integration.yml](.github/workflows/integration.yml). Проверка Metabase подтверждает создание dashboard и выполнение запросов карточек, но не является проверкой внешнего вида графиков во всех браузерах.
