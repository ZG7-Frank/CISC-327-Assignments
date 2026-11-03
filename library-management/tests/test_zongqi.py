
import pytest
from datetime import date

from datetime import date, timedelta

import pytest

from app import store

def test_created_book_is_saved_and_retrievable(client):
    payload = {
        "title": "QA Test Book",
        "author": "Test Author",
        "isbn": "9780132350884",
        "total_copies": 2,
    }

    create_response = client.post("/books", json=payload)

    assert create_response.status_code == 201
    created = create_response.get_json()
    book_id = created["id"]

    assert created["title"] == payload["title"]
    assert created["author"] == payload["author"]
    assert created["isbn"] == payload["isbn"]
    assert created["total_copies"] == 2
    assert created["available_copies"] == 2

    get_response = client.get(f"/books/{book_id}")

    assert get_response.status_code == 200
    assert get_response.get_json() == created
    
    
def test_list_books_returns_all_created_records(client):
    payloads = [
        {
            "title": "The Hidden Garden",
            "author": "Alice Morgan",
            "isbn": "9780132350884",
            "total_copies": 2,
        },
        {
            "title": "River Journey",
            "author": "Daniel Reed",
            "isbn": "9780134685991",
            "total_copies": 1,
        },
    ]

    created_books = []
    for payload in payloads:
        response = client.post("/books", json=payload)
        assert response.status_code == 201
        created_books.append(response.get_json())

    list_response = client.get("/books")

    assert list_response.status_code == 200
    listed_books = list_response.get_json()
    assert len(listed_books) == 2

    actual_by_id = {book["id"]: book for book in listed_books}
    expected_by_id = {book["id"]: book for book in created_books}
    assert actual_by_id == expected_by_id
    
def test_update_book_persists_changes(client):
    create_response = client.post("/books", json={
        "title": "Original Book",
        "author": "Original Author",
        "isbn": "9780132350884",
        "total_copies": 2,
    })
    assert create_response.status_code == 201
    book_id = create_response.get_json()["id"]

    update_response = client.put(f"/books/{book_id}", json={
        "title": "Updated Book",
        "author": "Updated Author",
    })

    assert update_response.status_code == 200
    updated = update_response.get_json()
    assert updated["id"] == book_id
    assert updated["title"] == "Updated Book"
    assert updated["author"] == "Updated Author"
    assert updated["isbn"] == "9780132350884"
    assert updated["total_copies"] == 2
    assert updated["available_copies"] == 2

    get_response = client.get(f"/books/{book_id}")

    assert get_response.status_code == 200
    assert get_response.get_json() == updated
    

def test_delete_book_removes_only_selected_record(client):
    first_response = client.post("/books", json={
        "title": "Delete Me",
        "author": "Author A",
        "isbn": "9780132350884",
        "total_copies": 1,
    })
    second_response = client.post("/books", json={
        "title": "Keep Me",
        "author": "Author B",
        "isbn": "9780134685991",
        "total_copies": 2,
    })

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_book = first_response.get_json()
    second_book = second_response.get_json()

    delete_response = client.delete(f"/books/{first_book['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/books/{first_book['id']}")
    assert missing_response.status_code == 404
    assert missing_response.get_json() == {"error": "Book not found"}

    list_response = client.get("/books")
    assert list_response.status_code == 200
    assert list_response.get_json() == [second_book]
    
    
    
@pytest.mark.parametrize(
"query, expected_titles",
[
    ("garden", ["The Hidden Garden"]),
    ("reed", ["River Journey"]),
    ("GaRd", ["The Hidden Garden"]),
    ("zzznomatch", []),
    ("", ["The Hidden Garden", "River Journey"]),
],
)
def test_book_search_returns_matching_records(client, query, expected_titles):
    payloads = [
        {
            "title": "The Hidden Garden",
            "author": "Alice Morgan",
            "isbn": "9780132350884",
            "total_copies": 2,
        },
        {
            "title": "River Journey",
            "author": "Daniel Reed",
            "isbn": "9780134685991",
            "total_copies": 1,
        },
    ]

    created_by_title = {}
    for payload in payloads:
        response = client.post("/books", json=payload)
        assert response.status_code == 201
        created_by_title[payload["title"]] = response.get_json()

    search_response = client.get("/books", query_string={"search": query})

    assert search_response.status_code == 200
    books = search_response.get_json()
    assert len(books) == len(expected_titles)

    actual_by_title = {book["title"]: book for book in books}
    assert set(actual_by_title) == set(expected_titles)

    for title in expected_titles:
        assert actual_by_title[title] == created_by_title[title]
        
    
    
    
    
