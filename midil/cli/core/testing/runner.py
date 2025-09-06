# midil/core/testing/runner.py
import subprocess
import sys
from midil.cli.core.testing.options import TestOptions
from midil.cli.core.testing.builder import PytestCommandBuilder
from midil.cli.commands._common import console


class PytestRunner:
    def __init__(self, options: TestOptions):
        self.options = options

    def run(self):
        try:
            builder = PytestCommandBuilder(self.options)
            command = builder.determine_runner().add_options().build()

            if self.options.html_cov:
                console.print(
                    "📊 HTML coverage report will be generated in htmlcov/",
                    style="cyan",
                )

            console.print(f"Running: {' '.join(command)}", style="dim")
            result = subprocess.run(command)

            if result.returncode == 0:
                console.print("✅ All tests passed!", style="green")
            else:
                console.print(
                    f"❌ Tests failed with exit code {result.returncode}", style="red"
                )
            sys.exit(result.returncode)

        except FileNotFoundError as e:
            console.print(f"❌ {e}", style="red")
            sys.exit(1)
        except KeyboardInterrupt:
            console.print("\n⚠️  Tests interrupted by user", style="yellow")
            sys.exit(1)
        except Exception as e:
            console.print(f"❌ Error running tests: {e}", style="red")
            sys.exit(1)
