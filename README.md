# neopipe

A Python library for seamless function orchestration, inspired by Rust and scikit-learn pipelines. Designed to streamline workflow management in microservices and AI-powered applications.

## Key Features:
- Pythonic implementation
- Efficient function pipelining
- Inspired by Rust's approach to data flow
- Tailored for microservices architecture
- Optimized for AI-driven applications

## Installation

```bash
$ pip install neopipe
```

## Usage

A single Threaded sequential execution example:

```python
# Define your pipeline
pipeline = Pipeline()

# Define example tasks using pipeline.task decorator

@pipeline.task(retries=3)
def get_all_users(data):
    # Example task: Extract names from data
    try:
        names = [item["name"] for item in data]
        return Ok(names)
    except KeyError as e:
        return Err(f"KeyError: {str(e)}")

# @pipeline.task(retries=2)
def filter_users_by_length(names):
    # Example task: Filter names based on criteria
    filtered_names = [name for name in names if len(name) > 3]
    return Ok(filtered_names)


def calculate_statistics(filtered_names):
    # Example task: Calculate statistics
    statistics = {
        "total_names": len(filtered_names),
        "longest_name": max(filtered_names, key=len) if filtered_names else None
    }
    return Ok(statistics)

# Add a function as task later in the pipeline
pipeline.append_function_as_task(filter_users_by_length, retries=2)

# Add a task object into the pipeline
pipeline.append_task(Task(calculate_statistics, retries=2))

# Sample data
sample_data = [
    {"name": "Alice"},
    {"name": "Bob"},
    {"name": "Charlie"},
    {"name": "David"},
    {"name": "Eve"},
]

# Run the pipeline
result = pipeline.run(sample_data, show_progress=True)  # Set verbosity to True to display progress bar

# Check the final result
if result.is_ok():
    final_statistics = result.unwrap()
    logging.info(f"Pipeline completed successfully. Statistics: {final_statistics}")
else:
    logging.error(f"Pipeline failed. Error: {result.unwrap_err()}")


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
