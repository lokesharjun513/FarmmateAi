"""reconcile current models with database

Revision ID: 1ca38a27638e
Revises: e9253852cea9
Create Date: 2026-08-16

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# ============================================================
# REVISION IDENTIFIERS
# ============================================================

revision: str = "1ca38a27638e"

down_revision: Union[str, Sequence[str], None] = "e9253852cea9"

branch_labels: Union[str, Sequence[str], None] = None

depends_on: Union[str, Sequence[str], None] = None


# ============================================================
# UPGRADE
# ============================================================


def upgrade() -> None:

    # ========================================================
    # 1. RENAME EXISTING ENUM TYPES
    #
    # The original migrations created these PostgreSQL enum
    # types without underscores.
    #
    # Current SQLAlchemy models use the underscored names.
    #
    # Existing data is preserved because only the PostgreSQL
    # TYPE names are being changed.
    # ========================================================

    op.execute(
        """
        ALTER TYPE activitytype
        RENAME TO activity_type
        """
    )

    op.execute(
        """
        ALTER TYPE activitystatus
        RENAME TO activity_status
        """
    )

    op.execute(
        """
        ALTER TYPE farmingseason
        RENAME TO farming_season
        """
    )

    op.execute(
        """
        ALTER TYPE cropseasonstatus
        RENAME TO crop_season_status
        """
    )

    op.execute(
        """
        ALTER TYPE notificationtype
        RENAME TO notification_type
        """
    )

    op.execute(
        """
        ALTER TYPE notificationpriority
        RENAME TO notification_priority
        """
    )

    # ========================================================
    # 2. ASK FM ROLE AND SESSION STATUS
    #
    # Ensure askfmrole and askfmsessionstatus are renamed to
    # underscored names if they exist from earlier migrations,
    # then add SYSTEM to ask_fm_role.
    # ========================================================

    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'askfmrole') THEN
                ALTER TYPE askfmrole RENAME TO ask_fm_role;
            END IF;
            IF EXISTS (SELECT 1 FROM pg_type WHERE typname = 'askfmsessionstatus') THEN
                ALTER TYPE askfmsessionstatus RENAME TO ask_fm_session_status;
            END IF;
        END
        $$;
        """
    )

    op.execute(
        """
        ALTER TYPE ask_fm_role
        ADD VALUE IF NOT EXISTS 'SYSTEM'
        """
    )

    # ========================================================
    # 3. ADD NEW ACTIVITY TYPES
    #
    # Existing values are preserved.
    #
    # New values:
    #
    # LAND_PREPARATION
    # NURSERY
    # TRANSPLANTING
    # SPRAYING
    # ========================================================

    op.execute(
        """
        ALTER TYPE activity_type
        ADD VALUE IF NOT EXISTS 'LAND_PREPARATION'
        """
    )

    op.execute(
        """
        ALTER TYPE activity_type
        ADD VALUE IF NOT EXISTS 'NURSERY'
        """
    )

    op.execute(
        """
        ALTER TYPE activity_type
        ADD VALUE IF NOT EXISTS 'TRANSPLANTING'
        """
    )

    op.execute(
        """
        ALTER TYPE activity_type
        ADD VALUE IF NOT EXISTS 'SPRAYING'
        """
    )

    # ========================================================
    # 4. CREATE CROP STAGE STATUS ENUM
    #
    # PostgreSQL enum type:
    #
    # crop_stage_status
    #
    # Values:
    #
    # PENDING
    # ACTIVE
    # COMPLETED
    # SKIPPED
    #
    # The DO block makes the operation safe if the type
    # already exists.
    # ========================================================

    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_type
                WHERE typname = 'crop_stage_status'
            ) THEN

                CREATE TYPE crop_stage_status AS ENUM (
                    'PENDING',
                    'ACTIVE',
                    'COMPLETED',
                    'SKIPPED'
                );

            END IF;
        END
        $$;
        """
    )

    crop_stage_status = postgresql.ENUM(
        "PENDING",
        "ACTIVE",
        "COMPLETED",
        "SKIPPED",
        name="crop_stage_status",
        create_type=False,
    )

    # ========================================================
    # 5. CREATE CROP STAGES TABLE
    # ========================================================

    op.create_table(
        "crop_stages",

        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "crop_season_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),

        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "stage_order",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "start_day",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "end_day",
            sa.Integer(),
            nullable=False,
        ),

        sa.Column(
            "status",
            crop_stage_status,
            nullable=False,
        ),

        sa.Column(
            "started_at",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
            "completed_at",
            sa.Date(),
            nullable=True,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),

        sa.ForeignKeyConstraint(
            ["crop_season_id"],
            ["crop_seasons.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint(
            "crop_season_id",
            "stage_order",
            name="uq_crop_stage_season_order",
        ),

        sa.CheckConstraint(
            "stage_order >= 1",
            name="ck_crop_stage_order_positive",
        ),

        sa.CheckConstraint(
            "start_day >= 1",
            name="ck_crop_stage_start_day_positive",
        ),

        sa.CheckConstraint(
            "end_day >= 1",
            name="ck_crop_stage_end_day_positive",
        ),

        sa.CheckConstraint(
            "end_day >= start_day",
            name="ck_crop_stage_valid_timeline",
        ),
    )

    # ========================================================
    # 6. CROP STAGE INDEXES
    # ========================================================

    op.create_index(
        "ix_crop_stages_crop_season_id",
        "crop_stages",
        ["crop_season_id"],
    )

    op.create_index(
        "ix_crop_stages_status",
        "crop_stages",
        ["status"],
    )

    op.create_index(
        "ix_crop_stage_season_status",
        "crop_stages",
        ["crop_season_id", "status"],
    )

    op.create_index(
        "ix_crop_stage_season_order",
        "crop_stages",
        ["crop_season_id", "stage_order"],
    )

    # ========================================================
    # 7. CREATE ACTIVITY SOURCE ENUM
    # ========================================================

    activity_source = postgresql.ENUM(
        "AI_PLANNED",
        "WEATHER_TRIGGERED",
        "FARMER_ADDED",
        "SYSTEM",
        name="activity_source",
    )

    activity_source.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ========================================================
    # 8. CREATE ACTIVITY PRIORITY ENUM
    # ========================================================

    activity_priority = postgresql.ENUM(
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
        name="activity_priority",
    )

    activity_priority.create(
        op.get_bind(),
        checkfirst=True,
    )

    # ========================================================
    # 9. ADD ACTIVITY STAGE ID
    # ========================================================

    op.add_column(
        "activities",
        sa.Column(
            "stage_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    # ========================================================
    # 10. ADD ORIGINAL SCHEDULED DATE
    # ========================================================

    op.add_column(
        "activities",
        sa.Column(
            "original_scheduled_date",
            sa.Date(),
            nullable=True,
        ),
    )

    # ========================================================
    # 11. ADD ACTIVITY SOURCE
    #
    # Existing activities were created before source existed.
    #
    # Existing rows are therefore classified as:
    #
    # AI_PLANNED
    # ========================================================

    op.add_column(
        "activities",
        sa.Column(
            "source",
            activity_source,
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE activities
        SET source = 'AI_PLANNED'
        WHERE source IS NULL
        """
    )

    op.alter_column(
        "activities",
        "source",
        existing_type=activity_source,
        nullable=False,
    )

    # ========================================================
    # 12. ADD ACTIVITY STAGE FOREIGN KEY
    # ========================================================

    op.create_foreign_key(
        "fk_activities_stage_id_crop_stages",
        "activities",
        "crop_stages",
        ["stage_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # ========================================================
    # 13. CONVERT ACTIVITY PRIORITY
    #
    # Current database:
    #
    # priority VARCHAR(20)
    #
    # Current values:
    #
    # HIGH
    # MEDIUM
    #
    # New enum:
    #
    # LOW
    # MEDIUM
    # HIGH
    # CRITICAL
    #
    # Existing values are preserved.
    # ========================================================

    op.add_column(
        "activities",
        sa.Column(
            "priority_new",
            activity_priority,
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE activities
        SET priority_new = priority::activity_priority
        """
    )

    op.drop_column(
        "activities",
        "priority",
    )

    op.alter_column(
        "activities",
        "priority_new",
        new_column_name="priority",
        existing_type=activity_priority,
        nullable=False,
    )

    # ========================================================
    # 14. EXPAND ACTIVITY TITLE
    #
    # 100 characters -> 150 characters
    # ========================================================

    op.alter_column(
        "activities",
        "title",
        existing_type=sa.String(length=100),
        type_=sa.String(length=150),
        existing_nullable=False,
    )

    # ========================================================
    # 15. ACTIVITY INDEXES
    # ========================================================

    op.create_index(
        "ix_activities_activity_type",
        "activities",
        ["activity_type"],
    )

    op.create_index(
        "ix_activities_completed_date",
        "activities",
        ["completed_date"],
    )

    op.create_index(
        "ix_activities_priority",
        "activities",
        ["priority"],
    )

    op.create_index(
        "ix_activities_scheduled_date",
        "activities",
        ["scheduled_date"],
    )

    op.create_index(
        "ix_activities_source",
        "activities",
        ["source"],
    )

    op.create_index(
        "ix_activities_stage_id",
        "activities",
        ["stage_id"],
    )

    op.create_index(
        "ix_activities_status",
        "activities",
        ["status"],
    )

    op.create_index(
        "ix_activity_crop_completed_date",
        "activities",
        ["crop_season_id", "completed_date"],
    )

    op.create_index(
        "ix_activity_crop_date_status",
        "activities",
        [
            "crop_season_id",
            "scheduled_date",
            "status",
        ],
    )

    op.create_index(
        "ix_activity_crop_source",
        "activities",
        [
            "crop_season_id",
            "source",
        ],
    )

    op.create_index(
        "ix_activity_crop_stage_status",
        "activities",
        [
            "crop_season_id",
            "stage_id",
            "status",
        ],
    )

    op.create_index(
        "ix_activity_crop_status_priority",
        "activities",
        [
            "crop_season_id",
            "status",
            "priority",
        ],
    )

    op.create_index(
        "ix_activity_date_priority",
        "activities",
        [
            "scheduled_date",
            "priority",
        ],
    )

    op.create_index(
        "ix_activity_stage_date",
        "activities",
        [
            "stage_id",
            "scheduled_date",
        ],
    )

    # ========================================================
    # 16. ADD ASK FM MESSAGE ORDER
    #
    # Existing messages are first given a nullable column.
    # ========================================================

    op.add_column(
        "ask_fm_messages",
        sa.Column(
            "message_order",
            sa.Integer(),
            nullable=True,
        ),
    )

    # ========================================================
    # 17. BACKFILL MESSAGE ORDER
    #
    # Example:
    #
    # Session A:
    #
    # 1 USER
    # 2 ASSISTANT
    # 3 USER
    # 4 ASSISTANT
    #
    # created_at is the primary ordering field.
    # id is the deterministic tie-breaker.
    # ========================================================

    op.execute(
        """
        WITH ordered_messages AS (
            SELECT
                id,
                ROW_NUMBER() OVER (
                    PARTITION BY session_id
                    ORDER BY created_at, id
                ) AS row_number
            FROM ask_fm_messages
        )
        UPDATE ask_fm_messages AS messages
        SET message_order = ordered_messages.row_number
        FROM ordered_messages
        WHERE messages.id = ordered_messages.id
        """
    )

    # ========================================================
    # 18. MAKE MESSAGE ORDER REQUIRED
    # ========================================================

    op.alter_column(
        "ask_fm_messages",
        "message_order",
        existing_type=sa.Integer(),
        nullable=False,
    )

    # ========================================================
    # 19. MESSAGE ORDER UNIQUE CONSTRAINT
    # ========================================================

    op.create_unique_constraint(
        "uq_ask_fm_message_session_order",
        "ask_fm_messages",
        [
            "session_id",
            "message_order",
        ],
    )

    # ========================================================
    # 20. CROP SEASON INDEXES
    # ========================================================

    op.create_index(
        "ix_crop_season_expected_harvest_date",
        "crop_seasons",
        ["expected_harvest_date"],
    )

    op.create_index(
        "ix_crop_season_farm_season",
        "crop_seasons",
        [
            "farm_id",
            "season",
        ],
    )

    op.create_index(
        "ix_crop_season_farm_status",
        "crop_seasons",
        [
            "farm_id",
            "status",
        ],
    )

    op.create_index(
        "ix_crop_season_farm_year",
        "crop_seasons",
        [
            "farm_id",
            "year",
        ],
    )

    op.create_index(
        "ix_crop_season_harvested_date",
        "crop_seasons",
        ["harvested_date"],
    )

    op.create_index(
        "ix_crop_season_sowing_date",
        "crop_seasons",
        ["sowing_date"],
    )

    op.create_index(
        "ix_crop_seasons_is_active",
        "crop_seasons",
        ["is_active"],
    )

    op.create_index(
        "ix_crop_seasons_status",
        "crop_seasons",
        ["status"],
    )

    # ========================================================
    # 21. FARMER / FARM INDEXES
    # ========================================================

    op.create_index(
        "ix_farmers_onboarding_completed",
        "farmers",
        ["onboarding_completed"],
    )

    op.create_index(
        "ix_farms_farmer_id",
        "farms",
        ["farmer_id"],
    )

    # ========================================================
    # 22. NOTIFICATION INDEXES
    # ========================================================

    op.create_index(
        "ix_notification_farmer_created",
        "notifications",
        [
            "farmer_id",
            "created_at",
        ],
    )

    op.create_index(
        "ix_notification_farmer_priority",
        "notifications",
        [
            "farmer_id",
            "priority",
        ],
    )

    op.create_index(
        "ix_notification_farmer_read",
        "notifications",
        [
            "farmer_id",
            "is_read",
        ],
    )

    op.create_index(
        "ix_notifications_is_read",
        "notifications",
        ["is_read"],
    )

    op.create_index(
        "ix_notifications_priority",
        "notifications",
        ["priority"],
    )

    op.create_index(
        "ix_notifications_type",
        "notifications",
        ["type"],
    )

    # ========================================================
    # 23. USERS UNIQUE CONSTRAINTS
    #
    # Existing database has unique indexes:
    #
    # ix_users_email
    # ix_users_mobile
    #
    # Convert them to explicit UNIQUE constraints.
    # ========================================================

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.drop_index(
        "ix_users_mobile",
        table_name="users",
    )

    op.create_unique_constraint(
        "uq_users_email",
        "users",
        ["email"],
    )

    op.create_unique_constraint(
        "uq_users_mobile",
        "users",
        ["mobile"],
    )

    # ========================================================
    # 24. USER ACTIVE INDEX
    # ========================================================

    op.create_index(
        "ix_users_is_active",
        "users",
        ["is_active"],
    )


# ============================================================
# DOWNGRADE
# ============================================================


def downgrade() -> None:

    # ========================================================
    # 1. USER ACTIVE INDEX
    # ========================================================

    op.drop_index(
        "ix_users_is_active",
        table_name="users",
    )

    # ========================================================
    # 2. RESTORE USER UNIQUE INDEXES
    # ========================================================

    op.drop_constraint(
        "uq_users_mobile",
        "users",
        type_="unique",
    )

    op.drop_constraint(
        "uq_users_email",
        "users",
        type_="unique",
    )

    op.create_index(
        "ix_users_mobile",
        "users",
        ["mobile"],
        unique=True,
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    # ========================================================
    # 3. NOTIFICATION INDEXES
    # ========================================================

    op.drop_index(
        "ix_notifications_type",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notifications_priority",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notifications_is_read",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notification_farmer_read",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notification_farmer_priority",
        table_name="notifications",
    )

    op.drop_index(
        "ix_notification_farmer_created",
        table_name="notifications",
    )

    # ========================================================
    # 4. FARM / FARMER INDEXES
    # ========================================================

    op.drop_index(
        "ix_farms_farmer_id",
        table_name="farms",
    )

    op.drop_index(
        "ix_farmers_onboarding_completed",
        table_name="farmers",
    )

    # ========================================================
    # 5. CROP SEASON INDEXES
    # ========================================================

    op.drop_index(
        "ix_crop_seasons_status",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_seasons_is_active",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_season_sowing_date",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_season_harvested_date",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_season_farm_year",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_season_farm_status",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_season_farm_season",
        table_name="crop_seasons",
    )

    op.drop_index(
        "ix_crop_season_expected_harvest_date",
        table_name="crop_seasons",
    )

    # ========================================================
    # 6. ASK FM MESSAGE ORDER
    # ========================================================

    op.drop_constraint(
        "uq_ask_fm_message_session_order",
        "ask_fm_messages",
        type_="unique",
    )

    op.drop_column(
        "ask_fm_messages",
        "message_order",
    )

    # ========================================================
    # 7. ACTIVITY INDEXES
    # ========================================================

    op.drop_index(
        "ix_activity_stage_date",
        table_name="activities",
    )

    op.drop_index(
        "ix_activity_date_priority",
        table_name="activities",
    )

    op.drop_index(
        "ix_activity_crop_status_priority",
        table_name="activities",
    )

    op.drop_index(
        "ix_activity_crop_stage_status",
        table_name="activities",
    )

    op.drop_index(
        "ix_activity_crop_source",
        table_name="activities",
    )

    op.drop_index(
        "ix_activity_crop_date_status",
        table_name="activities",
    )

    op.drop_index(
        "ix_activity_crop_completed_date",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_status",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_stage_id",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_source",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_scheduled_date",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_priority",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_completed_date",
        table_name="activities",
    )

    op.drop_index(
        "ix_activities_activity_type",
        table_name="activities",
    )

    # ========================================================
    # 8. ACTIVITY PRIORITY BACK TO VARCHAR
    # ========================================================

    op.add_column(
        "activities",
        sa.Column(
            "priority_old",
            sa.String(length=20),
            nullable=True,
        ),
    )

    op.execute(
        """
        UPDATE activities
        SET priority_old = priority::text
        """
    )

    op.drop_column(
        "activities",
        "priority",
    )

    op.alter_column(
        "activities",
        "priority_old",
        new_column_name="priority",
        existing_type=sa.String(length=20),
        nullable=False,
    )

    # ========================================================
    # 9. DROP ACTIVITY FOREIGN KEY
    # ========================================================

    op.drop_constraint(
        "fk_activities_stage_id_crop_stages",
        "activities",
        type_="foreignkey",
    )

    # ========================================================
    # 10. DROP ACTIVITY COLUMNS
    # ========================================================

    op.drop_column(
        "activities",
        "source",
    )

    op.drop_column(
        "activities",
        "original_scheduled_date",
    )

    op.drop_column(
        "activities",
        "stage_id",
    )

    # ========================================================
    # 11. DROP CROP STAGE INDEXES
    # ========================================================

    op.drop_index(
        "ix_crop_stage_season_order",
        table_name="crop_stages",
    )

    op.drop_index(
        "ix_crop_stage_season_status",
        table_name="crop_stages",
    )

    op.drop_index(
        "ix_crop_stages_status",
        table_name="crop_stages",
    )

    op.drop_index(
        "ix_crop_stages_crop_season_id",
        table_name="crop_stages",
    )

    # ========================================================
    # 12. DROP CROP STAGES TABLE
    # ========================================================

    op.drop_table(
        "crop_stages",
    )

    # ========================================================
    # 13. DROP NEW ENUM TYPES
    # ========================================================

    op.execute(
        """
        DROP TYPE IF EXISTS crop_stage_status
        """
    )

    op.execute(
        """
        DROP TYPE IF EXISTS activity_source
        """
    )

    op.execute(
        """
        DROP TYPE IF EXISTS activity_priority
        """
    )

    # ========================================================
    # 14. RESTORE OLD ENUM TYPE NAMES
    #
    # Ask FM enum names are intentionally NOT renamed here.
    #
    # They already existed with the current names before this
    # migration:
    #
    #     ask_fm_role
    #     ask_fm_session_status
    #
    # SYSTEM remains in ask_fm_role after downgrade because
    # PostgreSQL does not safely remove enum values.
    # ========================================================

    op.execute(
        """
        ALTER TYPE notification_priority
        RENAME TO notificationpriority
        """
    )

    op.execute(
        """
        ALTER TYPE notification_type
        RENAME TO notificationtype
        """
    )

    op.execute(
        """
        ALTER TYPE crop_season_status
        RENAME TO cropseasonstatus
        """
    )

    op.execute(
        """
        ALTER TYPE farming_season
        RENAME TO farmingseason
        """
    )

    op.execute(
        """
        ALTER TYPE activity_status
        RENAME TO activitystatus
        """
    )

    op.execute(
        """
        ALTER TYPE activity_type
        RENAME TO activitytype
        """
    )