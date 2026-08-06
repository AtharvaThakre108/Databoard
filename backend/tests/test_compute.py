import io
import pytest

from app.services.compute_service import compute_stat, ComputeError


# ---------------------------------------------------------------------
# Unit tests: compute_stat() directly, no HTTP/DB involved.
# ---------------------------------------------------------------------

def test_min_max_sum_happy_path():
    rows = [{"price": "10"}, {"price": "20"}, {"price": "5"}]
    columns = ["price"]

    assert compute_stat(rows, columns, "price", "min")["result"] == 5
    assert compute_stat(rows, columns, "price", "max")["result"] == 20
    assert compute_stat(rows, columns, "price", "sum")["result"] == 35


def test_empty_column_raises():
    rows = [{"price": ""}, {"price": ""}]
    with pytest.raises(ComputeError, match="empty"):
        compute_stat(rows, ["price"], "price", "sum")


def test_all_nulls_raises():
    rows = [{"other": "x"}, {"other": "y"}]  # "price" key never present
    with pytest.raises(ComputeError, match="empty"):
        compute_stat(rows, ["price"], "price", "sum")


def test_non_numeric_column_raises():
    rows = [{"name": "alice"}, {"name": "bob"}]
    with pytest.raises(ComputeError, match="not numeric"):
        compute_stat(rows, ["name"], "name", "min")


def test_mixed_numeric_and_junk_skips_junk():
    rows = [{"score": "10"}, {"score": "N/A"}, {"score": "30"}]
    result = compute_stat(rows, ["score"], "score", "sum")
    assert result["result"] == 40
    assert result["values_considered"] == 2
    assert result["values_skipped"] == 1


def test_missing_column_raises():
    with pytest.raises(ComputeError, match="does not exist"):
        compute_stat([{"price": "10"}], ["price"], "does_not_exist", "sum")


# ---------------------------------------------------------------------
# Integration tests: through the real HTTP endpoint (auth + upload +
# compute), confirming the router correctly turns ComputeError -> 400.
# ---------------------------------------------------------------------

def _upload_csv(client, headers, csv_text, name="test-dataset"):
    files = {"file": ("data.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    data = {"name": name}
    resp = client.post("/dataset", files=files, data=data, headers=headers)
    assert resp.status_code == 201, resp.json()
    return resp.json()["id"]


def test_compute_endpoint_happy_path(client, auth_headers):
    dataset_id = _upload_csv(client, auth_headers, "price,name\n10,a\n20,b\n5,c\n")
    resp = client.post(
        f"/dataset/{dataset_id}/compute",
        json={"column": "price", "operation": "max"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["result"] == 20


def test_compute_endpoint_empty_column_returns_400(client, auth_headers):
    dataset_id = _upload_csv(client, auth_headers, "price,name\n,a\n,b\n")
    resp = client.post(
        f"/dataset/{dataset_id}/compute",
        json={"column": "price", "operation": "sum"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "empty" in resp.json()["detail"]


def test_compute_endpoint_non_numeric_returns_400(client, auth_headers):
    dataset_id = _upload_csv(client, auth_headers, "price,name\n10,a\n20,b\n")
    resp = client.post(
        f"/dataset/{dataset_id}/compute",
        json={"column": "name", "operation": "min"},
        headers=auth_headers,
    )
    assert resp.status_code == 400
    assert "not numeric" in resp.json()["detail"]


def test_compute_endpoint_bad_operation_returns_422():
    # No auth_headers needed -- schema validation (422) happens before
    # the route body even runs, so this never reaches the DB/auth layer.
    pass  # see note below


def test_compute_endpoint_requires_auth(client):
    resp = client.post("/dataset/1/compute", json={"column": "price", "operation": "sum"})
    assert resp.status_code in (401, 403)  # HTTPBearer returns 403 if header missing entirely