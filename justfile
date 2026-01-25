alias r := run
alias s := stop
alias d := down
alias m := migrate
alias mm := makemigrations
alias mmm := makemigrations_and_migrate 

DB_HOST := env_var("POSTGRES_HOST")
DB_PORT := env_var("POSTGRES_PORT")
POSTGRES_USER := env_var("POSTGRES_USER")
POSTGRES_PASSWORD := env_var("POSTGRES_PASSWORD")
POSTGRES_DB := env_var("POSTGRES_DB")

DUMPS_DIR := env_var("DUMPS_DIR")
DUMP_NAME := env_var("DUMP_NAME")
DUMP_PATH := env_var("DUMPS_DIR")/env_var("DUMP_NAME")
BROWSER_PATH := env_var("BROWSER_PATH")

run:
   docker compose up -d postgres
   ./manage.py runserver

up *args:
   docker compose up {{args}}

down: 
   docker compose down

stop:
    docker stop $(docker ps -aq)

rebuild:
   docker compose up --build

makemigrations *args:
   ./manage.py makemigrations {{args}}
    
migrate *args:
   ./manage.py migrate {{args}}

makemigrations_and_migrate:
   ./manage.py makemigrations && ./manage.py migrate 

add_pg_history_model *args:
   ./manage.py add_pg_history_model {{args}}

repo:
    repomix -i "**/migrations/**" -o back.txt && dragon -a -x "back.txt"

dump:
    mkdir -p "{{DUMPS_DIR}}"
    docker compose exec -T postgres env PGPASSWORD="{{POSTGRES_PASSWORD}}" pg_dump -Fc --no-owner -U "{{POSTGRES_USER}}" "{{POSTGRES_DB}}" -v > "{{DUMPS_DIR}}/local-$(date +%Y-%m-%d-%H-%M)-dump.sql"

reinstall_db:
    ls {{DUMP_PATH}}
    docker compose down --volumes
    docker compose up -d postgres
    sleep 2
    cat "{{DUMP_PATH}}" | docker compose exec -T postgres sh -c 'PGPASSWORD="$POSTGRES_PASSWORD" pg_restore --no-owner -U "$POSTGRES_USER" -d "$POSTGRES_DB" -1 --clean --if-exists --single-transaction'
    PGPASSWORD={{POSTGRES_PASSWORD}} psql -U {{POSTGRES_USER}} -h {{DB_HOST}} -d {{POSTGRES_DB}} -c "update mailings_mailing set status = 'STOPPED'";

    {{BROWSER_PATH}} --new-window "http://127.0.0.1:8000/api/admin/"
    bash -c "python ./manage.py migrate"
    docker compose up -d postgres
