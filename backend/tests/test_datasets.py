import io


def _upload_csv(client, headers, csv_text, name):
    files = {"file": ("data.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    resp = client.post("/dataset", files=files, data={"name": name}, headers=headers)
    assert resp.status_code == 201, resp.json()
    return resp.json()


def test_upload_rejects_non_csv(client, auth_headers):
    files = {"file": ("data.txt", io.BytesIO(b"not a csv"), "text/plain")}
    resp = client.post(
        "/dataset", files=files, data={"name": "x"}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_upload_requires_name(client, auth_headers):
    files = {"file": ("data.csv", io.BytesIO(b"a,b\n1,2\n"), "text/csv")}
    resp = client.post(
        "/dataset", files=files, data={"name": "   "}, headers=auth_headers
    )
    assert resp.status_code == 400


def test_preview_returns_up_to_25_rows(client, auth_headers):
    rows = "\n".join(f"{i}" for i in range(40))
    csv_text = "n\n" + rows + "\n"
    dataset = _upload_csv(client, auth_headers, csv_text, "big")

    resp = client.get(f"/dataset/{dataset['id']}/preview", headers=auth_headers)
    body = resp.json()
    assert body["row_count"] == 40
    assert body["previewed"] == 25
    assert len(body["rows"]) == 25


def test_delete_dataset(client, auth_headers):
    dataset = _upload_csv(client, auth_headers, "a,b\n1,2\n", "to-delete")

    resp = client.delete(f"/dataset/{dataset['id']}", headers=auth_headers)
    assert resp.status_code == 200

    resp = client.get(f"/dataset/{dataset['id']}/preview", headers=auth_headers)
    assert resp.status_code == 404  # gone, and 404 not 403 per dataset_service


def test_cannot_access_another_users_dataset(client):
    # user A uploads
    client.post("/auth/register", json={"email": "owner@example.com", "password": "password123"})
    login_a = client.post(
        "/auth/login", json={"email": "owner@example.com", "password": "password123"}
    )
    headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
    dataset = _upload_csv(client, headers_a, "a,b\n1,2\n", "private")

    # user B tries to read it
    client.post("/auth/register", json={"email": "other@example.com", "password": "password123"})
    login_b = client.post(
        "/auth/login", json={"email": "other@example.com", "password": "password123"}
    )
    headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}

    resp = client.get(f"/dataset/{dataset['id']}/preview", headers=headers_b)
    assert resp.status_code == 404  # not 403 -- doesn't confirm the id exists


def test_plot_returns_paired_points(client, auth_headers):
    dataset = _upload_csv(
        client, auth_headers, "x,y\n1,10\n2,20\n3,30\n", "xy"
    )
    resp = client.get(
        f"/dataset/{dataset['id']}/plot",
        params={"col1": "x", "col2": "y"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    points = resp.json()["points"]
    assert len(points) == 3
    assert points[0] == {"x": "1", "y": "10"}


def test_plot_rejects_unknown_column(client, auth_headers):
    dataset = _upload_csv(client, auth_headers, "x,y\n1,2\n", "xy2")
    resp = client.get(
        f"/dataset/{dataset['id']}/plot",
        params={"col1": "x", "col2": "does_not_exist"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


# ---------------------------------------------------------------------
# Pagination: the spec explicitly says this "must be genuinely
# implemented, not stubbed -- verify with a dataset list >1 page." This
# is that verification: 5 datasets, limit=2, and we check page contents
# actually change (not the same 2 items repeated) plus that total/
# total_pages are computed correctly from the DB, not the page slice.
# ---------------------------------------------------------------------

def test_pagination_across_multiple_pages(client, auth_headers):
    for i in range(5):
        _upload_csv(client, auth_headers, "a,b\n1,2\n", f"dataset-{i}")

    page1 = client.get(
        "/dataset", params={"page": 1, "limit": 2}, headers=auth_headers
    ).json()
    page2 = client.get(
        "/dataset", params={"page": 2, "limit": 2}, headers=auth_headers
    ).json()
    page3 = client.get(
        "/dataset", params={"page": 3, "limit": 2}, headers=auth_headers
    ).json()

    assert page1["total"] == 5
    assert page1["total_pages"] == 3
    assert len(page1["items"]) == 2
    assert len(page2["items"]) == 2
    assert len(page3["items"]) == 1  # last page has the remainder

    # No overlap between pages -- proves it's a real OFFSET, not the
    # same slice of an in-memory list returned three times.
    ids_page1 = {d["id"] for d in page1["items"]}
    ids_page2 = {d["id"] for d in page2["items"]}
    ids_page3 = {d["id"] for d in page3["items"]}
    assert not (ids_page1 & ids_page2)
    assert not (ids_page2 & ids_page3)


def test_pagination_limit_is_capped(client, auth_headers):
    _upload_csv(client, auth_headers, "a,b\n1,2\n", "single")
    resp = client.get(
        "/dataset", params={"page": 1, "limit": 9999}, headers=auth_headers
    )
    body = resp.json()
    assert body["limit"] == 100  # settings.max_page_size, not the raw 9999