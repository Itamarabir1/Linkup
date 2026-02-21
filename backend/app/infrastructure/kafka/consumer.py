# ===================================
# app/infrastructure/kafka/consumer.py
# Kafka Consumer - Enterprise Grade
# ===================================

import logging
import json
import asyncio
from typing import Optional, Dict, Any, Callable, List, Set
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaError
from kafka.errors import KafkaConnectionError

logger = logging.getLogger(__name__)


# ===================================
# Configuration
# ===================================

@dataclass
class KafkaConsumerConfig:
    """
    Kafka Consumer Configuration
    
    Best Practices:
    - group_id: Unique per consumer group
    - auto_offset_reset='earliest': Process all messages
    - enable_auto_commit=False: Manual offset management (safer)
    - max_poll_records=100: Balance throughput/latency
    """
    bootstrap_servers: List[str]
    topics: List[str]
    group_id: str
    client_id: str = "linkup-consumer"
    
    # Offset Management
    auto_offset_reset: str = "earliest"  # or 'latest'
    enable_auto_commit: bool = False  # Manual commit for reliability
    auto_commit_interval_ms: int = 5000
    
    # Performance
    max_poll_records: int = 100
    max_poll_interval_ms: int = 300000  # 5 minutes
    session_timeout_ms: int = 10000  # 10 seconds
    
    # Security (optional)
    security_protocol: str = "PLAINTEXT"
    sasl_mechanism: Optional[str] = None
    sasl_username: Optional[str] = None
    sasl_password: Optional[str] = None
    
    def to_kafka_config(self) -> Dict[str, Any]:
        """Convert to aiokafka config dict"""
        config = {
            "bootstrap_servers": self.bootstrap_servers,
            "group_id": self.group_id,
            "client_id": self.client_id,
            "auto_offset_reset": self.auto_offset_reset,
            "enable_auto_commit": self.enable_auto_commit,
            "auto_commit_interval_ms": self.auto_commit_interval_ms,
            "max_poll_records": self.max_poll_records,
            "max_poll_interval_ms": self.max_poll_interval_ms,
            "session_timeout_ms": self.session_timeout_ms,
            "security_protocol": self.security_protocol,
            # Deserialization
            "value_deserializer": lambda v: json.loads(v.decode('utf-8')),
            "key_deserializer": lambda k: k.decode('utf-8') if k else None,
        }
        
        # Add SASL if configured
        if self.sasl_mechanism:
            config["sasl_mechanism"] = self.sasl_mechanism
            config["sasl_plain_username"] = self.sasl_username
            config["sasl_plain_password"] = self.sasl_password
        
        return config


# ===================================
# Message Handler Interface
# ===================================

class MessageHandler:
    """
    Abstract message handler
    
    Implement this to process messages
    """
    
    async def handle(self, event: Dict[str, Any]) -> bool:
        """
        Process a single event
        
        Args:
            event: Deserialized event data
            
        Returns:
            bool: True if processed successfully, False otherwise
        """
        raise NotImplementedError


# ===================================
# Kafka Consumer
# ===================================

