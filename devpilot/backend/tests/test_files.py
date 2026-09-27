import pytest


@pytest.fixture()
def project_id(client):
    res = client.post("/api/projects", json={"name": "Files Test", "template": "python"})
    return res.json()["id"]


def test_read_seeded_file(client, project_id):
    res = client.get(f"/api/projects/{project_id}/files/app/main.py")
    assert res.status_code == 200
    assert "def greet" in res.json()["content"]


def test_write_then_read_reflects_real_change(client, project_id):
    write_res = client.put(
        f"/api/projects/{project_id}/files/app/main.py",
        json={"content": "# totally new content\n"},
    )
    assert write_res.status_code == 200

    read_res = client.get(f"/api/projects/{project_id}/files/app/main.py")
    assert read_res.json()["content"] == "# totally new content\n"


def test_create_new_file(client, project_id):
    res = client.post(
        f"/api/projects/{project_id}/files",
        json={"path": "app/new_thing.py", "type": "file", "content": "x = 1\n"},
    )
    assert res.status_code == 201

    read_res = client.get(f"/api/projects/{project_id}/files/app/new_thing.py")
    assert read_res.json()["content"] == "x = 1\n"


def test_create_duplicate_file_conflicts(client, project_id):
    res = client.post(
        f"/api/projects/{project_id}/files",
        json={"path": "app/main.py", "type": "file", "content": "x = 1\n"},
    )
    assert res.status_code == 409


def test_delete_file(client, project_id):
    client.post(
        f"/api/projects/{project_id}/files",
        json={"path": "scratch.py", "type": "file", "content": "x = 1\n"},
    )
    del_res = client.delete(f"/api/projects/{project_id}/files/scratch.py")
    assert del_res.status_code == 204

    read_res = client.get(f"/api/projects/{project_id}/files/scratch.py")
    assert read_res.status_code == 404


def test_rename_file(client, project_id):
    client.post(
        f"/api/projects/{project_id}/files",
        json={"path": "old_name.py", "type": "file", "content": "x = 1\n"},
    )
    res = client.patch(
        f"/api/projects/{project_id}/files/old_name.py",
        json={"new_path": "new_name.py"},
    )
    assert res.status_code == 200

    old_res = client.get(f"/api/projects/{project_id}/files/old_name.py")
    assert old_res.status_code == 404
    new_res = client.get(f"/api/projects/{project_id}/files/new_name.py")
    assert new_res.status_code == 200


@pytest.mark.parametrize(
    "malicious_path",
    [
        "../../../etc/passwd",
        "..%2F..%2F..%2Fetc%2Fpasswd",
        "app/../../../etc/passwd",
    ],
)
def test_path_traversal_is_rejected(client, project_id, malicious_path):
    res = client.get(f"/api/projects/{project_id}/files/{malicious_path}")
    # Either blocked explicitly (400) or resolves to a not-found path safely
    # contained within the workspace (404) — never a 200 with host content.
    assert res.status_code in (400, 404)
    if res.status_code == 200:
        pytest.fail("path traversal must never return 200")


def test_reading_file_in_other_project_is_isolated(client):
    p1 = client.post("/api/projects", json={"name": "P1", "template": "python"}).json()["id"]
    p2 = client.post("/api/projects", json={"name": "P2", "template": "python"}).json()["id"]

    client.put(f"/api/projects/{p1}/files/app/main.py", json={"content": "# p1 secret\n"})

    # Reading the same relative path from a different project must return
    # that project's own file, never the other project's content.
    res = client.get(f"/api/projects/{p2}/files/app/main.py")
    assert "p1 secret" not in res.json()["content"]