@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_unknown_book_id_preserves_existing_records(client, method):
    create_response = client.post("/books", json={
        "title": "Existing Book",
        "author": "Existing Author",
        "isbn": "9780132350884",
        "total_copies": 2,
    })
    assert create_response.status_code == 201
    existing_book = create_response.get_json()

    unknown_id = existing_book["id"] + 1000
    path = f"/books/{unknown_id}"

    if method == "PUT":
        response = client.put(path, json={"title": "Should Not Be Saved"})
    else:
        response = client.open(path, method=method)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Book not found"}

    list_response = client.get("/books")
    assert list_response.status_code == 200
    assert list_response.get_json() == [existing_book]
    




def test_created_member_is_saved_and_retrievable(client):
    payload = {
        "name": "Alex Carter",
        "email": "alex.carter@example.com",
    }

    date_before = date.today()
    create_response = client.post("/members", json=payload)
    date_after = date.today()

    assert create_response.status_code == 201
    created = create_response.get_json()
    member_id = created["id"]

    assert created["name"] == payload["name"]
    assert created["email"] == payload["email"]

    membership_date = date.fromisoformat(created["membership_date"])
    assert date_before <= membership_date <= date_after

    get_response = client.get(f"/members/{member_id}")

    assert get_response.status_code == 200
    assert get_response.get_json() == created
    
    
    
def test_list_members_returns_all_created_records(client):
    payloads = [
        {"name": "Alex Carter", "email": "alex.carter@example.com"},
        {"name": "Jamie Chen", "email": "jamie.chen@example.com"},
    ]

    created_members = []
    for payload in payloads:
        response = client.post("/members", json=payload)
        assert response.status_code == 201
        created_members.append(response.get_json())

    list_response = client.get("/members")

    assert list_response.status_code == 200
    listed_members = list_response.get_json()
    assert len(listed_members) == 2

    actual_by_id = {member["id"]: member for member in listed_members}
    expected_by_id = {member["id"]: member for member in created_members}
    assert actual_by_id == expected_by_id   



def test_update_member_persists_changes(client):
    create_response = client.post("/members", json={
        "name": "Original Member",
        "email": "original@example.com",
    })
    assert create_response.status_code == 201
    original = create_response.get_json()
    member_id = original["id"]

    update_response = client.put(f"/members/{member_id}", json={
        "name": "Updated Member",
        "email": "updated@example.com",
    })

    assert update_response.status_code == 200
    updated = update_response.get_json()
    assert updated["id"] == member_id
    assert updated["name"] == "Updated Member"
    assert updated["email"] == "updated@example.com"
    assert updated["membership_date"] == original["membership_date"]

    get_response = client.get(f"/members/{member_id}")

    assert get_response.status_code == 200
    assert get_response.get_json() == updated
    
    
    
    
    
