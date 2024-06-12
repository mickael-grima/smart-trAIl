FROM golang:1.22 as build-stage

ENV APP_HOME /app

WORKDIR "$APP_HOME"
COPY go.mod go.sum ./
RUN go mod download

COPY *.go ./
COPY database/*.go ./database/

RUN go mod download
RUN go mod verify
RUN GO_ENABLED=0 GOOS=linux go build -o server

# Run the tests in the container
FROM build-stage AS run-test-stage
RUN go test -v ./...

FROM gcr.io/distroless/base-debian12 AS build-release-stage

ENV APP_HOME /app
WORKDIR "$APP_HOME"

COPY --from=build-stage "$APP_HOME"/server $APP_HOME

EXPOSE 8080
CMD ["./server"]