"""Full schema – single idempotent migration (users + google_id + groups + group_id).

Revision ID: 001_full_schema
Revises:
Create Date: 2025-03-09

One migration for the entire schema. Safe to run on empty DB or existing DB (adds only what is missing).
Run: alembic upgrade head
"""
from alembic import op
import sqlalchemy as sa


revision = "001_full_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()

    # 1. Enums (create only if not exist)
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'ride_status') THEN
                CREATE TYPE ride_status AS ENUM ('open', 'full', 'completed', 'cancelled');
            END IF;
        END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'booking_status') THEN
                CREATE TYPE booking_status AS ENUM ('pending_approval', 'confirmed', 'rejected', 'cancelled', 'completed');
            END IF;
        END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'passenger_request_status') THEN
                CREATE TYPE passenger_request_status AS ENUM ('active', 'matched', 'expired', 'cancelled', 'pending', 'approved', 'rejected', 'completed');
            END IF;
        END $$
    """))

    # 2. Trigger function (idempotent)
    conn.execute(sa.text("""
        CREATE OR REPLACE FUNCTION update_modified_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """))

    # 3. users (with google_id)
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            full_name VARCHAR(100) NOT NULL,
            phone_number VARCHAR(20) UNIQUE NOT NULL,
            email VARCHAR(255) UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            is_verified BOOLEAN DEFAULT FALSE,
            google_id VARCHAR(255),
            is_active BOOLEAN DEFAULT TRUE,
            is_admin BOOLEAN DEFAULT FALSE,
            fcm_token TEXT,
            refresh_token TEXT,
            last_location GEOGRAPHY(POINT, 4326),
            avatar_url VARCHAR(500),
            last_login TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'google_id') THEN
                ALTER TABLE users ADD COLUMN google_id VARCHAR(255);
            END IF;
        END $$
    """))

    # 4. groups (before rides/passenger_requests that reference it)
    # Create without FK to users so existing DBs with integer user_id don't fail; add FK only if users.user_id is UUID
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS groups (
            group_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(255) NOT NULL,
            invite_code VARCHAR(64) NOT NULL,
            admin_id UUID NOT NULL,
            is_active BOOLEAN DEFAULT TRUE NOT NULL,
            max_members INTEGER,
            invite_expires_at TIMESTAMP WITH TIME ZONE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'user_id' AND data_type = 'uuid')
               AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'groups_admin_id_fkey') THEN
                ALTER TABLE groups ADD CONSTRAINT groups_admin_id_fkey FOREIGN KEY (admin_id) REFERENCES users(user_id) ON DELETE CASCADE;
            END IF;
        END $$
    """))
    conn.execute(sa.text("CREATE UNIQUE INDEX IF NOT EXISTS ix_groups_invite_code ON groups (invite_code)"))

    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS group_members (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            group_id UUID NOT NULL REFERENCES groups(group_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            role VARCHAR(20) DEFAULT 'member' NOT NULL,
            joined_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_group_member UNIQUE (group_id, user_id)
        )
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'user_id' AND data_type = 'uuid')
               AND NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'group_members_user_id_fkey') THEN
                ALTER TABLE group_members ADD CONSTRAINT group_members_user_id_fkey FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE;
            END IF;
        END $$
    """))

    # 5. rides (with group_id)
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS rides (
            ride_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            driver_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
            estimated_arrival_time TIMESTAMP WITH TIME ZONE,
            available_seats INTEGER NOT NULL DEFAULT 4 CHECK (available_seats BETWEEN 0 AND 8),
            price NUMERIC(10, 2) DEFAULT 0 CHECK (price >= 0),
            origin_name VARCHAR(255),
            origin_geom GEOGRAPHY(POINT, 4326) NOT NULL,
            destination_name VARCHAR(255),
            destination_geom GEOGRAPHY(POINT, 4326) NOT NULL,
            route_coords GEOGRAPHY(LINESTRING, 4326),
            route_summary VARCHAR(255),
            distance_km DECIMAL(10, 2),
            duration_min DECIMAL(10, 2),
            status ride_status DEFAULT 'open' NOT NULL,
            group_id UUID,
            reminder_sent BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'rides' AND column_name = 'group_id') THEN
                ALTER TABLE rides ADD COLUMN group_id UUID;
            END IF;
        END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_rides_group_id') THEN
                ALTER TABLE rides ADD CONSTRAINT fk_rides_group_id FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE SET NULL;
            END IF;
        END $$
    """))

    # 6. passenger_requests (with group_id)
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS passenger_requests (
            request_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            passenger_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            num_passengers INTEGER NOT NULL DEFAULT 1 CHECK (num_passengers BETWEEN 1 AND 8),
            pickup_name VARCHAR(255),
            pickup_geom GEOGRAPHY(POINT, 4326) NOT NULL,
            destination_name VARCHAR(255),
            destination_geom GEOGRAPHY(POINT, 4326) NOT NULL,
            requested_departure_time TIMESTAMP WITH TIME ZONE NOT NULL,
            estimated_arrival_time TIMESTAMP WITH TIME ZONE,
            desired_arrival_time TIMESTAMP WITH TIME ZONE,
            search_radius_meters INTEGER DEFAULT 500 CHECK (search_radius_meters BETWEEN 100 AND 5000),
            is_auto_generated BOOLEAN DEFAULT FALSE,
            distance_km DECIMAL(10, 2) DEFAULT 0,
            duration_min DECIMAL(10, 2) DEFAULT 0,
            status passenger_request_status DEFAULT 'active' NOT NULL,
            is_notification_active BOOLEAN DEFAULT TRUE,
            group_id UUID,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'passenger_requests' AND column_name = 'group_id') THEN
                ALTER TABLE passenger_requests ADD COLUMN group_id UUID;
            END IF;
        END $$
    """))
    conn.execute(sa.text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_passenger_requests_group_id') THEN
                ALTER TABLE passenger_requests ADD CONSTRAINT fk_passenger_requests_group_id FOREIGN KEY (group_id) REFERENCES groups(group_id) ON DELETE SET NULL;
            END IF;
        END $$
    """))

    # 7. bookings
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            ride_id UUID NOT NULL REFERENCES rides(ride_id) ON DELETE CASCADE,
            passenger_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            request_id UUID REFERENCES passenger_requests(request_id) ON DELETE SET NULL,
            num_seats INTEGER NOT NULL DEFAULT 1 CHECK (num_seats BETWEEN 1 AND 8),
            pickup_point GEOGRAPHY(POINT, 4326),
            pickup_time TIMESTAMP WITH TIME ZONE,
            pickup_name VARCHAR(255),
            status booking_status DEFAULT 'pending_approval' NOT NULL,
            reminder_sent BOOLEAN DEFAULT FALSE NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT unique_passenger_per_ride UNIQUE (ride_id, passenger_id)
        )
    """))

    # 8. conversations + messages
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id_1 UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            user_id_2 UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_conversation_pair UNIQUE (user_id_1, user_id_2),
            CONSTRAINT ck_conversation_ordered CHECK (user_id_1 < user_id_2)
        )
    """))
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id BIGSERIAL PRIMARY KEY,
            conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
            sender_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
            body TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
        )
    """))

    # 9. outbox_events
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS outbox_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            event_name VARCHAR(100) NOT NULL,
            payload JSONB NOT NULL,
            targets VARCHAR[] NOT NULL,
            metadata JSONB,
            status VARCHAR(20) DEFAULT 'PENDING' NOT NULL,
            retry_count INTEGER DEFAULT 0 NOT NULL,
            last_error TEXT,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            processed_at TIMESTAMP WITH TIME ZONE,
            idempotency_key VARCHAR(255) UNIQUE
        )
    """))

    # 10. Triggers (drop if exists then create)
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_user_modtime ON users"))
    conn.execute(sa.text("CREATE TRIGGER update_user_modtime BEFORE UPDATE ON users FOR EACH ROW EXECUTE FUNCTION update_modified_column()"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_ride_modtime ON rides"))
    conn.execute(sa.text("CREATE TRIGGER update_ride_modtime BEFORE UPDATE ON rides FOR EACH ROW EXECUTE FUNCTION update_modified_column()"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_request_modtime ON passenger_requests"))
    conn.execute(sa.text("CREATE TRIGGER update_request_modtime BEFORE UPDATE ON passenger_requests FOR EACH ROW EXECUTE FUNCTION update_modified_column()"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_booking_modtime ON bookings"))
    conn.execute(sa.text("CREATE TRIGGER update_booking_modtime BEFORE UPDATE ON bookings FOR EACH ROW EXECUTE FUNCTION update_modified_column()"))

    # 11. chat_analysis
    conn.execute(sa.text("""
        CREATE TABLE IF NOT EXISTS chat_analysis (
            analysis_id BIGSERIAL PRIMARY KEY,
            conversation_id UUID NOT NULL REFERENCES conversations(conversation_id) ON DELETE CASCADE,
            driver_name VARCHAR(255),
            passenger_name VARCHAR(255),
            pickup_location TEXT,
            meeting_time TEXT,
            summary_hebrew TEXT,
            analysis_json JSONB,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
            CONSTRAINT uq_chat_analysis_conversation UNIQUE(conversation_id)
        )
    """))

    # 12. Indexes
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_conversations_user_1 ON conversations (user_id_1)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_conversations_user_2 ON conversations (user_id_2)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages (conversation_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_messages_created ON messages (conversation_id, created_at)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_chat_analysis_conversation ON chat_analysis (conversation_id)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_users_location ON users USING GIST(last_location)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_rides_origin_geom ON rides USING GIST(origin_geom)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_rides_destination_geom ON rides USING GIST(destination_geom)"))
    conn.execute(sa.text("CREATE INDEX IF NOT EXISTS idx_outbox_events_pending ON outbox_events (created_at) WHERE status = 'PENDING'"))


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_outbox_events_pending"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_rides_destination_geom"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_rides_origin_geom"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_users_location"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_chat_analysis_conversation"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_messages_created"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_messages_conversation"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_conversations_user_2"))
    conn.execute(sa.text("DROP INDEX IF EXISTS idx_conversations_user_1"))
    conn.execute(sa.text("DROP TABLE IF EXISTS chat_analysis CASCADE"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_booking_modtime ON bookings"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_request_modtime ON passenger_requests"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_ride_modtime ON rides"))
    conn.execute(sa.text("DROP TRIGGER IF EXISTS update_user_modtime ON users"))
    conn.execute(sa.text("DROP TABLE IF EXISTS outbox_events CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS messages CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS conversations CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS bookings CASCADE"))
    conn.execute(sa.text("ALTER TABLE passenger_requests DROP CONSTRAINT IF EXISTS fk_passenger_requests_group_id"))
    conn.execute(sa.text("ALTER TABLE passenger_requests DROP COLUMN IF EXISTS group_id"))
    conn.execute(sa.text("DROP TABLE IF EXISTS passenger_requests CASCADE"))
    conn.execute(sa.text("ALTER TABLE rides DROP CONSTRAINT IF EXISTS fk_rides_group_id"))
    conn.execute(sa.text("ALTER TABLE rides DROP COLUMN IF EXISTS group_id"))
    conn.execute(sa.text("DROP TABLE IF EXISTS rides CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS group_members CASCADE"))
    conn.execute(sa.text("DROP INDEX IF EXISTS ix_groups_invite_code"))
    conn.execute(sa.text("DROP TABLE IF EXISTS groups CASCADE"))
    conn.execute(sa.text("DROP TABLE IF EXISTS users CASCADE"))
    conn.execute(sa.text("DROP FUNCTION IF EXISTS update_modified_column()"))
    conn.execute(sa.text("DROP TYPE IF EXISTS passenger_request_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS booking_status CASCADE"))
    conn.execute(sa.text("DROP TYPE IF EXISTS ride_status CASCADE"))
