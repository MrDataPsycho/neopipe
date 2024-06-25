# NeoPipe Example: Lambda Function

## Difinition of Lambda Function

```python
import json
import logging
from typing import List, Dict, Any
from neopipe.pipeline import Pipeline
from neopipe.result import Result, Ok, Err

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
pipeline = Pipeline()

@pipeline.register(retries=3)
def process_fruit_data(fruit_data: List[Dict[str, Any]]) -> Result[Dict[str, Any], str]:
    try:
        unique_fruits = list(set(item['fruit'] for item in fruit_data))
        total_quantity = sum(item['quantity'] for item in fruit_data if item.get('quantity') is not None)
        return Ok({"unique_fruits": unique_fruits, "total_quantity": total_quantity})
    except (TypeError, KeyError) as e:
        return Err(f"Error processing fruit data: {str(e)}")

@pipeline.register(retries=3)
def calculate_average(data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
    try:
        total_quantity = data["total_quantity"]
        unique_fruits = data["unique_fruits"]
        average_quantity = total_quantity / len(unique_fruits) if unique_fruits else 0
        return Ok({
            "unique_fruits": unique_fruits,
            "total_quantity": total_quantity,
            "average_quantity": average_quantity
        })
    except (TypeError, KeyError, ZeroDivisionError) as e:
        return Err(f"Error calculating average quantity: {str(e)}")


def handler(event, context):
    # Run the pipeline
    result = pipeline.run(event)

    # Generate response based on the result
    if result.is_ok():
        final_result = result.unwrap()
        return {
            "statusCode": 200,
            "body": json.dumps(final_result)
        }
    else:
        error_message = result.unwrap_err()
        return {
            "statusCode": 400,
            "body": json.dumps({"error": error_message})
        }

# Example event for local testing
if __name__ == "__main__":
    event = [
        {"fruit": "apple", "quantity": 10},
        {"fruit": "banana", "quantity": 20},
        {"fruit": "orange", "quantity": None}
    ]
    context = {}
    response = handler(event, context)
    print(response)
```

## Output
```
2024-06-26 00:23:28 - neopipe.task - INFO - Executing task process_fruit_data (UUID: 589cac3e-7b79-4fca-8fdf-fc129620e3c5)
2024-06-26 00:23:28 - neopipe.task - INFO - Task process_fruit_data succeeded on attempt 1
2024-06-26 00:23:28 - neopipe.task - INFO - Executing task calculate_average (UUID: 8725cf3d-5b01-47d1-a8dc-ebf891b5798d)
2024-06-26 00:23:28 - neopipe.task - INFO - Task calculate_average succeeded on attempt 1
{'statusCode': 200, 'body': '{"unique_fruits": ["orange", "apple", "banana"], "total_quantity": 30, "average_quantity": 10.0}'}
```
