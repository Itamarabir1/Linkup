from enum import Enum

class DispatchTarget(str, Enum):
    """היעדים האפשריים להפצת אירועים - Domain Level"""
    RABBITMQ = "RABBITMQ"
    KAFKA = "KAFKA"
    WEBHOOK = "WEBHOOK"
    WEBSOCKET = "WEBSOCKET"
    REDIS= "REDIS"