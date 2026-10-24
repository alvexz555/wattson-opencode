from wattson_core.update_manager.health import PostUpdateHealthChecker


def test_health_passes_when_all_checks_pass():
    checker = PostUpdateHealthChecker()

    result = checker.validate(
        pytest_passed=True,
        imports_passed=True,
        startup_passed=True,
        adr0_passed=True,
    )

    assert result.success is True


def test_health_fails_when_pytest_fails():
    checker = PostUpdateHealthChecker()

    result = checker.validate(
        pytest_passed=False,
        imports_passed=True,
        startup_passed=True,
        adr0_passed=True,
    )

    assert result.success is False


def test_health_fails_when_startup_fails():
    checker = PostUpdateHealthChecker()

    result = checker.validate(
        pytest_passed=True,
        imports_passed=True,
        startup_passed=False,
        adr0_passed=True,
    )

    assert result.success is False


def test_health_fails_when_adr0_fails():
    checker = PostUpdateHealthChecker()

    result = checker.validate(
        pytest_passed=True,
        imports_passed=True,
        startup_passed=True,
        adr0_passed=False,
    )

    assert result.success is False
