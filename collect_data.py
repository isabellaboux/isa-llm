from dotenv import load_dotenv
import os
from openai import OpenAI
import json
import pandas as pd
from tqdm import tqdm
import time
import requests
import logging
from datetime import datetime, timezone
from uuid import uuid4
import config


# ================================      Environment
load_dotenv(override=True)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# ===============================      Funtions
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

def read_qas(file_path: str, retain=None) -> list:
    """
    Read the data from the given CSV file and transform it into a json structure that can be used as batch input to the LLMs.

    Args:
        file_path (str): The path to the CSV file.
        retain (int): The number of rows to include in the output for direct and indirect qaüpairs respectively.
    """
    # read the csv file
    df = pd.read_csv(file_path, sep=";")

    # clip if necessary
    if retain is not None:
        if retain > len(df):
            raise ValueError(f"Retain value {retain} is greater than the number of qas in the dataframe {len(df)}.")
        df = df.head(retain)


    # extract only relevant information
    df_new = df[["CODE", "CONTEXT QUESTION", "CRITICAL UTTERANCE"]]
    df_new["text"]  = "Person A: " + df_new["CONTEXT QUESTION"] + "; Person B: " + df_new["CRITICAL UTTERANCE"]
    df_new.rename(columns={"CODE": "id"}, inplace=True)

    # convert into json
    output = [
    {
        "id": str(row["id"]),
        "text": row["text"]
    }
    for _, row in df_new.iterrows()
    ]

    return output



def score_qas(model: str, qas: list) -> dict:
    """
    Score the QAs using one OpenRouter model.
    """

    response = client.chat.completions.create(
        model=model,
        temperature=config.TEMPERATURE,
        messages=[
            {
                "role": "system",
                "content": config.SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(qas),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "batch_classification_scores",
                "strict": True,
                "schema": config.SCORE_SCHEMA,
            },
        },
        extra_body={
            "provider": {
                "require_parameters": False,
                "allow_fallbacks": True,
            }
        },
    )

    content = response.choices[0].message.content
    result = json.loads(content)

    # ensure that the json file starts with the results field, at the top level
    if isinstance(result, list):
        result = {"results": result}
    elif not isinstance(result, dict) or "results" not in result:
        raise ValueError(f"Unexpected response shape: {result!r}")

    # validation of the score (integer between  1 and 7)
    for item in result["results"]:
        score = item["score"]
        if not isinstance(score, int) or not 1 <= score <= 7:
            raise ValueError(f"Invalid score {score!r} for item {item['id']}. Expected an integer from 1 to 7.")

    return result, response


def fetch_metadata(response: str) -> dict:
    """
    Fetch metadata for a completed generation.
    """

    
    metadata = {
        "generation_id": response.id,
        "requested_model": model,
        "returned_model": response.model,
        "provider_name": response.provider,
        "finish_reason": response.choices[0].finish_reason,
        "prompt_tokens": response.usage.prompt_tokens,
        "completion_tokens": response.usage.completion_tokens,
        "reasoning_tokens": response.usage.completion_tokens_details.reasoning_tokens,
        "total_tokens": response.usage.total_tokens,
        "total_cost": response.usage.cost,
    }

    try:
        stats = get_openrouter_generation_stats(response.id, config.METADATA_MAX_RETRIES)
        metadata.update({
            "router": stats.get("router"),
            "upstream_id": stats.get("upstream_id"),
            "native_finish_reason": stats.get("native_finish_reason"),
            "latency": stats.get("latency"),
            "generation_time": stats.get("generation_time"),
        })
    except Exception as e:
        logger.warning(f"Could not fetch extended generation stats for {response.id}: {e}")

    return metadata

def save_result(model: str, trial: int, result: dict):
    """
    Save the scoring results to a CSV file.
    """

    # Convert results to a dataframe
    results_df = pd.DataFrame(result["results"])
    results_df ['run_id'] = run_id
    results_df.to_csv(f"data/raw/results_{model.replace("/", "_")}_score_trial{trial+1}.csv", index=False)


def save_metadata(model: str, trial: int, metadata: dict):
    """
    Save the scoring results to a CSV file.
    """

    # Convert metedata to a dataframe
    metadata_df = pd.DataFrame([metadata])
    metadata_df ['run_id'] = run_id
    metadata_df.to_csv(f"data/raw/metadata_{model.replace("/", "_")}_score_trial{trial+1}.csv", index=False)