def test_delete_member_removes_only_selected_record(client):
    first_response = client.post("/members", json={
        "name": "Delete Member",
        "email": "delete@example.com",
    })
    second_response = client.post("/members", json={
        "name": "Keep Member",
        "email": "keep@example.com",
    })

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_member = first_response.get_json()
    second_member = second_response.get_json()

    delete_response = client.delete(f"/members/{first_member['id']}")
    assert delete_response.status_code == 204

    missing_response = client.get(f"/members/{first_member['id']}")
    assert missing_response.status_code == 404
    assert missing_response.get_json() == {"error": "Member not found"}

    list_response = client.get("/members")
    assert list_response.status_code == 200
    assert list_response.get_json() == [second_member]
    
    


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
def test_unknown_member_id_preserves_existing_records(client, method):
    create_response = client.post("/members", json={
        "name": "Existing Member",
        "email": "existing@example.com",
    })
    assert create_response.status_code == 201
    existing_member = create_response.get_json()

    unknown_id = existing_member["id"] + 1000
    path = f"/members/{unknown_id}"

    if method == "PUT":
        response = client.put(path, json={"name": "Should Not Be Saved"})
    else:
        response = client.open(path, method=method)

    assert response.status_code == 404
    assert response.get_json() == {"error": "Member not found"}

    list_response = client.get("/members")
    assert list_response.status_code == 200
    assert list_response.get_json() == [existing_member]
    
    
    
@pytest.fixture
def lending_records(client):
    book_response = client.post("/books", json={
        "title": "Loan Test Book",
        "author": "Test Author",
        "isbn": "9780132350884",
        "total_copies": 1,
    })
    first_member_response = client.post("/members", json={
        "name": "Alex Carter",
        "email": "alex.carter@example.com",
    })
    second_member_response = client.post("/members", json={
        "name": "Jamie Chen",
        "email": "jamie.chen@example.com",
    })

    assert book_response.status_code == 201
    assert first_member_response.status_code == 201
    assert second_member_response.status_code == 201

    return {
        "book": book_response.get_json(),
        "member": first_member_response.get_json(),
        "other_member": second_member_response.get_json(),
    }
    
    
    
    
def test_checkout_records_loan_and_updates_availability(client, lending_records):
    book = lending_records["book"]
    member = lending_records["member"]

    response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })

    assert response.status_code == 201
    loan = response.get_json()
    assert loan["book_id"] == book["id"]
    assert loan["member_id"] == member["id"]
    assert loan["return_date"] is None

    loan_date = date.fromisoformat(loan["loan_date"])
    due_date = date.fromisoformat(loan["due_date"])
    assert due_date > loan_date

    book_response = client.get(f"/books/{book['id']}")
    assert book_response.status_code == 200

    expected_book = book.copy()
    expected_book["available_copies"] = 0
    assert book_response.get_json() == expected_book

    loans_response = client.get("/loans")
    assert loans_response.status_code == 200
    assert loans_response.get_json() == [loan]



def test_checkout_without_available_copies_is_rejected(client, lending_records):
    book = lending_records["book"]
    first_member = lending_records["member"]
    second_member = lending_records["other_member"]

    first_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": first_member["id"],
    })
    assert first_response.status_code == 201
    first_loan = first_response.get_json()

    before_response = client.get(f"/books/{book['id']}")
    assert before_response.status_code == 200
    book_before = before_response.get_json()
    assert book_before["available_copies"] == 0

    second_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": second_member["id"],
    })

    after_response = client.get(f"/books/{book['id']}")
    loans_response = client.get("/loans")

    assert after_response.status_code == 200
    assert loans_response.status_code == 200
    assert after_response.get_json() == book_before
    assert loans_response.get_json() == [first_loan]
    assert second_response.status_code in (400, 409)
    
    

