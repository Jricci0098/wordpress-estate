from wp_estate_agent.simulate import generate_simulated_inventory


def test_simulated_payload_has_expected_shape():
    payload = generate_simulated_inventory(agent_id="agent-demo")

    assert payload["schema_version"] == "inventory/v1"
    assert payload["agent_id"] == "agent-demo"
    assert payload["request_id"]
    assert payload["timestamp"]
    assert len(payload["sites"]) == 5
    assert {s["site_name"] for s in payload["sites"]} == {
        "wp1",
        "wp2",
        "wp3",
        "wp4",
        "wp5",
    }
    assert {s["site_url"] for s in payload["sites"]} == {
        "http://localhost:8181",
        "http://localhost:8182",
        "http://localhost:8183",
        "http://localhost:8184",
        "http://localhost:8185",
    }


def test_simulated_payload_covers_all_origin_and_kind_variants():
    payload = generate_simulated_inventory(agent_id="agent-demo")

    all_plugins = [p for site in payload["sites"] for p in site["plugins"]]
    origins = {p["origin"] for p in all_plugins}
    kinds = {p["kind"] for p in all_plugins}

    assert {"wordpress_org", "commercial", "custom", "unknown"} <= origins
    assert {"plugin", "mu-plugin", "dropin"} <= kinds


def test_simulated_payload_never_marks_non_wordpress_org_as_current():
    payload = generate_simulated_inventory(agent_id="agent-demo")

    for site in payload["sites"]:
        for plugin in site["plugins"]:
            if plugin["origin"] != "wordpress_org":
                assert plugin["update_status"] != "current"


def test_simulated_payload_has_unique_request_id_per_call():
    first = generate_simulated_inventory(agent_id="agent-demo")
    second = generate_simulated_inventory(agent_id="agent-demo")
    assert first["request_id"] != second["request_id"]
