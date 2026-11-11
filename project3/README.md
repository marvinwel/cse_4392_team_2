# Team Assignment 3: A Multi-Agent System for Testing and Refactoring

This guide shows how to set up a Python virtual environment with **uv**, install the project's libraries from `app/requirements.txt`, and run the app from `app/main.py`.

## 1. Install uv

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
or with Homebrew:
```bash
brew install uv
```

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart your terminal, then check that it worked:
```bash
uv --version
```

## 2. Create the virtual environment

From the **project root folder** (the folder that contains `app/requirements.txt` and `app/`):

```bash
uv venv
```

This creates a `.venv/` folder. To use a specific Python version:
```bash
uv venv --python 3.12
```

## 3. Activate the virtual environment

**macOS / Linux**
```bash
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
.venv\Scripts\Activate.ps1
```

**Windows (Command Prompt)**
```cmd
.venv\Scripts\activate.bat
```

Your terminal prompt should now start with `(.venv)`.

## 4. Install the libraries

```bash
uv pip install -r app/requirements.txt
```




## 5. Configure AWS Credentials


```bash
aws configure
```

Enter your AWS credentials when prompted:

```text
AWS Access Key ID: YOUR_ACCESS_KEY
AWS Secret Access Key: YOUR_SECRET_KEY
Default region name: us-east-1
Default output format: json
```

## 6. Verify AWS Connection

Run:

```bash
aws sts get-caller-identity
```

Expected output:

```json
{
    "UserId": "AIDAEXAMPLE",
    "Account": "123456789012",
    "Arn": "arn:aws:iam::123456789012:user/tam2Admin"
}
```

**Note:** Never commit your AWS access keys to GitHub.




## 7. Run the app

From the **project root** (not from inside `app/`):

```bash
python app/main.py
```

If `main.py` imports other modules from the `app` package (for example `from app.agents import ...`), run it as a module instead:
```bash
python -m app.main
```

You can also skip activating the environment and let uv run it for you:
```bash
uv run python app/main.py
```


## 8. Development and Testing Commands

Run all commands from the `project3/` root directory.

### Prerequisites

- Python with the dependencies from `app/requirements.txt`
- JDK 17 or newer
- Apache Maven installed and available on PATH
- AWS Bedrock credentials for the AI workflow

These commands are designed for macOS/Linux shells.
On Windows, use WSL or a compatible Unix environment.

### Available Commands

| Command | Description |
|---|---|
| `make help` | Display available commands |
| `make run` | Run the current LangGraph workflow, automatically building the merger JAR if needed |
| `make test-original` | Copy the latest generated tests into the original Java project and run JUnit/JaCoCo |
| `make test-original-current` | Rerun installed original tests without generating or copying new ones |
| `make test-refactored` | Execute the installed adapted tests against the refactored Java implementation |
| `make verify-original` | Strict Maven verification requiring passing tests and 100% branch coverage |
| `make verify-refactored` | Strict Maven verification for the refactored implementation |
| `make test-python` | Run Python unit tests without invoking an LLM or Maven |
| `make check` | Validate Python syntax |
| `make build-merger` | Force a clean rebuild of the Java JUnit merger |
| `make clean` | Remove Java testing build outputs while retaining the merger JAR |
| `make clean-all` | Clean all three Maven projects, including the merger |

### Standard Workflow

Generate and execute a new suite:

```bash
make run
```

The current workflow uses LLM-generated EP/BVA tests,
merges them, performs an AI review, and executes tests
when its review accepts the suite.

To independently execute the latest generated suite
and display JUnit results and JaCoCo branch coverage:

```bash
make test-original
```

This command copies:

`generated_tests/SeasonSwitchMergedTest.java`

into:

`java-original/src/test/java/cse4392/`

WARNING: This overwrites the previously installed
merged test file. Preserve any manual changes first.

### Repeating Tests Without Regeneration

To run the same installed test suite again:

```bash
make test-original-current
```

This does not call the LLM, regenerate tests, or copy
new test source files.

It does perform a fresh Maven build.

### Strict Acceptance Verification

For original Java code:

```bash
make verify-original
```

For refactored Java code, after the State-pattern
implementation and adapted tests are available:

```bash
make verify-refactored
```

These commands use Maven's strict verification gate.
A build fails when tests fail or the required 100%
branch coverage is not achieved.


**Difference between testing and verification:**

- `make test-original` copies the latest AI-generated merged test suite into the original Java project, then runs that test class and reports JUnit results and JaCoCo branch coverage.
- `make test-original-current` reruns the previously installed merged test suite without copying or regenerating tests.
- `make verify-original` executes Maven's full verification lifecycle, including all discovered JUnit tests (such as `SeasonSwitchSmokeTest`), rather than only the AI-generated merged test class. This is the strict acceptance check for passing tests and the required 100% branch coverage.
- `make verify-refactored` performs the equivalent strict verification against the refactored Java project once that implementation is available.

Use `make test-original` to inspect the latest AI-generated tests. Use `make verify-original` to determine whether the complete original Java project satisfies its Maven verification requirements.


### Python Development Checks

Run these after modifying Python source:

```bash
make check
make test-python
```

They do not require AWS Bedrock or Maven execution.

### Maven Cleaning

The Python Java testing tool already runs Maven with:

`clean verify`

Therefore, `make test-original`,
`make test-original-current`, and
`make test-refactored` automatically remove old Maven
build outputs before testing.

Manual cleanup is available:

```bash
make clean
```

This cleans original/refactored Maven build directories
without removing Marvin's merger JAR.

For a complete Maven build reset:

```bash
make clean-all
```

The next `make run` automatically rebuilds the missing
merger JAR.

WARNING: Cleaning deletes existing Maven reports under
each project's `target/` directory. Save any evidence
required for submission before cleaning.

### Test Results and Coverage Reports

JUnit/Surefire reports:

`java-original/target/surefire-reports/`

JaCoCo HTML coverage report:

`java-original/target/site/jacoco/index.html`

The refactored project uses corresponding paths under
`java-refactored/`.

The Java testing commands report test failures and
branch coverage separately.

A nonzero exit status may indicate failed tests,
incomplete coverage, or a build problem.

### Current Implementation Status

The Makefile provides consistent commands for the
workflow currently implemented.

The project still needs its required human approval
stages, complete repair/coverage-gap handling, and
State-pattern refactoring integration.

Running `make run` does not by itself establish
completion of the professor's requirements.
