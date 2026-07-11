import pytest
import pandas as pd
from backend.services.schema_validator import SchemaValidator

@pytest.fixture
def baseline_df():
    return pd.DataFrame({
        'user_id': [1, 2, 3],
        'name': ['Alice', 'Bob', 'Charlie'],
        'age': [25, 30, 35]
    })

@pytest.fixture
def current_df_same():
    return pd.DataFrame({
        'user_id': [4, 5, 6],
        'name': ['David', 'Eve', 'Frank'],
        'age': [28, 32, 37]
    })

@pytest.fixture
def current_df_new_column():
    return pd.DataFrame({
        'user_id': [4, 5, 6],
        'name': ['David', 'Eve', 'Frank'],
        'age': [28, 32, 37],
        'email': ['d@e.com', 'e@e.com', 'f@e.com']
    })

@pytest.fixture
def current_df_missing_column():
    return pd.DataFrame({
        'user_id': [4, 5, 6],
        'name': ['David', 'Eve', 'Frank']
    })

@pytest.fixture
def current_df_type_change():
    return pd.DataFrame({
        'user_id': ['4', '5', '6'],
        'name': ['David', 'Eve', 'Frank'],
        'age': [28, 32, 37]
    })

def test_extract_schema(baseline_df):
    schema = SchemaValidator.extract_schema(baseline_df)
    assert 'user_id' in schema
    assert 'name' in schema
    assert 'age' in schema

def test_no_schema_changes(baseline_df, current_df_same):
    baseline_schema = SchemaValidator.extract_schema(baseline_df)
    current_schema = SchemaValidator.extract_schema(current_df_same)
    changes, is_breaking = SchemaValidator.compare_schemas(baseline_schema, current_schema)
    assert len(changes) == 0
    assert not is_breaking

def test_new_column_detection(baseline_df, current_df_new_column):
    baseline_schema = SchemaValidator.extract_schema(baseline_df)
    current_schema = SchemaValidator.extract_schema(current_df_new_column)
    changes, is_breaking = SchemaValidator.compare_schemas(baseline_schema, current_schema)

    assert len(changes) == 1
    assert changes[0].change_type == "NEW_COLUMN"
    assert changes[0].column == "email"
    assert not is_breaking

def test_missing_column_detection(baseline_df, current_df_missing_column):
    baseline_schema = SchemaValidator.extract_schema(baseline_df)
    current_schema = SchemaValidator.extract_schema(current_df_missing_column)
    changes, is_breaking = SchemaValidator.compare_schemas(baseline_schema, current_schema)

    assert len(changes) == 1
    assert changes[0].change_type == "MISSING_COLUMN"
    assert changes[0].column == "age"
    assert is_breaking

def test_type_change_detection(baseline_df, current_df_type_change):
    baseline_schema = SchemaValidator.extract_schema(baseline_df)
    current_schema = SchemaValidator.extract_schema(current_df_type_change)
    changes, is_breaking = SchemaValidator.compare_schemas(baseline_schema, current_schema)

    assert len(changes) == 1
    assert changes[0].change_type == "TYPE_CHANGE"
    assert changes[0].column == "user_id"
    assert is_breaking

def test_validate_schema(baseline_df, current_df_same):
    baseline_schema = SchemaValidator.extract_schema(baseline_df)
    result = SchemaValidator.validate_schema(current_df_same, baseline_schema)

    assert not result["is_breaking"]
    assert len(result["changes"]) == 0
