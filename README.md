# Lolzteam Keeper

**Keeps your Lolzteam threads on top and your giveaways running — on a schedule, without you.**

A single asyncio process with two cron jobs: one bumps a fixed list of threads through the Lolzteam API, the other picks a random giveaway template from `contests.json` and publishes it. Configuration is one `.env` file and one JSON file; there is no database and nothing to back up.

<p>
  <img alt="Language Python 3.13" src="https://img.shields.io/badge/language-Python%203.13-3776AB?logo=python&logoColor=white">
  <img alt="Scheduler APScheduler" src="https://img.shields.io/badge/scheduler-APScheduler-4B8BBE">
  <img alt="Runtime Docker Compose v2" src="https://img.shields.io/badge/runtime-Docker%20Compose%20v2-2496ED?logo=docker&logoColor=white">
  <img alt="License MIT" src="https://img.shields.io/badge/license-MIT-3DA639?logo=opensourceinitiative&logoColor=white">
</p>

## How it works

Two jobs are registered on an `AsyncIOScheduler` running in `SCHEDULER_TIMEZONE` (default `Europe/Moscow`):

| Job              | Default schedule                             | What it does                                                                                  |
|------------------|----------------------------------------------|ч-----------------------------------------------------------------------------------------------|
| Thread bumping   | `08:00` and `20:00` daily                    | Walks `THREAD_TO_BUMP_IDS` in order, `POST /threads/{id}/bump`, pausing between each request. |
| Contest creation | `17:00` on the 1st, 8th, 15th, 22nd and 29th | Loads `contests.json`, picks one entry at random, `POST /contests`.                           |

The bumping job is registered only when `THREAD_TO_BUMP_IDS` is non-empty. Each job opens its own HTTP session and closes it when done, so nothing is held open between runs.

Every request is retried with exponential back-off on `429`, `5xx`, connection errors and timeouts (`tenacity`). A bump the forum rejects because the per-rights limit is reached is logged as a warning and **not** retried further — that is an expected outcome, not a failure. A single failing thread or contest never aborts the run; it is logged and the loop continues.

## Quick start

**1. Clone and create the config files.**

```bash
git clone https://github.com/Kartoshka2331/lolzteam-keeper.git
cd lolzteam-keeper
cp .env.example .env
cp contests.example.json contests.json
```

**2. Fill in `.env`.** The two required values are `API_TOKEN` (a Lolzteam API token) and `SECRET_ANSWER` (your account's secret answer, which the forum demands for contest creation).

**3. Write your giveaway templates** into `contests.json` (see below), or leave the example in place to try it out.

**4. Start it.**

```bash
docker compose up -d --build
docker compose logs -f
```

Both `.env` and `contests.json` are mounted read-only, so editing a template only needs `docker compose restart`.

## Running without Docker

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .
python3 -m main
```

Settings are read from the process environment first and from `.env` in the project root second — identical behaviour to the container.

## Contest templates

`contests.json` is a list of objects. `title` and `body` are required, `parameters` is optional and every key inside it falls back to its default. `body` is BB-code, exactly as the forum editor produces it.

```json
[
  {
    "title": "Заголовок темы",
    "body": "[CENTER]Текст розыгрыша в BB-code разметке.[/CENTER]",
    "parameters": {
      "prize_data_money": 500,
      "count_winners": 1,
      "length_value": 3
    }
  }
]
```

| Parameter                  | Default          | Description                                                   |
|----------------------------|------------------|---------------------------------------------------------------|
| `contest_type`             | `by_finish_date` | The only value the API accepts.                               |
| `length_value`             | `3`              | Duration, in units of `length_option`.                        |
| `length_option`            | `days`           | `minutes`, `hours` or `days`. Three days is the hard maximum. |
| `prize_type`               | `money`          | `money` or `upgrades`.                                        |
| `count_winners`            | `1`              | Number of winners, `1`–`100`.                                 |
| `prize_data_money`         | `500`            | Payout **per winner**.                                        |
| `require_like_count`       | `1`              | Minimum sympathies the participant earned this week.          |
| `require_total_like_count` | `200`            | Minimum sympathies the participant earned for all time.       |
| `tags`                     | `""`             | Comma-separated thread tags.                                  |

A malformed or missing file is logged and the run is skipped — the scheduler stays up.

## Configuration reference

| Variable                       | Default                         | Description                                                                  |
|--------------------------------|---------------------------------|------------------------------------------------------------------------------|
| `API_TOKEN`                    | —                               | **Required.** Lolzteam API token.                                            |
| `SECRET_ANSWER`                | —                               | **Required.** Account secret answer, needed to create contests.              |
| `API_BASE_URL`                 | `https://prod-api.zelenka.guru` | API root.                                                                    |
| `API_REQUEST_TIMEOUT_SECONDS`  | `30.0`                          | Total per-request timeout.                                                   |
| `THREAD_TO_BUMP_IDS`           | empty                           | Comma-separated thread ids, e.g. `10298734,7388873`. Empty disables the job. |
| `THREAD_BUMP_DELAY_SECONDS`    | `3.0`                           | Pause between consecutive bumps.                                             |
| `THREAD_BUMP_CRON_HOUR`        | `8,20`                          | Cron hour field for bumping.                                                 |
| `THREAD_BUMP_CRON_MINUTE`      | `0`                             | Cron minute field for bumping.                                               |
| `CONTESTS_CONFIG_PATH`         | `contests.json`                 | Path to the templates file.                                                  |
| `CONTEST_CREATION_CRON_DAY`    | `*/7`                           | Cron day field for contest creation.                                         |
| `CONTEST_CREATION_CRON_HOUR`   | `17`                            | Cron hour field for contest creation.                                        |
| `CONTEST_CREATION_CRON_MINUTE` | `0`                             | Cron minute field for contest creation.                                      |
| `RETRY_MAX_ATTEMPTS`           | `3`                             | Attempts per request before giving up.                                       |
| `RETRY_WAIT_MIN_SECONDS`       | `4.0`                           | Lower bound of the back-off.                                                 |
| `RETRY_WAIT_MAX_SECONDS`       | `10.0`                          | Upper bound of the back-off.                                                 |
| `RETRY_WAIT_MULTIPLIER`        | `1.0`                           | Exponential back-off multiplier.                                             |
| `SCHEDULER_TIMEZONE`           | `Europe/Moscow`                 | Timezone every cron expression is evaluated in.                              |
| `LOG_LEVEL`                    | `INFO`                          | Loguru level.                                                                |

## Troubleshooting

| Symptom                             | Cause and fix                                                                                                       |
|-------------------------------------|---------------------------------------------------------------------------------------------------------------------|
| `ValidationError` at startup        | `.env` is missing, or `API_TOKEN` / `SECRET_ANSWER` are not set.                                                    |
| `Bump limit reached for thread …`   | The forum's per-rights bump interval has not elapsed. Expected — widen `THREAD_BUMP_CRON_HOUR` if it repeats daily. |
| `No threads configured for bumping` | `THREAD_TO_BUMP_IDS` is empty, so the job was never scheduled.                                                      |
| `Contests config file not found`    | `contests.json` was never created from the example, or `CONTESTS_CONFIG_PATH` points elsewhere.                     |
| Nothing fires at the expected time  | Cron fields are evaluated in `SCHEDULER_TIMEZONE`, not the host clock.                                              |
| An `.env` edit had no effect        | `docker compose restart` keeps the old environment. Run `docker compose up -d` to recreate the container.           |