def test_return_restores_book_and_records_date(client, lending_records):
    book = lending_records["book"]
    member = lending_records["member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()

    date_before = date.today()
    return_response = client.put(f"/loans/{loan['id']}/return")
    date_after = date.today()

    assert return_response.status_code == 200
    returned = return_response.get_json()

    return_date = date.fromisoformat(returned["return_date"])
    assert date_before <= return_date <= date_after

    expected_loan = loan.copy()
    expected_loan["return_date"] = returned["return_date"]
    assert returned == expected_loan

    book_response = client.get(f"/books/{book['id']}")
    assert book_response.status_code == 200
    assert book_response.get_json() == book

    loans_response = client.get("/loans")
    assert loans_response.status_code == 200
    assert loans_response.get_json() == [returned]
 
 
def test_repeated_return_preserves_book_and_loan(client, lending_records):
    book = lending_records["book"]
    member = lending_records["member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()

    first_return = client.put(f"/loans/{loan['id']}/return")
    assert first_return.status_code == 200
    returned_loan = first_return.get_json()

    before_response = client.get(f"/books/{book['id']}")
    assert before_response.status_code == 200
    assert before_response.get_json() == book

    second_return = client.put(f"/loans/{loan['id']}/return")

    assert second_return.status_code == 400
    assert second_return.get_json() == {"error": "Loan already returned"}

    after_response = client.get(f"/books/{book['id']}")
    assert after_response.status_code == 200
    assert after_response.get_json() == book

    loans_response = client.get("/loans")
    assert loans_response.status_code == 200
    assert loans_response.get_json() == [returned_loan]  
    
    



@pytest.mark.parametrize("filter_name", ["book_id", "member_id"])
def test_loan_filters_return_matching_records(client, lending_records, filter_name):
    first_book = lending_records["book"]
    first_member = lending_records["member"]
    second_member = lending_records["other_member"]

    book_response = client.post("/books", json={
        "title": "Second Loan Book",
        "author": "Another Author",
        "isbn": "9780134685991",
        "total_copies": 1,
    })
    assert book_response.status_code == 201
    second_book = book_response.get_json()

    first_response = client.post("/loans", json={
        "book_id": first_book["id"],
        "member_id": second_member["id"],
    })
    second_response = client.post("/loans", json={
        "book_id": second_book["id"],
        "member_id": first_member["id"],
    })

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    first_loan = first_response.get_json()

    response = client.get(
        "/loans",
        query_string={filter_name: first_loan[filter_name]},
    )

    assert response.status_code == 200
    assert response.get_json() == [first_loan] 
    
def test_renewal_updates_only_due_date(client, lending_records):
    book = lending_records["book"]
    member = lending_records["member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()
    original_due_date = date.fromisoformat(loan["due_date"])

    renewal_response = client.put(f"/loans/{loan['id']}/renew")

    assert renewal_response.status_code == 200
    renewed = renewal_response.get_json()
    new_due_date = date.fromisoformat(renewed["due_date"])
    assert new_due_date > original_due_date

    expected_loan = loan.copy()
    expected_loan["due_date"] = renewed["due_date"]
    assert renewed == expected_loan

    loans_response = client.get(
        "/loans", query_string={"book_id": book["id"]}
    )
    assert loans_response.status_code == 200
    assert loans_response.get_json() == [renewed]

    book_response = client.get(f"/books/{book['id']}")
    assert book_response.status_code == 200
    expected_book = book.copy()
    expected_book["available_copies"] = 0
    assert book_response.get_json() == expected_book
    
    
    
def test_another_members_hold_blocks_renewal(client, lending_records):
    book = lending_records["book"]
    borrower = lending_records["member"]
    waiting_member = lending_records["other_member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": borrower["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()

    reservation_response = client.post("/reservations", json={
        "book_id": book["id"],
        "member_id": waiting_member["id"],
    })
    assert reservation_response.status_code == 201
    reservation = reservation_response.get_json()
    assert reservation["fulfilled"] is False

    renewal_response = client.put(f"/loans/{loan['id']}/renew")

    loans_response = client.get(
        "/loans", query_string={"book_id": book["id"]}
    )
    reservations_response = client.get(
        "/reservations", query_string={"book_id": book["id"]}
    )

    assert loans_response.status_code == 200
    assert reservations_response.status_code == 200
    assert reservations_response.get_json() == [reservation]
    assert loans_response.get_json() == [loan]
    assert renewal_response.status_code in (400, 409)
    
    
    
def test_returned_loan_cannot_be_renewed(client, lending_records):
    book = lending_records["book"]
    member = lending_records["member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()

    return_response = client.put(f"/loans/{loan['id']}/return")
    assert return_response.status_code == 200
    returned_loan = return_response.get_json()

    renewal_response = client.put(f"/loans/{loan['id']}/renew")

    assert renewal_response.status_code == 400
    assert renewal_response.get_json() == {"error": "Loan already returned"}

    loans_response = client.get(
        "/loans", query_string={"book_id": book["id"]}
    )
    assert loans_response.status_code == 200
    assert loans_response.get_json() == [returned_loan]

    book_response = client.get(f"/books/{book['id']}")
    assert book_response.status_code == 200
    assert book_response.get_json() == book
    
    
    
@pytest.mark.parametrize(
    "method, operation",
    [("PUT", "return"), ("PUT", "renew"), ("GET", "fine")],
)
def test_unknown_loan_id_preserves_records(client, lending_records, method, operation):
    book = lending_records["book"]
    member = lending_records["member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()
    unknown_id = loan["id"] + 1000

    response = client.open(
        f"/loans/{unknown_id}/{operation}", method=method
    )

    assert response.status_code == 404
    assert response.get_json() == {"error": "Loan not found"}

    loans_response = client.get("/loans")
    assert loans_response.status_code == 200
    assert loans_response.get_json() == [loan]

    book_response = client.get(f"/books/{book['id']}")
    assert book_response.status_code == 200
    expected_book = book.copy()
    expected_book["available_copies"] = 0
    assert book_response.get_json() == expected_book
    
    
@pytest.fixture
def fine_reference_day(monkeypatch):
    reference_day = date.today()

    class FixedDate(date):
        @classmethod
        def today(cls):
            return reference_day

    monkeypatch.setattr("app.routes.loans.date", FixedDate)
    return reference_day


@pytest.mark.parametrize(
    "due_offset, return_offset, expected_fine",
    [
        (3, None, 0.0),
        (0, None, 0.0),
        (-3, None, 0.75),
        (-3, -4, 0.0),
        (-3, -2, 0.25),
    ],
    ids=[
        "not_due",
        "due_today",
        "active_three_days_overdue",
        "returned_before_due",
        "returned_one_day_late",
    ],
)
def test_fine_uses_due_and_return_dates(
    client, lending_records, fine_reference_day,
    due_offset, return_offset, expected_fine,
):
    book = lending_records["book"]
    member = lending_records["member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })
    assert checkout_response.status_code == 201
    loan_id = checkout_response.get_json()["id"]

    stored_loan = store.loans[loan_id]
    stored_loan.due_date = fine_reference_day + timedelta(days=due_offset)
    stored_loan.loan_date = stored_loan.due_date - timedelta(days=14)

    if return_offset is not None:
        return_response = client.put(f"/loans/{loan_id}/return")
        assert return_response.status_code == 200
        stored_loan.return_date = (
            fine_reference_day + timedelta(days=return_offset)
        )

    loan_before = stored_loan.to_dict()
    fine_response = client.get(f"/loans/{loan_id}/fine")

    assert fine_response.status_code == 200
    result = fine_response.get_json()
    assert result["loan_id"] == loan_id
    assert result["fine_amount"] == pytest.approx(expected_fine)
    assert stored_loan.to_dict() == loan_before
    
    
def test_created_reservation_is_saved_and_retrievable(client, lending_records):
    book = lending_records["book"]
    borrower = lending_records["member"]
    waiting_member = lending_records["other_member"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": borrower["id"],
    })
    assert checkout_response.status_code == 201

    date_before = date.today()
    create_response = client.post("/reservations", json={
        "book_id": book["id"],
        "member_id": waiting_member["id"],
    })
    date_after = date.today()

    assert create_response.status_code == 201
    reservation = create_response.get_json()
    assert reservation["book_id"] == book["id"]
    assert reservation["member_id"] == waiting_member["id"]
    assert reservation["fulfilled"] is False

    reservation_date = date.fromisoformat(reservation["reservation_date"])
    assert date_before <= reservation_date <= date_after

    list_response = client.get("/reservations")
    assert list_response.status_code == 200
    assert list_response.get_json() == [reservation]

    book_response = client.get(f"/books/{book['id']}")
    assert book_response.status_code == 200
    expected_book = book.copy()
    expected_book["available_copies"] = 0
    assert book_response.get_json() == expected_book   


@pytest.fixture
def reservation_records(client, lending_records):
    first_book = lending_records["book"]
    first_member = lending_records["member"]
    second_member = lending_records["other_member"]

    book_response = client.post("/books", json={
        "title": "Second Reserved Book",
        "author": "Another Author",
        "isbn": "9780134685991",
        "total_copies": 1,
    })
    assert book_response.status_code == 201
    second_book = book_response.get_json()

    first_checkout = client.post("/loans", json={
        "book_id": first_book["id"],
        "member_id": first_member["id"],
    })
    second_checkout = client.post("/loans", json={
        "book_id": second_book["id"],
        "member_id": second_member["id"],
    })
    assert first_checkout.status_code == 201
    assert second_checkout.status_code == 201

    first_response = client.post("/reservations", json={
        "book_id": first_book["id"],
        "member_id": second_member["id"],
    })
    second_response = client.post("/reservations", json={
        "book_id": second_book["id"],
        "member_id": first_member["id"],
    })
    assert first_response.status_code == 201
    assert second_response.status_code == 201

    return {
        "first": first_response.get_json(),
        "second": second_response.get_json(),
    }


def test_list_reservations_returns_all_records(client, reservation_records):
    response = client.get("/reservations")

    assert response.status_code == 200
    reservations = response.get_json()
    assert len(reservations) == 2

    actual_by_id = {
        reservation["id"]: reservation
        for reservation in reservations
    }
    expected_by_id = {
        reservation["id"]: reservation
        for reservation in reservation_records.values()
    }
    assert actual_by_id == expected_by_id
    
    
    
@pytest.mark.parametrize(
    "filter_case, should_match",
    [
        ("book", True),
        ("member", True),
        ("both", True),
        ("missing_book", False),
        ("missing_member", False),
        ("nonmatching_pair", False),
    ],
)
def test_reservation_filters_return_matching_records(
    client, reservation_records, filter_case, should_match,
):
    first = reservation_records["first"]
    second = reservation_records["second"]

    queries = {
        "book": {"book_id": first["book_id"]},
        "member": {"member_id": first["member_id"]},
        "both": {
            "book_id": first["book_id"],
            "member_id": first["member_id"],
        },
        "missing_book": {"book_id": first["book_id"] + 1000},
        "missing_member": {"member_id": first["member_id"] + 1000},
        "nonmatching_pair": {
            "book_id": first["book_id"],
            "member_id": second["member_id"],
        },
    }

    response = client.get(
        "/reservations", query_string=queries[filter_case]
    )

    assert response.status_code == 200
    expected = [first] if should_match else []
    assert response.get_json() == expected
    
    
@pytest.mark.parametrize(
    "missing_field, error_message",
    [
        ("book_id", "Book not found"),
        ("member_id", "Member not found"),
    ],
)
def test_reservation_with_unknown_reference_preserves_records(
    client, reservation_records, missing_field, error_message,
):
    first = reservation_records["first"]
    payload = {
        "book_id": first["book_id"],
        "member_id": first["member_id"],
    }
    payload[missing_field] += 1000

    response = client.post("/reservations", json=payload)

    assert response.status_code == 404
    assert response.get_json() == {"error": error_message}

    list_response = client.get("/reservations")
    assert list_response.status_code == 200
    reservations = list_response.get_json()
    assert len(reservations) == 2

    actual_by_id = {
        reservation["id"]: reservation
        for reservation in reservations
    }
    expected_by_id = {
        reservation["id"]: reservation
        for reservation in reservation_records.values()
    }
    assert actual_by_id == expected_by_id
    
    
def test_ui_checkout_blocks_over_lending(client, lending_records):
    book = lending_records["book"]
    borrower = lending_records["member"]
    other_member = lending_records["other_member"]

    first_response = client.post("/ui/loans", data={
        "book_id": book["id"],
        "member_id": borrower["id"],
    })
    assert first_response.status_code == 302

    loans_before = client.get("/loans")
    assert loans_before.status_code == 200
    existing_loans = loans_before.get_json()
    assert len(existing_loans) == 1
    assert existing_loans[0]["book_id"] == book["id"]
    assert existing_loans[0]["member_id"] == borrower["id"]
    assert existing_loans[0]["return_date"] is None

    expected_book = book.copy()
    expected_book["available_copies"] = 0

    book_before = client.get(f"/books/{book['id']}")
    assert book_before.status_code == 200
    assert book_before.get_json() == expected_book

    second_response = client.post("/ui/loans", data={
        "book_id": book["id"],
        "member_id": other_member["id"],
    })

    assert second_response.status_code == 400
    assert "No copies available" in second_response.get_data(as_text=True)

    book_after = client.get(f"/books/{book['id']}")
    assert book_after.status_code == 200
    assert book_after.get_json() == expected_book

    loans_after = client.get("/loans")
    assert loans_after.status_code == 200
    assert loans_after.get_json() == existing_loans



def test_checkout_with_initial_zero_stock_is_rejected(client):
    book_response = client.post("/books", json={
        "title": "Zero Stock Book",
        "author": "Test Author",
        "isbn": "9780132350884",
        "total_copies": 0,
    })
    member_response = client.post("/members", json={
        "name": "Zero Stock Member",
        "email": "zero.stock@example.com",
    })

    assert book_response.status_code == 201
    assert member_response.status_code == 201
    book = book_response.get_json()
    member = member_response.get_json()
    assert book["total_copies"] == 0
    assert book["available_copies"] == 0

    response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": member["id"],
    })

    assert response.status_code == 400
    assert response.get_json() == {"error": "No copies available"}

    book_after = client.get(f"/books/{book['id']}")
    assert book_after.status_code == 200
    assert book_after.get_json() == book

    loans_after = client.get("/loans")
    assert loans_after.status_code == 200
    assert loans_after.get_json() == []


def test_member_without_loans_gets_empty_list(client, lending_records):
    book = lending_records["book"]
    member_without_loans = lending_records["member"]
    borrower = lending_records["other_member"]

    # Deliberately match the book ID and the non-borrowing member's ID.
    assert book["id"] == member_without_loans["id"]
    assert borrower["id"] != member_without_loans["id"]

    checkout_response = client.post("/loans", json={
        "book_id": book["id"],
        "member_id": borrower["id"],
    })
    assert checkout_response.status_code == 201
    loan = checkout_response.get_json()

    response = client.get(
        "/loans",
        query_string={"member_id": member_without_loans["id"]},
    )
    assert response.status_code == 200
    assert response.get_json() == []

    # The lookup must leave the other member's loan unchanged.
    all_loans_response = client.get("/loans")
    assert all_loans_response.status_code == 200
    assert all_loans_response.get_json() == [loan]
    
    
    
def test_combined_loan_filters_require_both_matches(client, lending_records):
    first_book = lending_records["book"]
    first_member = lending_records["member"]
    second_member = lending_records["other_member"]

    book_response = client.post("/books", json={
        "title": "Combined Filter Book",
        "author": "Test Author",
        "isbn": "9780134685991",
        "total_copies": 1,
    })
    assert book_response.status_code == 201
    second_book = book_response.get_json()

    first_checkout = client.post("/loans", json={
        "book_id": first_book["id"],
        "member_id": second_member["id"],
    })
    second_checkout = client.post("/loans", json={
        "book_id": second_book["id"],
        "member_id": first_member["id"],
    })
    assert first_checkout.status_code == 201
    assert second_checkout.status_code == 201
    second_loan = second_checkout.get_json()

    matching_response = client.get("/loans", query_string={
        "book_id": second_book["id"],
        "member_id": first_member["id"],
    })
    assert matching_response.status_code == 200
    assert matching_response.get_json() == [second_loan]

    nonmatching_response = client.get("/loans", query_string={
        "book_id": first_book["id"],
        "member_id": first_member["id"],
    })
    assert nonmatching_response.status_code == 200
    assert nonmatching_response.get_json() == []