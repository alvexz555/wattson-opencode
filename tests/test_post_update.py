from wattson_core.update_manager.post_update import (
    PostUpdateValidator,
)


def test_post_update_passes_when_sha_and_tests_are_valid():
    validator = PostUpdateValidator()

    result = validator.validate(
        target_commit="def456",
        current_commit="def456",
        tests_passed=True,
    )

    assert result.success is True


def test_post_update_fails_when_sha_is_wrong():
    validator = PostUpdateValidator()

    result = validator.validate(
        target_commit="def456",
        current_commit="abc123",
        tests_passed=True,
    )

    assert result.success is False


def test_post_update_fails_when_tests_fail():
    validator = PostUpdateValidator()

    result = validator.validate(
        target_commit="def456",
        current_commit="def456",
        tests_passed=False,
    )

    assert result.success is False
