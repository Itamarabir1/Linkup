# סכמת מבנה הפרויקט – Linkup

מסמך זה מכיל את כל התיקיות, תתי־התיקיות והקבצים בפרויקט (למעט תוכן `node_modules` ו־`.venv` שהם תלויות חיצוניות).

---

## שורש הפרויקט (Linkup/)

```
Linkup/
├── .git/                          # מאגר Git
├── .github/
│   └── workflows/                 # CI/CD
│       ├── backend-ci.yml
│       ├── chat-ws-ci.yml
│       └── frontend-ci.yml
├── .vscode/
│   └── settings.json
├── .gitignore
├── docker-compose.yml
├── docker-compose.override.yml.example   # template; copy to docker-compose.override.yml (in .gitignore)
├── k8s/                           # הגדרות Kubernetes
│   ├── base/
│   ├── backend/
│   ├── chat-ws/
│   ├── frontend/
│   └── infra/
├── README.md
├── render.yaml
├── RUN.md
├── backend/
├── chat-ws/
├── db/
├── docs/
├── frontend/
└── mobile/
```

---

## backend/

```
backend/
├── .env
├── .env.example
├── .pytest_cache/                 # cache של pytest (לא חלק מקוד המקור)
│   ├── .gitignore
│   ├── CACHEDIR.TAG
│   ├── README.md
│   └── v/cache/nodeids
├── alembic.ini
├── celerybeat-schedule
├── Dockerfile
├── Makefile
├── .dockerignore
├── requirements.txt
├── README.md
├── run-backend.bat
├── run-backend.sh
├── alembic/
│   ├── env.py
│   ├── README.md
│   ├── script.py.mako
│   └── versions/
│       ├── add_refresh_token_to_users.py
│       ├── add_ride_distance_duration_columns.py
│       ├── add_route_summary_to_rides.py
│       └── normalize_ride_status_enum.py
├── app/
│   ├── __init__.py
│   ├── admin_config.py
│   ├── main.py
│   ├── admin/
│   │   └── setup.py
│   ├── api/
│   │   ├── dependencies/
│   │   │   ├── auth.py
│   │   │   ├── file.py
│   │   │   └── rate_limit.py
│   │   ├── v1/
│   │   │   ├── api_router.py
│   │   │   └── routers/
│   │   │       ├── __init__.py
│   │   │       ├── auth.py
│   │   │       ├── bookings.py
│   │   │       ├── chat.py
│   │   │       ├── geo.py
│   │   │       ├── passengers.py
│   │   │       ├── rides.py
│   │   │       └── users.py
│   │   └── websockets/
│   │       └── notifications.py
│   ├── core/
│   │   ├── config.py
│   │   ├── lifespan.py
│   │   ├── security.py
│   │   ├── exceptions/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── base.py
│   │   │   ├── base_user.py
│   │   │   ├── booking.py
│   │   │   ├── handlers.py
│   │   │   ├── infrastructure.py
│   │   │   ├── notification.py
│   │   │   ├── passenger.py
│   │   │   ├── ride.py
│   │   │   ├── user.py
│   │   │   └── validation.py
│   │   ├── middleware/
│   │   │   ├── __init__.py
│   │   │   ├── https_redirect.py
│   │   │   └── security_headers.py
│   │   └── utils/
│   │       └── validators.py
│   ├── db/
│   │   ├── base.py
│   │   ├── models.py
│   │   └── session.py
│   ├── domain/
│   │   ├── auth/
│   │   │   ├── google_auth.py
│   │   │   ├── schema.py
│   │   │   ├── service.py
│   │   │   └── verification_service.py
│   │   ├── bookings/
│   │   │   ├── crud.py
│   │   │   ├── enum.py
│   │   │   ├── model.py
│   │   │   ├── schema.py
│   │   │   └── service.py
│   │   ├── chat/
│   │   │   ├── __init__.py
│   │   │   ├── ai/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── analyzer.py
│   │   │   │   ├── analysis.py
│   │   │   │   ├── client.py
│   │   │   │   ├── crud.py
│   │   │   │   ├── prompts.py
│   │   │   │   └── schema.py
│   │   │   ├── calendar_export.py
│   │   │   ├── completion/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── detector.py
│   │   │   │   └── service.py
│   │   │   ├── crud.py
│   │   │   ├── model.py
│   │   │   ├── schema.py
│   │   │   ├── service.py
│   │   │   └── calendar/
│   │   │       ├── __init__.py
│   │   │       ├── builder.py
│   │   │       ├── event.py
│   │   │       ├── exporter.py
│   │   │       └── time_parser.py
│   │   ├── events/
│   │   │   ├── enum.py
│   │   │   ├── model.py
│   │   │   ├── outbox.py
│   │   │   ├── routing.py
│   │   │   └── schema.py
│   │   ├── geo/
│   │   │   ├── processor.py
│   │   │   ├── schema.py
│   │   │   ├── mixins.py
│   │   │   └── utils.py
│   │   ├── notifications/
│   │   │   ├── constants.py
│   │   │   ├── manager.py
│   │   │   ├── channels/
│   │   │   │   ├── email/
│   │   │   │   │   ├── __init__.py
│   │   │   │   │   ├── client.py
│   │   │   │   │   ├── renderer.py
│   │   │   │   │   └── templates/
│   │   │   │   │       ├── chat/
│   │   │   │   │       │   └── conversation_summary.html
│   │   │   │   │       ├── driver/
│   │   │   │   │       │   ├── new_ride_request.html
│   │   │   │   │       │   ├── passenger_cancelled.html
│   │   │   │   │       │   └── ride_reminder_driver.html
│   │   │   │   │       ├── passenger/
│   │   │   │   │       │   ├── booking_approved.html
│   │   │   │   │       │   ├── booking_rejected.html
│   │   │   │   │       │   ├── ride_cancelled_by_driver.html
│   │   │   │   │       │   ├── ride_reminder_passenger.html
│   │   │   │   │       │   └── ride_created_for_passengers.html
│   │   │   │   │       └── user/
│   │   │   │   │           ├── password_reset.html
│   │   │   │   │           ├── verify_email.html
│   │   │   │   │           └── welcome.html
│   │   │   │   └── push/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── client.py
│   │   │   │       └── render.py
│   │   │   ├── config/
│   │   │   │   ├── mappings.py
│   │   │   │   └── templates_map/
│   │   │   │       ├── __init__.py
│   │   │   │       ├── email_conf.py
│   │   │   │       └── push_conf.py
│   │   │   ├── core/
│   │   │   │   ├── facade.py
│   │   │   │   ├── handler.py
│   │   │   │   ├── resolver.py
│   │   │   │   └── builders/
│   │   │   │       ├── base.py
│   │   │   │       ├── booking_builder.py
│   │   │   │       ├── chat_builder.py
│   │   │   │       ├── registry.py
│   │   │   │       ├── ride_builder.py
│   │   │   │       └── user_builder.py
│   │   │   ├── providers/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py
│   │   │   │   ├── email_provider.py
│   │   │   │   ├── push_provider.py
│   │   │   │   └── websocket_provider.py
│   │   │   └── services/
│   │   │       ├── notification_streamer.py
│   │   │       ├── orchestrator.py
│   │   │       └── reminder_scheduler.py
│   │   ├── passengers/
│   │   │   ├── crud.py
│   │   │   ├── enum.py
│   │   │   ├── model.py
│   │   │   ├── schema.py
│   │   │   └── service.py
│   │   ├── rides/
│   │   │   ├── actions.py
│   │   │   ├── cleanup.py
│   │   │   ├── crud.py
│   │   │   ├── enum.py
│   │   │   ├── logic.py
│   │   │   ├── mapper.py
│   │   │   ├── model.py
│   │   │   ├── broadcast.py
│   │   │   ├── repository.py
│   │   │   ├── schema.py
│   │   │   └── service.py
│   │   ├── system/
│   │   │   ├── maintenance_crud.py
│   │   │   ├── maintenance_service.py
│   │   │   └── outbox_service.py
│   │   └── users/
│   │       ├── __init__.py
│   │       ├── crud.py
│   │       ├── model.py
│   │       ├── schema.py
│   │       └── service.py
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── websocket_bus.py
│   │   ├── events/
│   │   │   ├── dispatcher/
│   │   │   │   ├── base.py
│   │   │   │   ├── evaluator.py
│   │   │   │   └── factory.py
│   │   │   └── publishers/
│   │   │       ├── base.py
│   │   │       ├── rabbitmq.py
│   │   │       ├── redis.py
│   │   │       └── websocket.py
│   │   ├── firebase_core/
│   │   │   ├── firebase-credentials.example.json
│   │   │   ├── firebase-credentials.json   # local only, in .gitignore
│   │   │   └── firebase.py
│   │   ├── geo/
│   │   │   ├── client.py
│   │   │   └── utils.py
│   │   ├── outbox/
│   │   │   ├── enum.py
│   │   │   ├── model.py
│   │   │   └── repository.py
│   │   ├── rabbitmq/
│   │   │   ├── client.py
│   │   │   └── consumer.py
│   │   ├── redis/
│   │   │   ├── __init__.py
│   │   │   ├── broadcast.py
│   │   │   ├── chat_completion_publish.py
│   │   │   ├── client.py
│   │   │   ├── keys.py
│   │   │   └── pubsub.py
│   │   └── s3/
│   │       ├── client.py
│   │       └── service.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── location/
│   │       ├── __init__.py
│   │       ├── geocoding.py
│   │       ├── location_service.py
│   │       └── routing.py
│   └── workers/
│       ├── main_worker.py
│       ├── outbox_worker.py
│       └── tasks/
│           ├── avatar_tasks.py
│           ├── chat_summary_task.py
│           ├── chat_timeout_task.py
│           ├── fuel_price_task.py
│           ├── maintenance_task.py
│           ├── notification_tasks.py
│           ├── ride_task.py
│           └── scheduled_tasks.py
└── tests/
    ├── __init__.py
    └── test_security.py
```