def get_metadata_parameter(metadata: dict, parameter: str) -> float:
    """
    Get a specific parameter from the metadata dictionary.
    """
    if parameter not in metadata:
        raise ValueError(f"Parameter {parameter} not found in metadata.")
    return metadata[parameter]


def get_openrouter_generation_stats(generation_id: str, max_retries: int = 5) -> dict:
    """
    Fetch OpenRouter metadata for a completed generation.
    This is where provider_name is available.
    """
    
    url = "https://openrouter.ai/api/v1/generation"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    }

    for attempt in range(max_retries):
        response = requests.get(
            url,
            headers=headers,
            params={"id": generation_id},
            timeout=30,
        )

        if response.status_code == 200:
            return response.json()["data"]

        # Sometimes metadata may not be immediately available.
        if response.status_code == 404 and attempt < max_retries - 1:
            time.sleep(3)
            continue

        response.raise_for_status()

    raise RuntimeError(f"Could not fetch generation stats for {generation_id}")

def save_config_to_json():
    """
    Save the configuration to a JSON file.
    """

    run_configuration = {
        "run_id": run_id,
        "started_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "models": config.MODELS,
        "trials": config.TRIALS,
        "temperature": config.TEMPERATURE,
        "retain": config.RETAIN,
        "system_prompt": config.SYSTEM_PROMPT,
        "score_schema": config.SCORE_SCHEMA,
        "metadata_max_retries": config.METADATA_MAX_RETRIES,
    }

    with open(f"data/log/config_{run_id}.json", "w", encoding="utf-8") as file:
            json.dump(run_configuration, file, indent=4, ensure_ascii=False)



# ========================     Intiialization
# gereate unique run ID
run_id = (
    f"{datetime.now():%Y%m%dT%H%M%SZ}"
    f"_{uuid4().hex[:8]}"
)

# initialize logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(f"data/log/run_{run_id}.log"),
        logging.StreamHandler()
    ],
    force=True,
)
logger = logging.getLogger(__name__)


# start preparatory steps
logger.info(f"Script started with run ID: {run_id}")
start = time.time()
save_config_to_json()
logger.info(f"Saved configuration to .json file in data/log/config_{run_id}.json")
qas = read_qas("data/external/iCO-Eval2_summarizedRatings.csv", retain=config.RETAIN)
logger.info(f"Number of QAs: {len(qas)}")



# ================================       Data collection
total_cost = 0

for model in config.MODELS:
    
    for trial in tqdm(range(config.TRIALS), desc=f"Currently collecting data from {model}\n"):

        logger.info(f"Model {model}, Trial {trial+1}/{config.TRIALS}")

        # collect LLM responses
        try:
            result, response = score_qas(model, qas)
            logger.info(f"Model {model}, Trial {trial+1}/{config.TRIALS}: scoring completed")
        except Exception as e:
            logger.error(f"Model {model}, Trial {trial+1}/{config.TRIALS}: scoring failed: {e}")
            continue

        # save LLM responses
        try:
            save_result(model, trial, result)
            logger.info(f"Model {model}, Trial {trial+1}/{config.TRIALS}: scoring saved")
        except Exception as e:
            logger.error(f"Model {model}, Trial {trial+1}/{config.TRIALS}: saving scoring failed: {e}")
            continue

        # extract metadata from OpenRouter
        try:
            metadata = fetch_metadata(response)
            logger.info(f"Model {model}, Trial {trial+1}/{config.TRIALS}: metadata fetched")
        except Exception as e:
            logger.error(f"Model {model}, Trial {trial+1}/{config.TRIALS}: fetching metadata failed: {e}")
            continue

        # save metadata to CSV
        try:
            save_metadata(model, trial, metadata)
            logger.info(f"Model {model}, Trial {trial+1}/{config.TRIALS}: metadata saved")
            # calculate total costs so far based on available metadata.
            total_cost += get_metadata_parameter(metadata, "total_cost")

        except Exception as e:
            logger.error(f"Model {model}, Trial {trial+1}/{config.TRIALS}: saving metadata failed: {e}")
            continue


finish = time.time()
logger.info(f"Data collection completed. Total time taken is {(finish - start)/60:.0f}m:{(finish - start)%60:.0f}s. Total cost of all trials: ${total_cost:.4f}")