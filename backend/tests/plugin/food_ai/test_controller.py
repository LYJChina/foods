from fastapi.testclient import TestClient

VALID_PRECHECK = {
    "product_name": "潮州糖果示例产品",
    "product_category": "candy",
    "target_market": "EU",
    "materials": ["label_image", "product_spec"],
    "contains_core_data": False,
}


def test_create_and_query_precheck_without_authentication(test_client: TestClient) -> None:
    created = test_client.post("/food-ai/prechecks", json=VALID_PRECHECK)

    assert created.status_code == 201
    created_body = created.json()
    assert created_body["success"] is True
    assert created_body["data"]["status"] == "completed"
    assert created_body["data"]["result"]["is_demo"] is True

    task_id = created_body["data"]["task_id"]
    fetched = test_client.get(f"/food-ai/prechecks/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["task_id"] == task_id


def test_precheck_rejects_invalid_request(test_client: TestClient) -> None:
    invalid = {key: value for key, value in VALID_PRECHECK.items() if key != "target_market"}
    response = test_client.post("/food-ai/prechecks", json=invalid)

    assert response.status_code == 422
    assert response.json()["success"] is False


def test_precheck_rejects_declared_core_data(test_client: TestClient) -> None:
    response = test_client.post(
        "/food-ai/prechecks",
        json={**VALID_PRECHECK, "contains_core_data": True},
    )

    assert response.status_code == 400
    assert "核心数据" in response.json()["msg"]


def test_missing_precheck_returns_not_found(test_client: TestClient) -> None:
    response = test_client.get("/food-ai/prechecks/not-a-real-task")

    assert response.status_code == 404
    assert response.json()["success"] is False
    assert response.json()["msg"] == "预检任务不存在"


def test_portal_summary_is_explicitly_sample_data(test_client: TestClient) -> None:
    response = test_client.get("/food-ai/portal/summary")

    assert response.status_code == 200
    assert response.json()["data"] == {
        "service_count": 4,
        "scenario_count": 6,
        "output_mode_count": 2,
        "diagnosis_class_count": 3,
        "is_demo": True,
        "data_label": "样例数据，非实时统计",
    }


def test_diagnosis_returns_three_action_classes(test_client: TestClient) -> None:
    response = test_client.post(
        "/food-ai/diagnoses",
        json={
            "digital_foundation": 1,
            "data_readiness": 0,
            "ai_experience": 1,
            "governance_readiness": 0,
            "export_need": 2,
        },
    )

    assert response.status_code == 201
    data = response.json()["data"]
    assert data["is_demo"] is True
    assert set(data["recommendations"]) == {
        "public_platform",
        "light_poc",
        "enterprise_project",
    }
