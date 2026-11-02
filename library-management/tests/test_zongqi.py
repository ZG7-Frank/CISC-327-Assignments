
import pytest
from datetime import date


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