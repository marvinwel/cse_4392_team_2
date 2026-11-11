
# CSE 4392 - Team Assignment 3
# Run all targets from the project3 root directory.

PYTHON ?= python
MAVEN  ?= mvn

TEST_CLASS := SeasonSwitchMergedTest
GENERATED_TEST := generated_tests/$(TEST_CLASS).java
ORIGINAL_TEST := java-original/src/test/java/cse4392/$(TEST_CLASS).java
REFACTORED_TEST := java-refactored/src/test/java/cse4392/$(TEST_CLASS).java
MERGER_POM := junit-merger/pom.xml
MERGER_JAR := junit-merger/target/junit-merger-1.0.0.jar
MERGER_SOURCES := $(shell find junit-merger/src/main/java -type f -name '*.java')

.DEFAULT_GOAL := help
.PHONY: help check test-python run build-merger test-original \
        test-original-current test-refactored verify-original \
        verify-refactored clean clean-all

help:
	@echo 'CSE 4392 - Team Assignment 3'
	@echo '  make run                    Generate/review/run tests through current LangGraph'
	@echo '  make test-original          Copy latest merged tests; run JUnit + JaCoCo'
	@echo '  make test-original-current  Run installed original tests (no copying)'
	@echo '  make test-refactored        Run installed refactored tests (when ready)'
	@echo '  make verify-original        Strict Maven build/100% branch coverage gate'
	@echo '  make verify-refactored      Strict refactored Maven coverage gate (when ready)'
	@echo '  make test-python            Run Python unit tests (no LLM/Maven)'
	@echo '  make check                  Check Python syntax'
	@echo '  make build-merger           Force clean rebuild of Java test merger'
	@echo '  make clean                  Clean Java test build outputs, preserve merger JAR'
	@echo '  make clean-all              Also clean merger JAR (run auto-rebuilds it)'

# Rebuild the merger if missing or if its sources/POM changed.
$(MERGER_JAR): $(MERGER_POM) $(MERGER_SOURCES)
	$(MAVEN) -B -ntp -f $(MERGER_POM) package

run: $(MERGER_JAR)
	$(PYTHON) app/main.py

# The Python runner already calls Maven with "clean verify".
test-original:
	@test -s "$(GENERATED_TEST)" || { echo 'Missing or empty $(GENERATED_TEST); run make run first.'; exit 1; }
	@mkdir -p "$(dir $(ORIGINAL_TEST))"
	cp "$(GENERATED_TEST)" "$(ORIGINAL_TEST)"
	$(PYTHON) app/java_tools.py original --test-class $(TEST_CLASS)

test-original-current:
	@test -s "$(ORIGINAL_TEST)" || { echo 'No installed original test suite: $(ORIGINAL_TEST)'; exit 1; }
	$(PYTHON) app/java_tools.py original --test-class $(TEST_CLASS)

test-refactored:
	@test -d java-refactored/src/main/java || { echo 'Refactored Java source is not installed yet.'; exit 1; }
	@test -s "$(REFACTORED_TEST)" || { echo 'Refactored JUnit suite is not installed yet.'; exit 1; }
	$(PYTHON) app/java_tools.py refactored --test-class $(TEST_CLASS)

# Strict acceptance checks: tests and branch coverage.
verify-original:
	$(MAVEN) -B -ntp -f java-original/pom.xml clean verify

verify-refactored:
	@test -d java-refactored/src/main/java || { echo 'Refactored Java source is not installed yet.'; exit 1; }
	@test -s "$(REFACTORED_TEST)" || { echo 'Refactored JUnit suite is not installed yet.'; exit 1; }
	$(MAVEN) -B -ntp -f java-refactored/pom.xml clean verify

check:
	$(PYTHON) -m compileall -q app tests
	@echo 'Python syntax: PASS'

test-python:
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py' -v

build-merger:
	$(MAVEN) -B -ntp -f $(MERGER_POM) clean package

# Explicit cleanup. Preserve needed reports first.
clean:
	$(MAVEN) -B -ntp -f java-original/pom.xml clean
	$(MAVEN) -B -ntp -f java-refactored/pom.xml clean

clean-all: clean
	$(MAVEN) -B -ntp -f $(MERGER_POM) clean
