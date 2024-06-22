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