---

## chat-ws/

```
chat-ws/
├── .dockerignore
├── .env.example
├── .gitignore
├── ARCHITECTURE.md
├── Dockerfile
├── go.mod
├── Makefile
├── README.md
├── cmd/
│   └── server/
│       └── main.go
├── internal/
│   ├── auth/
│   │   └── jwt.go
│   ├── config/
│   │   └── config.go
│   ├── hub/
│   │   ├── conn.go
│   │   ├── handler.go
│   │   ├── hub.go
│   │   └── message.go
│   └── redis/
│       └── subscriber.go
```

---

## db/

```
db/
├── schema.sql
├── scripts/
│   └── check_match_distance.sql
```

---

## docs/

```
docs/
├── ARCHITECTURE.md
└── HTTPS_SETUP.md
```

---

## frontend/

```
frontend/
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── eslint.config.js
├── index.html
├── nginx.conf
├── package-lock.json
├── package.json
├── README.md
├── tsconfig.app.json
├── tsconfig.json
├── tsconfig.node.json
├── vite.config.ts
├── dist/                          # build output (לא ב-Git)
├── node_modules/                  # תלויות npm (לא מפורט)
├── public/
│   └── vite.svg
└── src/
    ├── App.css
    ├── App.tsx
    ├── index.css
    ├── main.tsx
    ├── api/
    │   └── client.ts
    ├── assets/
    │   └── react.svg
    ├── components/
    │   ├── Layout/
    │   │   ├── index.tsx
    │   │   └── Layout.module.css
    │   ├── RouteMapModal/
    │   │   ├── index.tsx
    │   │   └── RouteMapModal.module.css
    │   ├── GoogleSignIn.tsx
    ├── config/
    │   └── env.ts
    ├── context/
    │   └── AuthContext.tsx
    ├── pages/
    │   ├── CreateRide.module.css
    │   ├── CreateRide.tsx
    │   ├── Login.module.css
    │   ├── Login.tsx
    │   ├── Messages.module.css
    │   ├── Messages.tsx
    │   ├── MessageThread.module.css
    │   ├── MessageThread.tsx
    │   ├── MyBookings.module.css
    │   ├── MyBookings.tsx
    │   ├── MyRequests.module.css
    │   ├── MyRequests.tsx
    │   ├── MyRides.module.css
    │   ├── MyRides.tsx
    │   ├── Notifications.module.css
    │   ├── Notifications.tsx
    │   ├── Profile.module.css
    │   ├── Profile.tsx
    │   ├── Register.module.css
    │   ├── Register.tsx
    │   ├── SearchRides.module.css
    │   ├── SearchRides.tsx
    │   ├── VerifyEmail.module.css
    │   └── VerifyEmail.tsx
    ├── types/
    │   ├── api.ts
    │   └── google-maps.d.ts
    └── utils/
        ├── date.ts
        └── duration.ts
```

