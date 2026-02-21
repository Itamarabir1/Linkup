# ===================================
# app/infrastructure/kafka/producer.py
# Kafka Producer - Enterprise Grade
# ===================================

import logging
import json
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError, KafkaTimeoutError
from kafka.errors import KafkaConnectionError

logger = logging.getLogger(__name__)


# ===================================
# Configuration
# ===================================

@dataclass
class KafkaProducerConfig:
    """
    Kafka Producer Configuration
    
    Best Practices:
    - acks='all': Wait for all replicas (durability)
    - compression_type='gzip': Reduce bandwidth
    - max_in_flight_requests_per_connection=5: Balance throughput/ordering
    - retries=10: Auto-retry on transient failures
    """
    bootstrap_servers: list[str]
    client_id: str = "linkup-producer"
    
    # Reliability
    acks: str = "all"  # Wait for all in-sync replicas
    retries: int = 10
    max_in_flight_requests_per_connection: int = 5
    
    # Performance
    compression_type: str = "gzip"
    batch_size: int = 16384  # 16KB
    linger_ms: int = 10  # Wait 10ms to batch messages
    
    # Timeouts
    request_timeout_ms: int = 30000  # 30 seconds
    
    # Security (optional)
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    
    def to_kafka_config(self) -> Dict[str, Any]:
        """Convert to aiokafka config dict"""
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "client_id": self.client_id,
            "acks": self.acks,
            "retries": self.retries,
            "max_in_flight_requests_per_connection": self.max_in_flight_requests_per_connection,
            "compression_type": self.compression_type,
            "batch_size": self.batch_size,
            "linger_ms": self.linger_ms,
            "request_timeout_ms": self.request_timeout_ms,
            "security_protocol": self.security_protocol,
            # Serialization
            "value_serializer": lambda v: json.dumps(v).encode('utf-8'),
            "key_serializer": lambda k: k.encode('utf-8') if k else None,
        }
        
        # Add SASL if configured
        if self.sasl_mechanism:
            config["sasl_mechanism"] = self.sasl_mechanism
            config["sasl_plain_username"] = self.sasl_username
            config["sasl_plain_password"] = self.sasl_password
        
        return config


# ===================================
# Kafka Producer
# ===================================

