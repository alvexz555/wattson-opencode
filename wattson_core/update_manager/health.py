from dataclasses import dataclass
import sys

from wattson_core.executor.runner import run_command


@dataclass(frozen=True)
class HealthCheckResult:
    pytest_passed: bool
    imports_passed: bool
    startup_passed: bool
    adr0_passed: bool

    @property
    def success(self) -> bool:
        return all(
            (
                self.pytest_passed,
                self.imports_passed,
                self.startup_passed,
                self.adr0_passed,
            )
        )


class PostUpdateHealthChecker:
    def __init__(self, repository_path="."):
        self.repository_path = repository_path

    def run_pytest(self) -> bool:
        result = run_command(
            [
                sys.executable,
                "-m",
                "pytest",
                "-m",
                "not integration",
            ],
            cwd=self.repository_path,
        )
        return result.returncode == 0

    def check_imports(self) -> bool:
        result = run_command(
            [
                sys.executable,
                "-c",
                (
                    "import wattson_core; "
                    "import wattson_core.core.orchestrator; "
                    "import wattson_core.terminal_runner; "
                    "import wattson_core.update_manager.git; "
                    "import wattson_core.update_manager.health; "
                    "import wattson_core.diagnostics.adr0"
                ),
            ],
            cwd=self.repository_path,
        )
        return result.returncode == 0

    def check_startup(self) -> bool:
        result = run_command(
            [
                sys.executable,
                "-c",
                (
                    "from wattson_core.terminal_runner "
                    "import create_wattson; "
                    "create_wattson()"
                ),
            ],
            cwd=self.repository_path,
        )
        return result.returncode == 0

    def check_adr0(self) -> bool:
        result = run_command(
            [
                sys.executable,
                "-m",
                "wattson_core.adr0",
                "--format",
                "json",
            ],
            cwd=self.repository_path,
        )
        return result.returncode == 0

    def run_all(self) -> HealthCheckResult:
        return HealthCheckResult(
            pytest_passed=self.run_pytest(),
            imports_passed=self.check_imports(),
            startup_passed=self.check_startup(),
            adr0_passed=self.check_adr0(),
        )

    def validate(
        self,
        pytest_passed: bool,
        imports_passed: bool,
        startup_passed: bool,
        adr0_passed: bool,
    ) -> HealthCheckResult:
        return HealthCheckResult(
            pytest_passed=pytest_passed,
            imports_passed=imports_passed,
            startup_passed=startup_passed,
            adr0_passed=adr0_passed,
        )
