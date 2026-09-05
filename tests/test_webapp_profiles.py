import webapp


def test_profile_view_uses_selected_model(monkeypatch):
    entities = {
        "u1": "sensor.grid_voltage",
        "i1": "sensor.grid_current",
        "p_total": "sensor.grid_power",
        "freq": "sensor.grid_frequency",
        "p1": "sensor.grid_power",
    }
    monkeypatch.setattr(webapp, "get_ha_entities", lambda: entities)

    profile = webapp._profile_view("inepro_pro2")

    assert profile["key"] == "inepro_pro2"
    assert profile["label"] == "Inepro PRO2-Mod"
    assert "i1" in profile["required"]
    assert profile["fields"]
    assert next(field for field in profile["fields"] if field["key"] == "i1")["role"] == "required"
    assert next(field for field in profile["fields"] if field["key"] == "u2")["role"] == "not_used"


def test_settings_page_renders_active_profile_and_configuration(monkeypatch):
    monkeypatch.setattr(webapp, "get_meter_model", lambda: "inepro_pro2")
    monkeypatch.setattr(
        webapp,
        "get_ha_entities",
        lambda: {"i1": "sensor.grid_current"},
    )

    response = webapp.app.test_client().get("/settings")

    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Inepro PRO2-Mod" in body
    assert "inepro_pro2" in body
    assert "sensor.grid_current" in body
    assert "Current L1" in body


def test_state_api_exposes_active_meter_profile(monkeypatch):
    monkeypatch.setattr(webapp, "get_meter_model", lambda: "janitza_b23")
    monkeypatch.setattr(webapp, "get_ha_entities", lambda: {})

    response = webapp.app.test_client().get("/api/state")

    assert response.status_code == 200
    data = response.get_json()
    assert data["meter_model"] == "janitza_b23"
    assert data["meter_profile"]["current_register"] == "0x5B0C"
