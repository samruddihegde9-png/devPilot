def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_create_project_creates_workspace_with_real_files(client):
    res = client.post("/api/projects", json={"name": "My App", "template": "fastapi"})
    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "My App"
    assert body["template"] == "fastapi"
    project_id = body["id"]

    # The workspace must actually exist on disk with real starter files —
    # not just a database row.
    tree_res = client.get(f"/api/projects/{project_id}/files")
    assert tree_res.status_code == 200
    paths = {node["path"] for node in tree_res.json()}
    assert "README.md" in paths
    assert "app" in paths


def test_list_projects(client):
    client.post("/api/projects", json={"name": "A", "template": "python"})
    client.post("/api/projects", json={"name": "B", "template": "node"})

    res = client.get("/api/projects")
    assert res.status_code == 200
    names = {p["name"] for p in res.json()}
    assert names == {"A", "B"}


def test_get_missing_project_404(client):
    res = client.get("/api/projects/does-not-exist")
    assert res.status_code == 404


def test_delete_project_removes_workspace(client):
    create_res = client.post("/api/projects", json={"name": "Temp", "template": "python"})
    project_id = create_res.json()["id"]

    del_res = client.delete(f"/api/projects/{project_id}")
    assert del_res.status_code == 204

    get_res = client.get(f"/api/projects/{project_id}")
    assert get_res.status_code == 404

    tree_res = client.get(f"/api/projects/{project_id}/files")
    assert tree_res.status_code == 404


def test_invalid_template_rejected(client):
    res = client.post("/api/projects", json={"name": "Bad", "template": "cobol"})
    assert res.status_code == 422
