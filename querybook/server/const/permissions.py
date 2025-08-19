from enum import Enum


class Permission(Enum):
    READ = "read"
    EXECUTE = "execute"
    WRITE = "write"
