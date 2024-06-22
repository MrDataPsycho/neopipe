import pytest
from neopipe.result import Result, Ok, Err

def test_result_is_ok():
    result = Ok("Success")
    assert result.is_ok() is True
    assert result.is_err() is False

def test_result_is_err():
    result = Err("Error")
    assert result.is_ok() is False
    assert result.is_err() is True

def test_result_unwrap_ok():
    result = Ok("Success")
    assert result.unwrap() == "Success"

def test_result_unwrap_err():
    result = Err("Error")
    with pytest.raises(ValueError, match="Called unwrap on an Err value: Error"):
        result.unwrap()

def test_result_unwrap_err_value():
    result = Err("Error")
    assert result.unwrap_err() == "Error"

def test_result_unwrap_err_on_ok_value():
    result = Ok("Success")
    with pytest.raises(ValueError, match="Called unwrap_err on an Ok value: Success"):
        result.unwrap_err()

def test_result_to_dict():
    result_ok = Ok({"name": "John", "age": 30})
    result_err = Err("Some error occurred")
    assert result_ok.to_dict() == {'value': {'name': 'John', 'age': 30}, 'error': None}
    assert result_err.to_dict() == {'value': None, 'error': 'Some error occurred'}

def test_result_to_json():
    result_ok = Ok({"name": "John", "age": 30})
    result_err = Err("Some error occurred")
    assert result_ok.to_json() == '{"value": {"name": "John", "age": 30}, "error": null}'
    assert result_err.to_json() == '{"value": null, "error": "Some error occurred"}'

def test_result_repr():
    result_ok = Ok("Success")
    result_err = Err("Error")
    assert repr(result_ok) == "Result(value='Success', error=None)"
    assert repr(result_err) == "Result(value=None, error='Error')"