---

## mobile/

```
mobile/
├── .env.example
├── .gitignore
├── app.json
├── App.tsx
├── index.ts
├── package-lock.json
├── package.json
├── README.md
├── tsconfig.json
├── assets/
│   ├── adaptive-icon.png
│   ├── favicon.png
│   ├── icon.png
│   └── splash-icon.png
├── node_modules/                  # תלויות npm (לא מפורט)
└── src/
    ├── api/
    │   └── client.ts
    ├── config/
    │   └── env.ts
    ├── context/
    │   └── AuthContext.tsx
    ├── hooks/
    │   └── useGeo.ts
    ├── navigation/
    │   └── AppNavigator.tsx
    ├── screens/
    │   ├── CreateRideScreen.tsx
    │   ├── LoginScreen.tsx
    │   ├── MyRequestsScreen.tsx
    │   ├── MyRidesScreen.tsx
    │   ├── ProfileScreen.tsx
    │   ├── RegisterScreen.tsx
    │   └── SearchRidesScreen.tsx
    └── types/
        └── api.ts
```

---

## .github/workflows/

```
.github/
└── workflows/
    ├── backend-ci.yml
    ├── chat-ws-ci.yml
    └── frontend-ci.yml
```

---

## k8s/

```
k8s/
├── base/
│   ├── namespace.yaml
│   └── kustomization.yaml
├── backend/
│   ├── configmap.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── chat-ws/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
├── frontend/
│   ├── deployment.yaml
│   ├── service.yaml
│   └── kustomization.yaml
└── infra/
    ├── configmap.yaml
    ├── postgres.yaml
    ├── redis.yaml
    ├── rabbitmq.yaml
    └── kustomization.yaml
```

---

## הערות

- **backend**: שרת API ב‑Python (FastAPI), עם Alembic למיגרציות, workers, ותשתיות (Redis, RabbitMQ, S3, Firebase).
- **chat-ws**: שרת WebSocket ב‑Go בלבד. אחראי על העברת הודעות בזמן אמת בין משתמשים.
- **db**: סכמה (schema.sql) וסקריפטים שימושיים; מיגרציות ב-backend/alembic/.
- **frontend**: אפליקציית ווב ב‑React + TypeScript + Vite.
- **mobile**: אפליקציית מובייל (Expo/React Native) ב‑TypeScript.
- **.github/workflows**: CI/CD ל‑backend (Python), chat-ws (Go), frontend (React).
- **k8s**: הגדרות Kubernetes (base, backend, chat-ws, frontend, infra).
- **node_modules** (ב‑frontend ו‑mobile) ו־**.venv** (בסביבות Python) לא פורטו – אלה תלויות שנוצרות בהתקנה.
- קבצי **.env** לא נכללו בתיאור מפורש מטעמי אבטחה; הם קיימים לפי .env.example.

*מסמך זה נוצר אוטומטית לפי מבנה התיקיות בפרויקט.*
