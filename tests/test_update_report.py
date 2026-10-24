from wattson_core.update_manager.report import UpdateReport


def test_update_report_records_successful_update():
    report = UpdateReport.create(
        initiator="orchestrator",
        current_commit="abc123",
        target_commit="def456",
        pytest_passed=True,
        imports_passed=True,
        startup_passed=True,
        adr0_passed=True,
        applied=True,
        rollback=False,
        error=None,
        final_state="active",
    )

    assert report.current_commit == "abc123"
    assert report.target_commit == "def456"
    assert report.applied is True
    assert report.rollback is False
    assert report.error is None
    assert report.final_state == "active"
    assert report.timestamp
    assert report.device


def test_update_report_records_failed_update_and_rollback():
    report = UpdateReport.create(
        initiator="orchestrator",
        current_commit="abc123",
        target_commit="def456",
        pytest_passed=False,
        imports_passed=True,
        startup_passed=True,
        adr0_passed=True,
        applied=True,
        rollback=True,
        error="pytest failed",
        final_state="previous_version_active",
    )

    assert report.applied is True
    assert report.rollback is True
    assert report.error == "pytest failed"
    assert report.final_state == "previous_version_active"
    assert report.pytest_passed is False


def test_update_report_serializes_to_json():
    report = UpdateReport.create(
        initiator="test",
        current_commit="abc123",
        target_commit="def456",
        pytest_passed=True,
        imports_passed=True,
        startup_passed=True,
        adr0_passed=True,
        applied=True,
        rollback=False,
        error=None,
        final_state="active",
    )

    payload = report.to_json()

    assert '"current_commit": "abc123"' in payload
    assert '"target_commit": "def456"' in payload
    assert '"applied": true' in payload
    assert '"rollback": false' in payload
