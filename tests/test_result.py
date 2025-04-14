import pytest
import asyncio
from neopipe.result import Result, Ok, Err, UnwrapError


def test_ok_and_err():
    r1 = Ok(42)
    r2 = Err("error")
    assert r1.is_ok()
    assert not r1.is_err()
    assert r2.is_err()
    assert not r2.is_ok()
    assert r1.ok() == 42
    assert r2.err() == "error"


def test_map_ok():
    result = Ok(10).map(lambda x: x + 5)
    assert result == Ok(15)


def test_map_err():
    result = Err("fail").map(lambda x: x + 5)
    assert result == Err("fail")


@pytest.mark.asyncio
async def test_map_async_ok():
    async def plus_1(x: int) -> int:
        await asyncio.sleep(0.01)
        return x + 1

    result = await Ok(3).map_async(plus_1)
    assert result == Ok(4)


@pytest.mark.asyncio
async def test_map_async_err():
    async def plus_1(x: int) -> int:
        return x + 1

    result = await Err("boom").map_async(plus_1)
    assert result == Err("boom")


def test_map_err_ok_passthrough():
    result = Ok("value").map_err(lambda e: f"error: {e}")
    assert result == Ok("value")


def test_map_err_transform():
    result = Err("fail").map_err(lambda e: f"[x] {e}")
    assert result == Err("[x] fail")


@pytest.mark.asyncio
async def test_map_err_async_ok_passthrough():
    async def tag_error(e: str) -> str:
        return f"ERR: {e}"

    result = await Ok("fine").map_err_async(tag_error)
    assert result == Ok("fine")


@pytest.mark.asyncio
async def test_map_err_async_transform():
    async def tag_error(e: str) -> str:
        return f"ERR: {e}"

    result = await Err("bad").map_err_async(tag_error)
    assert result == Err("ERR: bad")


def test_and_then_chaining():
    def double(x: int) -> Result[int, str]:
        return Ok(x * 2)

    result = Ok(4).and_then(double)
    assert result == Ok(8)


def test_and_then_passthrough_err():
    def double(x: int) -> Result[int, str]:
        return Ok(x * 2)

    result = Err("fail").and_then(double)
    assert result == Err("fail")


@pytest.mark.asyncio
async def test_and_then_async_success():
    async def double(x: int) -> Result[int, str]:
        return Ok(x * 2)

    result = await Ok(5).and_then_async(double)
    assert result == Ok(10)


@pytest.mark.asyncio
async def test_and_then_async_error_passthrough():
    async def double(x: int) -> Result[int, str]:
        return Ok(x * 2)

    result = await Err("fail").and_then_async(double)
    assert result == Err("fail")


def test_unwrap_and_expect():
    assert Ok(100).unwrap() == 100
    assert Ok(200).expect("should not fail") == 200

    with pytest.raises(UnwrapError, match="unwrap"):
        Err("boom").unwrap()

    with pytest.raises(UnwrapError, match="expected it to work"):
        Err("fail").expect("expected it to work")


def test_unwrap_or_and_or_else():
    assert Ok(1).unwrap_or(9) == 1
    assert Err("e").unwrap_or(9) == 9

    assert Ok(1).unwrap_or_else(lambda e: 42) == 1
    assert Err("boom").unwrap_or_else(lambda e: 42) == 42


def test_match_branching():
    result = Ok(5).match(lambda x: f"OK {x}", lambda e: f"ERR {e}")
    assert result == "OK 5"

    result = Err("fail").match(lambda x: f"OK {x}", lambda e: f"ERR {e}")
    assert result == "ERR fail"


def test_to_dict_and_json():
    import json
    r = Ok({"a": 1, "b": 2})
    as_dict = r.to_dict()
    assert as_dict["_is_ok"] is True
    assert as_dict["_value"] == {"a": 1, "b": 2}

    json_str = r.to_json()
    parsed = json.loads(json_str)
    assert parsed["_is_ok"] is True
    assert parsed["_value"]["a"] == 1
