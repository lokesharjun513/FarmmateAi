from uuid import uuid4

from app.modules.chat.message_repository import (
    MessageRepository,
)
from app.modules.chat.models import (
    AskFMRole,
)


# ============================================================
# USER MESSAGE
# ============================================================


def test_create_user_message(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    message = repository.create_user_message(
        session_id=session_id,
        content="How is my rice crop?",
    )

    assert message.id is not None

    assert message.session_id == session_id

    assert message.role == AskFMRole.USER

    assert message.content == (
        "How is my rice crop?"
    )

    assert message.message_order == 1


# ============================================================
# ASSISTANT MESSAGE
# ============================================================


def test_create_assistant_message(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    message = repository.create_assistant_message(
        session_id=session_id,
        content="Your rice crop looks healthy.",
    )

    assert message.id is not None

    assert message.session_id == session_id

    assert message.role == AskFMRole.ASSISTANT

    assert message.content == (
        "Your rice crop looks healthy."
    )

    assert message.message_order == 1


# ============================================================
# SYSTEM MESSAGE
# ============================================================


def test_create_system_message(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    message = repository.create_system_message(
        session_id=session_id,
        content="System context.",
    )

    assert message.id is not None

    assert message.session_id == session_id

    assert message.role == AskFMRole.SYSTEM

    assert message.content == (
        "System context."
    )

    assert message.message_order == 1


# ============================================================
# MESSAGE ORDER
# ============================================================


def test_message_order_increments(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    message_1 = repository.create_user_message(
        session_id=session_id,
        content="Question 1",
    )

    message_2 = repository.create_assistant_message(
        session_id=session_id,
        content="Answer 1",
    )

    message_3 = repository.create_user_message(
        session_id=session_id,
        content="Question 2",
    )

    assert message_1.message_order == 1

    assert message_2.message_order == 2

    assert message_3.message_order == 3


# ============================================================
# MESSAGE ORDER IS PER SESSION
# ============================================================


def test_message_order_is_per_session(db):

    repository = MessageRepository(db)

    session_1 = uuid4()
    session_2 = uuid4()

    message_1 = repository.create_user_message(
        session_id=session_1,
        content="Session 1 Message 1",
    )

    message_2 = repository.create_user_message(
        session_id=session_1,
        content="Session 1 Message 2",
    )

    message_3 = repository.create_user_message(
        session_id=session_2,
        content="Session 2 Message 1",
    )

    assert message_1.message_order == 1

    assert message_2.message_order == 2

    assert message_3.message_order == 1


# ============================================================
# GET BY ID
# ============================================================


def test_get_message_by_id(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    created = repository.create_user_message(
        session_id=session_id,
        content="Test message",
    )

    result = repository.get_by_id(
        created.id,
    )

    assert result is not None

    assert result.id == created.id

    assert result.session_id == session_id

    assert result.role == AskFMRole.USER

    assert result.content == "Test message"

    assert result.message_order == 1


# ============================================================
# GET MESSAGES
# ============================================================


def test_get_messages(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    repository.create_user_message(
        session_id=session_id,
        content="Question 1",
    )

    repository.create_assistant_message(
        session_id=session_id,
        content="Answer 1",
    )

    repository.create_user_message(
        session_id=session_id,
        content="Question 2",
    )

    messages = repository.get_messages(
        session_id,
    )

    assert len(messages) == 3

    assert messages[0].message_order == 1
    assert messages[1].message_order == 2
    assert messages[2].message_order == 3

    assert messages[0].content == "Question 1"
    assert messages[1].content == "Answer 1"
    assert messages[2].content == "Question 2"


# ============================================================
# GET MESSAGES DOES NOT RETURN OTHER SESSIONS
# ============================================================


def test_get_messages_isolated_by_session(db):

    repository = MessageRepository(db)

    session_1 = uuid4()
    session_2 = uuid4()

    repository.create_user_message(
        session_id=session_1,
        content="Session 1",
    )

    repository.create_user_message(
        session_id=session_2,
        content="Session 2",
    )

    messages = repository.get_messages(
        session_1,
    )

    assert len(messages) == 1

    assert messages[0].session_id == session_1

    assert messages[0].content == "Session 1"


# ============================================================
# RECENT MESSAGES
# ============================================================


def test_get_recent_messages_limit(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    # Create 25 messages.
    for index in range(25):

        repository.create_user_message(
            session_id=session_id,
            content=f"Message {index}",
        )

    messages = repository.get_recent_messages(
        session_id=session_id,
        limit=20,
    )

    # Only the latest 20 messages should be returned.
    assert len(messages) == 20

    # They must be returned in chronological order.
    assert messages[0].message_order == 6

    assert messages[-1].message_order == 25

    assert messages[0].content == "Message 5"

    assert messages[-1].content == "Message 24"


# ============================================================
# RECENT MESSAGES ARE CHRONOLOGICAL
# ============================================================


def test_recent_messages_are_chronological(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    for index in range(10):

        repository.create_user_message(
            session_id=session_id,
            content=f"Message {index}",
        )

    messages = repository.get_recent_messages(
        session_id=session_id,
        limit=5,
    )

    assert len(messages) == 5

    orders = [
        message.message_order
        for message in messages
    ]

    assert orders == [6, 7, 8, 9, 10]

    contents = [
        message.content
        for message in messages
    ]

    assert contents == [
        "Message 5",
        "Message 6",
        "Message 7",
        "Message 8",
        "Message 9",
    ]


# ============================================================
# RECENT MESSAGES WITH LIMIT 1
# ============================================================


def test_get_recent_messages_limit_one(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    for index in range(5):

        repository.create_user_message(
            session_id=session_id,
            content=f"Message {index}",
        )

    messages = repository.get_recent_messages(
        session_id=session_id,
        limit=1,
    )

    assert len(messages) == 1

    assert messages[0].message_order == 5

    assert messages[0].content == "Message 4"


# ============================================================
# RECENT MESSAGES DEFAULT LIMIT
# ============================================================


def test_get_recent_messages_default_limit(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    for index in range(25):

        repository.create_user_message(
            session_id=session_id,
            content=f"Message {index}",
        )

    messages = repository.get_recent_messages(
        session_id,
    )

    assert len(messages) == 20

    assert messages[0].content == "Message 5"

    assert messages[-1].content == "Message 24"


# ============================================================
# DELETE SESSION MESSAGES
# ============================================================


def test_delete_session_messages(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    repository.create_user_message(
        session_id=session_id,
        content="Message 1",
    )

    repository.create_assistant_message(
        session_id=session_id,
        content="Message 2",
    )

    deleted = repository.delete_session_messages(
        session_id,
    )

    assert deleted == 2

    messages = repository.get_messages(
        session_id,
    )

    assert messages == []


# ============================================================
# DELETE DOES NOT AFFECT OTHER SESSION
# ============================================================


def test_delete_session_messages_isolated(db):

    repository = MessageRepository(db)

    session_1 = uuid4()
    session_2 = uuid4()

    repository.create_user_message(
        session_id=session_1,
        content="Session 1",
    )

    repository.create_user_message(
        session_id=session_2,
        content="Session 2",
    )

    deleted = repository.delete_session_messages(
        session_1,
    )

    assert deleted == 1

    session_1_messages = repository.get_messages(
        session_1,
    )

    session_2_messages = repository.get_messages(
        session_2,
    )

    assert session_1_messages == []

    assert len(session_2_messages) == 1

    assert session_2_messages[0].content == (
        "Session 2"
    )


# ============================================================
# MESSAGE ROLES
# ============================================================


def test_message_roles(db):

    repository = MessageRepository(db)

    session_id = uuid4()

    user_message = (
        repository.create_user_message(
            session_id=session_id,
            content="Question",
        )
    )

    assistant_message = (
        repository.create_assistant_message(
            session_id=session_id,
            content="Answer",
        )
    )

    system_message = (
        repository.create_system_message(
            session_id=session_id,
            content="System",
        )
    )

    assert user_message.role == AskFMRole.USER

    assert (
        assistant_message.role
        == AskFMRole.ASSISTANT
    )

    assert system_message.role == AskFMRole.SYSTEM

    assert user_message.message_order == 1
    assert assistant_message.message_order == 2
    assert system_message.message_order == 3