class KafkaProducer:
    """
    Enterprise-grade Kafka Producer
    
    Features:
    - Async/await support
    - Automatic retries
    - Connection pooling
    - Error handling
    - Monitoring hooks
    - Graceful shutdown
    
    Design Patterns:
    - Singleton (one producer per application)
    - Builder (configuration)
    - Observer (callbacks for monitoring)
    """
    
    def __init__(self, config: KafkaProducerConfig):
        self._config = config
        self._producer: Optional[AIOKafkaProducer] = None
        self._is_connected = False
        
        # Monitoring
        self._send_success_count = 0
        self._send_failure_count = 0
        self._on_success_callback: Optional[Callable] = None
        self._on_failure_callback: Optional[Callable] = None
    
    async def connect(self):
        """
        Initialize connection to Kafka cluster
        
        Should be called once during app startup
        """
        if self._is_connected:
            logger.warning("Kafka producer already connected")
            return
        
        try:
            self._producer = AIOKafkaProducer(**self._config.to_kafka_config())
            await self._producer.start()
            self._is_connected = True
            logger.info(f"✅ Kafka producer connected to {self._config.bootstrap_servers}")
            
        except Exception as e:
            logger.error(f"❌ Failed to connect Kafka producer: {e}")
            raise
    
    async def disconnect(self):
        """
        Close connection to Kafka cluster
        
        Should be called during app shutdown
        """
        if not self._is_connected or not self._producer:
            return
        
        try:
            await self._producer.stop()
            self._is_connected = False
            logger.info("✅ Kafka producer disconnected")
            
        except Exception as e:
            logger.error(f"❌ Error disconnecting Kafka producer: {e}")
    
    async def send_event(
        self,
        topic: str,
        value: Dict[str, Any],
        key: Optional[str] = None,
        partition: Optional[int] = None,
        timestamp_ms: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send event to Kafka topic
        
        Args:
            topic: Kafka topic name
            value: Event data (will be JSON serialized)
            key: Partition key (optional)
            partition: Specific partition (optional)
            timestamp_ms: Event timestamp (optional)
            headers: Message headers (optional)
            
        Returns:
            bool: True if sent successfully, False otherwise
            
        Example:
            await producer.send_event(
                topic="user_events",
                value={"user_id": 123, "action": "login"},
                key="user_123",
                headers={"source": "api"}
            )
        """
        if not self._is_connected or not self._producer:
            logger.error("❌ Kafka producer not connected")
            return False
        
        try:
            # Add metadata
            enriched_value = {
                **value,
                "_metadata": {
                    "timestamp": timestamp_ms or int(datetime.now().timestamp() * 1000),
                    "producer": self._config.client_id,
                    "version": value.get("version", "1.0")
                }
            }
            
            # Convert headers to bytes
            kafka_headers = None
            if headers:
                kafka_headers = [
                    (k, v.encode('utf-8') if isinstance(v, str) else v)
                    for k, v in headers.items()
                ]
            
            # Send to Kafka
            result = await self._producer.send_and_wait(
                topic=topic,
                value=enriched_value,
                key=key,
                partition=partition,
                timestamp_ms=timestamp_ms,
                headers=kafka_headers
            )
            
            # Success
            self._send_success_count += 1
            logger.debug(
                f"✅ Kafka: Sent to {topic} "
                f"(partition={result.partition}, offset={result.offset})"
            )
            
            # Callback
            if self._on_success_callback:
                await self._on_success_callback(topic, enriched_value, result)
            
            return True
            
        except KafkaTimeoutError as e:
            self._send_failure_count += 1
            logger.warning(f"⚠️ Kafka timeout for topic {topic}: {e}")
            
            if self._on_failure_callback:
                await self._on_failure_callback(topic, value, e)
            
            return False
            
        except KafkaConnectionError as e:
            self._send_failure_count += 1
            logger.error(f"❌ Kafka connection error for topic {topic}: {e}")
            
            if self._on_failure_callback:
                await self._on_failure_callback(topic, value, e)
            
            return False
            
        except Exception as e:
            self._send_failure_count += 1
            logger.error(f"❌ Kafka send error for topic {topic}: {e}", exc_info=True)
            
            if self._on_failure_callback:
                await self._on_failure_callback(topic, value, e)
            
            return False
    
    def set_success_callback(self, callback: Callable):
        """
        Set callback for successful sends (for monitoring)
        
        Example:
            async def on_success(topic, value, result):
                metrics.increment("kafka.send.success", tags=[f"topic:{topic}"])
            
            producer.set_success_callback(on_success)
        """
        self._on_success_callback = callback
    
    def set_failure_callback(self, callback: Callable):
        """Set callback for failed sends (for monitoring)"""
        self._on_failure_callback = callback
    
    def get_metrics(self) -> Dict[str, int]:
        """Get producer metrics"""
        return {
            "send_success_count": self._send_success_count,
            "send_failure_count": self._send_failure_count,
            "is_connected": self._is_connected
        }
    
    @property
    def is_connected(self) -> bool:
        """Check if producer is connected"""
        return self._is_connected


# ===================================
# Factory & Singleton
# ===================================

def create_kafka_producer(config: KafkaProducerConfig) -> KafkaProducer:
    """Factory function to create Kafka producer"""
    return KafkaProducer(config)


# Global instance (initialized at app startup)
_kafka_producer: Optional[KafkaProducer] = None


async def initialize_kafka_producer(config: KafkaProducerConfig):
    """
    Initialize global Kafka producer
    
    Call this during app startup (lifespan)
    """
    global _kafka_producer
    _kafka_producer = create_kafka_producer(config)
    await _kafka_producer.connect()


async def shutdown_kafka_producer():
    """
    Shutdown global Kafka producer
    
    Call this during app shutdown (lifespan)
    """
    global _kafka_producer
    if _kafka_producer:
        await _kafka_producer.disconnect()


def get_kafka_producer() -> KafkaProducer:
    """
    Get global Kafka producer instance
    
    Raises:
        RuntimeError: If not initialized
    """
    if _kafka_producer is None:
        raise RuntimeError(
            "Kafka producer not initialized. "
            "Call initialize_kafka_producer() during app startup."
        )
    return _kafka_producer


# ===================================
# Convenience Alias (backward compatible)
# ===================================

kafka_producer = get_kafka_producer  # For backward compatibility