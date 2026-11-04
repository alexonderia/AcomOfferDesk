from __future__ import annotations

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.repositories.users import UserRepository
from app.repositories.chats import ChatRepository
from app.repositories.feedback import FeedBackRepository


@pytest_asyncio.fixture
async def qa_session():
    engine = create_async_engine('sqlite+aiosqlite:///:memory:')
    statements = [
        'CREATE TABLE users (id TEXT PRIMARY KEY, id_role INTEGER, created_at TIMESTAMP)',
        'CREATE TABLE profiles (id TEXT PRIMARY KEY, mail TEXT, full_name TEXT)',
        'CREATE TABLE company_contacts (id TEXT PRIMARY KEY, inn TEXT, company_name TEXT, mail TEXT)',
        'CREATE TABLE feed_back (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT NOT NULL, author_user_id TEXT, created_at TIMESTAMP)',
        'CREATE TABLE chats (id INTEGER PRIMARY KEY)',
        'CREATE TABLE chat_participants (id_chat INTEGER, id_user TEXT, joined_at TIMESTAMP, left_at TIMESTAMP, last_read_message_id INTEGER, last_read_at TIMESTAMP, is_muted BOOLEAN, is_archived BOOLEAN, PRIMARY KEY(id_chat,id_user))',
    ]
    async with engine.begin() as connection:
        for statement in statements:
            await connection.exec_driver_sql(statement)
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_distinct_inn_is_not_a_duplicate_despite_shared_name_and_email(qa_session):
    s = qa_session
    await s.execute(text("INSERT INTO users VALUES ('company-a',3,'2026-01-01'),('company-b',3,'2026-01-01')"))
    await s.execute(text("INSERT INTO company_contacts VALUES ('company-a','1111111111','Same name','shared@example.com'),('company-b','2222222222','Same name','shared@example.com')"))
    repo = UserRepository(s)
    assert await repo.find_matching_contractor_user_ids(contractor_role_id=3, inn='2222222222', email='shared@example.com', company_name='Same name') == ['company-b']
    assert await repo.find_matching_contractor_user_ids(contractor_role_id=3, inn='3333333333', email='shared@example.com', company_name='Same name') == []


@pytest.mark.asyncio
async def test_feedback_roundtrip_author_search_and_pagination_preserve_legacy_unknowns(qa_session):
    s = qa_session
    await s.execute(text("INSERT INTO profiles VALUES ('author-a','a@example.com','Alice'),('author-b','b@example.com','Bob')"))
    await s.execute(text("INSERT INTO feed_back (text) VALUES ('old feedback')"))
    repo = FeedBackRepository(s)
    first = await repo.create(text='alpha issue', author_user_id='author-a')
    await repo.create(text='second issue', author_user_id='author-b')
    await s.commit()
    s.expunge_all()
    items, total = await repo.list_page(search='Alice', author_user_id=None, sort_by='created_at', sort_order='desc', limit=20, offset=0)
    assert total == 1 and items[0].id == first.id
    assert items[0].author_user_id == 'author-a' and items[0].author_name == 'Alice'
    assert items[0].created_at is not None
    page, total = await repo.list_page(search='', author_user_id=None, sort_by='created_at', sort_order='desc', limit=1, offset=2)
    assert total == 3 and page[0].text == 'old feedback'
    assert page[0].author_user_id is None and page[0].created_at is None


@pytest.mark.asyncio
async def test_chat_reconciliation_adds_new_manager_and_revokes_previous_manager(qa_session):
    s = qa_session
    await s.execute(text('INSERT INTO chats VALUES (10)'))
    repo = ChatRepository(s)
    await repo.reconcile_participants(chat_id=10, user_ids={'owner', 'contractor', 'old-lead'}, primary_user_ids={'owner', 'contractor'})
    assert set(await repo.list_active_participant_user_ids(chat_id=10)) == {'owner', 'contractor', 'old-lead'}
    await repo.reconcile_participants(chat_id=10, user_ids={'owner', 'contractor', 'new-lead'}, primary_user_ids={'owner', 'contractor'})
    assert set(await repo.list_active_participant_user_ids(chat_id=10)) == {'owner', 'contractor', 'new-lead'}
    old = await repo.get_active_participant(chat_id=10, user_id='old-lead')
    assert old is None
    await repo.reconcile_participants(chat_id=10, user_ids={'owner', 'contractor', 'new-lead'}, primary_user_ids={'owner', 'contractor'})
    count = (await s.execute(text('SELECT count(*) FROM chat_participants'))).scalar_one()
    assert count == 4