class KafkaConsumer:
    """
    Enterprise-grade Kafka Consumer
    
    Features:
    - Async/await support
    - Manual offset management
    - Error handling
    - Graceful shutdown
    - At-least-once delivery
    - Message handlers
    
    Design Patterns:
    - Observer (message handlers)
    - Template Method (message processing flow)
    - Strategy (different handlers for different events)
    """
    
    def __init__(self, config: KafkaConsumerConfig):
        self._config = config
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._is_running = False
        self._handlers: Dict[str, MessageHandler] = {}
        
        # Monitoring
        self._messages_processed = 0
        self._messages_failed = 0
    
    async def connect(self):
        """
        Initialize connection to Kafka cluster
        
        Should be called once during app startup
        """
        try:
            self._consumer = AIOKafkaConsumer(
                *self._config.topics,
                **self._config.to_kafka_config()
            )
            
            await self._consumer.start()
            logger.info(
                f"✅ Kafka consumer connected: "
                f"topics={self._config.topics}, "
                f"group={self._config.group_id}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to connect Kafka consumer: {e}")
            raise
    
    async def disconnect(self):
        """
        Close connection to Kafka cluster
        
        Should be called during app shutdown
        """
        if self._consumer:
            try:
                await self._consumer.stop()
                logger.info("✅ Kafka consumer disconnected")
            except Exception as e:
                logger.error(f"❌ Error disconnecting Kafka consumer: {e}")
    
    def register_handler(self, event_name: str, handler: MessageHandler):
        """
        Register a handler for specific event type
        
        Example:
            consumer.register_handler("USER_REGISTERED", UserRegisteredHandler())
            consumer.register_handler("RIDE_CREATED", RideCreatedHandler())
        """
        self._handlers[event_name] = handler
        logger.info(f"📝 Registered handler for event: {event_name}")
    
    async def start(self):
        """
        Start consuming messages
        
        This runs in an infinite loop until stopped
        Should be run as a background task
        """
        if not self._consumer:
            raise RuntimeError("Consumer not connected. Call connect() first.")
        
        self._is_running = True
        logger.info("🚀 Kafka consumer started")
        
        try:
            async for message in self._consumer:
                if not self._is_running:
                    break
                
                await self._process_message(message)
                
        except asyncio.CancelledError:
            logger.info("🛑 Kafka consumer cancelled")
            raise
            
        except Exception as e:
            logger.error(f"❌ Kafka consumer error: {e}", exc_info=True)
            raise
    
    async def stop(self):
        """
        Stop consuming messages
        
        Gracefully shuts down the consumer
        """
        logger.info("🛑 Stopping Kafka consumer...")
        self._is_running = False
    
    async def _process_message(self, message):
        """
        Process a single Kafka message
        
        Implements at-least-once delivery:
        1. Process message
        2. If successful, commit offset
        3. If failed, retry or skip (based on strategy)
        """
        try:
            # Extract event data
            event_data = message.value
            event_name = event_data.get("event")
            
            if not event_name:
                logger.warning(f"⚠️ Message without event name: {message}")
                await self._commit_offset(message)
                return
            
            # Find handler
            handler = self._handlers.get(event_name)
            
            if not handler:
                logger.warning(f"⚠️ No handler for event: {event_name}")
                await self._commit_offset(message)
                return
            
            # Process message
            logger.debug(
                f"📨 Processing: {event_name} "
                f"(partition={message.partition}, offset={message.offset})"
            )
            
            success = await handler.handle(event_data)
            
            if success:
                self._messages_processed += 1
                await self._commit_offset(message)
                logger.debug(f"✅ Processed: {event_name}")
            else:
                self._messages_failed += 1
                logger.error(f"❌ Failed to process: {event_name}")
                # Don't commit - message will be reprocessed
                # TODO: Implement dead letter queue for permanent failures
            
        except Exception as e:
            self._messages_failed += 1
            logger.error(
                f"❌ Error processing message: {e}",
                exc_info=True,
                extra={
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset
                }
            )
            # Don't commit - message will be reprocessed
    
    async def _commit_offset(self, message):
        """Commit message offset"""
        try:
            if not self._config.enable_auto_commit:
                await self._consumer.commit({
                    message.topic: {
                        message.partition: message.offset + 1
                    }
                })
        except Exception as e:
            logger.error(f"❌ Failed to commit offset: {e}")
    
    def get_metrics(self) -> Dict[str, int]:
        """Get consumer metrics"""
        return {
            "messages_processed": self._messages_processed,
            "messages_failed": self._messages_failed,
            "is_running": self._is_running
        }


# ===================================
# Example Handlers
# ===================================

class AnalyticsHandler(MessageHandler):
    """
    Example handler for analytics events
    
    Stores events in database/data warehouse
    """
    
    def __init__(self, analytics_db):
        self._db = analytics_db
    
    async def handle(self, event: Dict[str, Any]) -> bool:
        """Process analytics event"""
        try:
            event_name = event.get("event")
            payload = event.get("payload", {})
            
            # Store in analytics database
            await self._db.store_event(
                event_type=event_name,
                data=payload,
                timestamp=payload.get("timestamp", datetime.now().isoformat())
            )
            
            logger.info(f"📊 Analytics: Stored {event_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Analytics handler error: {e}")
            return False


class UserRegisteredHandler(MessageHandler):
    """Example handler for user registration events"""
    
    async def handle(self, event: Dict[str, Any]) -> bool:
        """Process user registration event"""
        try:
            payload = event.get("payload", {})
            user_id = payload.get("user_id")
            
            # Example: Update user statistics
            logger.info(f"👤 User registered: {user_id}")
            
            # Your business logic here
            # await self._analytics_service.track_registration(user_id)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ UserRegisteredHandler error: {e}")
            return False


# ===================================
# Factory & Lifecycle
# ===================================

def create_kafka_consumer(
    config: KafkaConsumerConfig,
    handlers: Optional[Dict[str, MessageHandler]] = None
) -> KafkaConsumer:
    """
    Factory function to create Kafka consumer
    
    Args:
        config: Consumer configuration
        handlers: Dict mapping event names to handlers
    """
    consumer = KafkaConsumer(config)
    
    if handlers:
        for event_name, handler in handlers.items():
            consumer.register_handler(event_name, handler)
    
    return consumer


async def run_kafka_consumer(consumer: KafkaConsumer):
    """
    Run Kafka consumer as a background task
    
    Example:
        consumer = create_kafka_consumer(config, handlers)
        await consumer.connect()
        
        task = asyncio.create_task(run_kafka_consumer(consumer))
        
        # ... do other work ...
        
        await consumer.stop()
        await task
    """
    try:
        await consumer.start()
    except asyncio.CancelledError:
        logger.info("Consumer task cancelled")
    except Exception as e:
        logger.error(f"Consumer task failed: {e}", exc_info=True)
    finally:
        await consumer.disconnect()