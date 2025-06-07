#!/bin/bash

set -e

BASE=$(pwd)

declare -A SERVICES=(
    [watcher]="test_watcher.py"
    [metadata]="test_metadata.py"
    [splitter]="test_splitter.py"
    [packager]="test_packager.py"
    [organizer]="test_organizer.py"
    [status-api]="test_status_api.py"
)

for SERVICE in "${!SERVICES[@]}"; do
    TESTDIR="$BASE/$SERVICE/tests"
    TESTFILE="$TESTDIR/${SERVICES[$SERVICE]}"
    mkdir -p "$TESTDIR"
    if [[ ! -f "$TESTFILE" ]]; then
        cat > "$TESTFILE" <<EOF
# Minimal pytest skeleton for $SERVICE
def test_placeholder():
    assert True  # Replace with real tests
EOF
        echo "Initialized: $TESTFILE"
    fi
done

# Root-level integration test
mkdir -p "$BASE/tests"
if [[ ! -f "$BASE/tests/test_pipeline_integration.py" ]]; then
    cat > "$BASE/tests/test_pipeline_integration.py" <<EOF
# Placeholder for E2E pipeline integration test
def test_pipeline_placeholder():
    assert True  # Replace with real pipeline integration test
EOF
    echo "Initialized: $BASE/tests/test_pipeline_integration.py"
fi

echo "Test directory scaffolding complete."
