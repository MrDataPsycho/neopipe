<p align="left">
  <img src="media/neopipe.png" alt="neopipe Logo" width="100" height="100">
</p>

---

# neopipe

A Python library for seamless function orchestration, inspired by Rust and scikit-learn pipelines. Designed to streamline workflow management in microservices and AI-powered applications.

## Key Features:
- Pythonic implementation
- Efficient function pipelining
- Inspired by Rust's approach to data flow
- Tailored for microservices architecture
- Optimized for AI-driven application

## Installation

```bash
$ pip install neopipe
```

## Usage
```python

from typing import Dict, List
from neopipe.pipeline import Pipeline
from neopipe.task import Task
from neopipe.result import Ok, Err, Result
import logging


# Initialize logging
logging.basicConfig(level=logging.INFO)
# Define your pipeline
pipeline = Pipeline()


# Define example tasks using pipeline.task decorator : Method 1 (Using decorator)
@pipeline.task(retries=3)
def get_all_users(data: Dict[str, str]) -> Result[List[str], str]:
    # Example task: Extract names from data
    try:
        names = [item["name"] for item in data]
        return Ok(names)
    except KeyError as e:
        return Err(f"KeyError: {str(e)}")


# Define example tasks using pipeline
def filter_users_by_length(names) -> Result[List[str], str]:
    # Example task: Filter names based on criteria
    filtered_names = [name for name in names if len(name) > 3]
    return Ok(filtered_names)


def calculate_statistics(filtered_names) -> Result[Dict[str, int], str]:
    # Example task: Calculate statistics
    statistics = {
        "total_names": len(filtered_names),
        "longest_name": max(filtered_names, key=len) if filtered_names else None,
    }
    return Ok(statistics)


# Example: Append tasks to the pipeline Alternative Method (Using append_function_as_task)
pipeline.append_function_as_task(filter_users_by_length, retries=2)

# Example: Append tasks to the pipeline Alternative Method (Using append_task)
pipeline.append_task(Task(calculate_statistics, retries=2))


if __name__ == "__main__":
    # Sample data
    sample_data = [
        {"name": "Alice"},
        {"name": "Bob"},
        {"name": "Charlie"},
        {"name": "David"},
        {"name": "Eve"},
    ]

    # Run the pipeline
    result = pipeline.run(
        sample_data, show_progress=True
    )  # Set verbosity to True to display progress bar

    # Check the final result
    if result.is_ok():
        final_statistics = result.unwrap()
        logging.info(f"Pipeline completed successfully. Statistics: {final_statistics}")
    else:
        logging.error(f"Pipeline failed. Error: {result.unwrap_err()}")

```

## Execution Result
```
(.venv) neopipe|main⚡ ⇒ python examples/starter.py 
Pipeline Progress:   0%|                                                                                                                                                                        [ 00:00 ]INFO:root:Executing task get_all_users (UUID: 238bb38a-667c-441c-a4b1-81ffc8f7ca9c)
INFO:root:Task get_all_users succeeded on attempt 1
INFO:root:Executing task filter_users_by_length (UUID: 22c1e1ad-38a2-4528-bc5d-099ca56094c3)
INFO:root:Task filter_users_by_length succeeded on attempt 1
INFO:root:Executing task calculate_statistics (UUID: cb1ea76d-c8b7-49ee-86ab-359d42f0aae1)
INFO:root:Task calculate_statistics succeeded on attempt 1
Pipeline Progress: 100%|███████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████████ [ 00:00 ]
INFO:root:Pipeline completed successfully. Statistics: {'total_names': 3, 'longest_name': 'Charlie'}
```

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`neopipe` was created by MrDataPsycho. It is licensed under the terms of the MIT license.

## Credits

`neopipe` was initially built using [`cookiecutter`](https://cookiecutter.readthedocs.io/en/latest/). But later found some draw back and later adjusted to use Hatch as backend wtith [`Hatch`](https://hatch.pypa.io/1.8/intro/) tool set, which also remove third party python dependency manager from the project.

Modifications include:
- Hatchling build system
- MkDocs for documentation (TODO)
