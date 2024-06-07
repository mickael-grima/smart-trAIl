# Trail Running Scrapers

This project is about getting trail running competitions data
from different providers, storing those data into a database,
and serving them through a web-server, providing enriching
functionalities.

## Database

We use a SQL database for this project. The tables are described as following:

#### Competitions

| Field      | Type         | Null | Key | Default | Extra          |
|------------|--------------|------|-----|---------|----------------|
| id         | int          | NO   | PRI | NULL    | auto_increment |
| name       | varchar(255) | NO   | MUL | NULL    |                |
| timekeeper | varchar(50)  | NO   |     | NULL    |                |

#### CompetitionEvents

| Field          | Type              | Null | Key | Default | Extra          |
|----------------|-------------------|------|-----|---------|----------------|
| id             | int               | NO   | PRI | NULL    | auto_increment |
| name           | varchar(255)      | NO   | MUL | NULL    |                |
| start_date     | date              | NO   |     | NULL    |                |
| end_date       | date              | YES  |     | NULL    |                |
| distance       | smallint unsigned | NO   |     | NULL    |                |
| competition_id | int               | NO   | MUL | NULL    |                |

`competition_id` references `competitions.id`

#### Runners

| Field      | Type         | Null | Key | Default | Extra          |
|------------|--------------|------|-----|---------|----------------|
| id         | int          | NO   | PRI | NULL    | auto_increment |
| first_name | varchar(255) | NO   | MUL | NULL    |                |
| last_name  | varchar(255) | NO   |     | NULL    |                |
| birth_year | year         | YES  |     | NULL    |                |
| gender     | char(1)      | NO   |     | NULL    |                |

#### Results

| Field            | Type              | Null | Key | Default | Extra |
|------------------|-------------------|------|-----|---------|-------|
| runner_id        | int               | NO   | PRI | NULL    |       |
| event_id         | int               | NO   | PRI | NULL    |       |
| status           | varchar(20)       | NO   |     | NULL    |       |
| time             | time              | YES  |     | NULL    |       |
| license          | varchar(255)      | YES  |     | NULL    |       |
| category         | varchar(20)       | YES  |     | NULL    |       |
| scratch_ranking  | smallint unsigned | YES  |     | NULL    |       |
| gender_ranking   | smallint unsigned | YES  |     | NULL    |       |
| category_ranking | smallint unsigned | YES  |     | NULL    |       |

`runner_id` references `runners.id`  
`event_id` references `competitionEvents.id`

## Collector

The collector is a python service in charge of scraping data from
different websites:

- competitions
- competitions' events
- runners
- competitions' results

Those data are then stored into a MySQL database.

### Timekeepers

The supported timekeepers websites are:

- http://www.sportpro.re

### How to run it?

#### prerequisites

1. This service is dockerize: we should install docker first.
2. Make sure you have a MySQL DB running. If it runs on your local,
   its address will be `host.docker.internal`. Otherwise use the one
   wanted.
3. Build the docker container:

```commandline
docker build -t collector .
```

4. Create your environment file `.env`:

```dotenv
MYSQL_ADDRESS=
MYSQL_USERNAME=
MYSQL_PASSWORD=
MYSQL_DBNAME=
```

5. Run the container:

```commandline
docker --env-file .env -t collector
```

## Server

The `server` service acts as an entrypoint for any client willing to get data from the database. It is built
as a RESTFull API

### Endpoints

| Method | Path                    | Parameters            | Description                                                                                                             |
|--------|-------------------------|-----------------------|-------------------------------------------------------------------------------------------------------------------------|
| `GET`  | `/runners/search`       | `q`: the search query | Returns all the runners matching the given query                                                                        |
| `GET`  | `/runners/<id>`         | `id`: the runner's id | Returns the runner corresponding to the id. 404 is returned if None                                                     |
| `GET`  | `/runners/<id>/results` | `id`: the runner's id | Returns the list of results of the runner corresponding to the id. 404 is returned if no runner corresponding to the id |
| `GET`  | `/events/search`        | `q`: the search query | Returns all events corresponding to the search query                                                                    |
| `GET`  | `/events/<id>`          | `id`: the event's id  | Return the event corresponding to the id. 404 is returned if no event                                                   |
| `GET`  | `/events/<id>/results`  | `id`: the event's id  | Returns the list of results of the event corresponding to the id. 404 is returned if no event corresponding to the id   |
