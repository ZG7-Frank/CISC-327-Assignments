from datetime import date, timedelta
from unittest.mock import patch

import pytest

from app import store


@pytest.fixture
def reminder_loan(client):
    book_response = client.post("/books", json={
        "title": "QA Test Book",
        "author": "Test Author",
        "isbn": "9780132350884",
        "total_copies": 1,
    })
    assert book_response.status_code == 201
    book_id = book_response.get_json()["id"]

    member_response = client.post("/members", json={
        "name": "Test Member",
        "email": "member@example.com",
    })
    assert member_response.status_code == 201
    member_id = member_response.get_json()["id"]

    checkout_response = client.post("/loans", json={
        "book_id": book_id,
        "member_id": member_id,
    })
    assert checkout_response.status_code == 201

    loan_id = checkout_response.get_json()["id"]
    loan = store.loans[loan_id]
    loan.due_date = date.today() + timedelta(days=2)
    return loan.to_dict()


def test_due_date_reminder_reports_success(client, reminder_loan, monkeypatch):
    monkeypatch.setattr(
        "app.routes.loans.send_notification",
        lambda recipient, subject, message: True,
    )

    loan_id = reminder_loan["id"]
    response = client.post(f"/loans/{loan_id}/reminder")

    assert response.status_code == 200
    assert response.get_json() == {"loan_id": loan_id, "notified": True}
    assert store.loans[loan_id].to_dict() == reminder_loan
    
def test_due_date_reminder_sends_expected_notification(client, reminder_loan):
    loan_id = reminder_loan["id"]
    due_date = reminder_loan["due_date"]

    with patch("app.routes.loans.send_notification", return_value=True) as mock_send:
        response = client.post(f"/loans/{loan_id}/reminder")

    mock_send.assert_called_once_with(
        "member@example.com",
        "[Library] Upcoming due date",
        f"Your library loan #{loan_id} is due on {due_date}.",
    )
    assert response.status_code == 200
    assert response.get_json() == {"loan_id": loan_id, "notified": True}
    assert store.loans[loan_id].to_dict() == reminder_loan


def test_web_book_form_creates_and_deletes_book(client):
    created = client.post(
        "/ui/books",
        data={
            "title": "QA Web Form Book",
            "author": "Test Author",
            "isbn": "9780132350884",
            "total_copies": "2",
        },
        follow_redirects=True,
    )

    assert created.status_code == 200
    assert "QA Web Form Book" in created.get_data(as_text=True)

    books = client.get("/books").get_json()
    assert len(books) == 1
    book = books[0]
    assert book["title"] == "QA Web Form Book"
    assert book["available_copies"] == 2

    deleted = client.post(
        f"/ui/books/{book['id']}/delete",
        follow_redirects=True,
    )

    assert deleted.status_code == 200
    assert "QA Web Form Book" not in deleted.get_data(as_text=True)
    assert client.get("/books").get_json() == []
    
def test_web_member_form_creates_and_deletes_member(client):
    created = client.post(
        "/ui/members",
        data={"name": "QA Web Member", "email": "web.member@example.com"},
        follow_redirects=True,
    )

    assert created.status_code == 200
    assert "QA Web Member" in created.get_data(as_text=True)

    members = client.get("/members").get_json()
    assert len(members) == 1
    member = members[0]
    assert member["name"] == "QA Web Member"
    assert member["email"] == "web.member@example.com"

    deleted = client.post(
        f"/ui/members/{member['id']}/delete",
        follow_redirects=True,
    )

    assert deleted.status_code == 200
    assert "QA Web Member" not in deleted.get_data(as_text=True)
    assert client.get("/members").get_json() == []