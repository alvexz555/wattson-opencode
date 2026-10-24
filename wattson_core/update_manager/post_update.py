from dataclasses import dataclass


@dataclass(frozen=True)
class PostUpdateValidation:
    target_commit: str
    current_commit: str
    tests_passed: bool

    @property
    def success(self) -> bool:
        return (
            self.current_commit == self.target_commit
            and self.tests_passed
        )


class PostUpdateValidator:
    def validate(
        self,
        target_commit: str,
        current_commit: str,
        tests_passed: bool,
    ) -> PostUpdateValidation:
        return PostUpdateValidation(
            target_commit=target_commit,
            current_commit=current_commit,
            tests_passed=tests_passed,
        )
