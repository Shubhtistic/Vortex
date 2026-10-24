from enum import Enum


class EventSource(str, Enum):
    web = "web"
    ios = "ios"
    android = "android"
    server = "server"
    api = "api"
