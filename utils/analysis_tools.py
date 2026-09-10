import pandas as pd
import plotly.express as px
from pathlib import Path
import  matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, confusion_matrix,ConfusionMatrixDisplay
import numpy as np
import seaborn as sns
import pingouin as pg
import math

from config_collection import MODELS

def read_scores_from_model(model):

    model_name = "results_" + model + "_"
    model_name = model_name.replace("/", "_")
    files = list(Path("data/raw/").glob(f"{model_name}*.csv"))

    df = pd.DataFrame([])

    print(f"Found {len(files)} data files for model {model}.")
    for f in files:
        df_data = pd.read_csv(f'data/raw/{f.name}')
        df_data["run"] = f.name[-5:-4]
        df = pd.concat([df, df_data], ignore_index=True)

    df["model"] = model
    df["id"] = df["id"].astype(int)

    # validate (this removes any hallucinated rows that are not in the reference data)
    print(df.columns)
    ref = pd.read_csv("data/external/iCO-Eval2_summarizedRatings.csv", sep=";")
    valid_codes = set(ref["CODE"].astype(int))
    invalid_count = (~pd.to_numeric(df["id"], errors="coerce").isin(valid_codes)).sum()
    print(f"Invalid code rows: {invalid_count}")
    df = df[df["id"].astype(int).isin(valid_codes)].copy()

    return df


def summarize_scores_from_model(df, model):
    summary = df.groupby("id").agg({"score": ["mean", "std", "sem"]}).reset_index()
    summary.columns = summary.columns.get_level_values(1)
    #summary.columns = ['id', f'{model}_mean', f'{model}_std', f'{model}_sem']
    summary.columns = ['id', 'score_mean', 'score_std', 'score_sem']
    print(f"Summarized data for model {model}.")

    return summary


def collate_human_and_llm_data_wide(MODELS: list) -> pd.DataFrame:
    
    # fetch human data
    df = pd.read_csv("data/external/iCO-Eval2_summarizedRatings.csv", sep=";")

    # fetch, aggregate and merge LLM data
    for model in MODELS:
        df_model = read_scores_from_model(model)
        summary_model = summarize_scores_from_model(df_model, model)
        summary_model.head()
        summary_model.columns = ['id', f'{model}_mean', f'{model}_std', f'{model}_sem']
        df = pd.merge(df, summary_model, left_on="CODE", right_on="id", how="left").drop(columns='id')
        
    return df


def collate_human_and_llm_data_long(MODELS: list) -> pd.DataFrame:

    df_evaluators = pd.DataFrame(
        [
            ("human/human", "none"),
            ("openai/gpt-5.4-nano", "closed"),
            ("openai/gpt-5.4-mini", "closed"),
            ("openai/gpt-5.4", "closed"),
            ("openai/gpt-5.5", "closed"),
            ("openai/gpt-5.6-luna", "closed"),
            ("openai/gpt-5.6-terra", "closed"),
            ("openai/gpt-5.6-sol", "closed"),

            ("anthropic/claude-opus-5", "closed"),
            ("anthropic/claude-opus-4.8", "closed"),
            ("anthropic/claude-sonnet-5", "closed"),
            ("anthropic/claude-sonnet-4.6", "closed"),
            ("anthropic/claude-haiku-4.5", "closed"),

            ("google/gemini-3.1-pro-preview", "closed"),
            ("google/gemini-2.5-pro", "closed"),
            ("google/gemini-3.7-flash", "closed"),
            ("google/gemini-3.6-flash", "closed"),
            ("google/gemini-3.5-flash-lite", "closed"),
            ("google/gemini-3.1-flash-lite", "closed"),

            ("google/gemma-4-26b-a4b-it", "open"),
            ("google/gemma-3-27b-it", "open"),

            ("meta-llama/llama-4-maverick", "open"),
            ("meta-llama/llama-4-scout", "open"),
            ("meta-llama/llama-3.3-70b-instruct", "open"),

            ("qwen/qwen3.7-max", "closed"),
            ("qwen/qwen3.7-plus", "closed"),
            ("qwen/qwen3.7-flash", "closed"),
            ("qwen/qwen3.8-max", "closed"),
            ("qwen/qwen3.8-2.4t-a95b", "open"),
            ("qwen/qwen3.8-27b", "open"),

            ("mistralai/mistral-large-2512", "open"),
            ("mistralai/mistral-small-2603", "open"),
            ("mistralai/ministral-14b-2512", "open"),
        ],
        columns=["evaluator", "evaluator_type"],
    )
    
    # fetch human data
    df = pd.read_csv("data/external/iCO-Eval2_summarizedRatings.csv", sep=";")
    df.drop(columns=["CONTEXT QUESTION", "CRITICAL UTTERANCE", "CORRECT RESPONSE (0=no; 1=yes)", "FUN_std", "FUN_sem", "COH_std", "COH_sem", "DIR_std", "DIR_sem", "PRE_std", "PRE_sem", "SSI_std", "SSI_sem", "CER_std", "CER_sem"], inplace=True) #this is not really necessary

    # add information such as condition and set
    ref = df

    df["evaluator"] = "human/human"

    # fetch, aggregate and merge LLM data
    for model in MODELS:
        df_model = read_scores_from_model(model)
        summary_model = summarize_scores_from_model(df_model, model)

        print(summary_model.columns)
        
        # only take mean, leave sd and std out
        summary_model  = summary_model[["id", "score_mean"]] 
        summary_model.rename(columns={"score_mean": "FUN_mean", "id": "CODE"}, inplace=True)
        
        # generate certainty score
        summary_model["CER_mean"] = ((summary_model["FUN_mean"] - 4).abs())+1
        
        # add evaluator column to indicate which model the scores are from
        summary_model["evaluator"] = model

        # add SET and CONDITION infformation from the reference human data
        summary_model = summary_model.merge(ref[["CODE", "SET (1=SA-matched;2=non-SA-matched)", "CONDITION"]], on="CODE", how="left", validate="m:1")

        # concatenate with data so far
        df = pd.concat([df, summary_model], axis=0, join='outer').reset_index(drop=True)
        
    # rename SET column
    df = df.rename(columns={"SET (1=SA-matched;2=non-SA-matched)": "SET"})

    # create columns with model properties
    df[["evaluator_provider", "evaluator_name"]] = df["evaluator"].str.split(
        "/",
        n=1,
        expand=True
        )
    df = df.merge(
    df_evaluators,
    on="evaluator",
    how="left",
    validate="m:1",
)

    # save
    df.to_csv("data/processed/iCO-Eval2_summarizedRatings_long.csv", index=False)

    return df


def compare_to_human(df_long: pd.DataFrame) -> pd.DataFrame:
    '''Classify scores into 3 classes (score < 4: no, score == 4, unsure, score > 4: yes) for all evaluators and compare moel responses to human ones.'''

    # create a reference data frame containing categorized human scores
    ref = df_long.loc[df_long["evaluator"] == "human/human", ["CODE", "FUN_mean"]]
    ref.loc[ref["FUN_mean"] <= 4, 'reference'] = "no"
    ref.loc[ref["FUN_mean"] > 4, 'reference'] = "yes"
    ref

    # merge it to main df_long
    df_long = df_long.merge(ref[["CODE", "reference"]], on="CODE", how="left", validate="m:1")

    # categorize human and model scores
    df_long.loc[df_long["FUN_mean"] <= 4, 'response'] = "no"
    df_long.loc[df_long["FUN_mean"] > 4, 'response'] = "yes"

    # compare model and human to generate accuracy
    df_long['accuracy'] = df_long['response'] == df_long['reference']

    return df_long


def rescale(series: pd.Series, min: int, max: int) -> pd.Series:
    return (series - min) / (max - min)


def conf_matrix(df_long: pd.DataFrame, MODELS: list):
    '''For each model, creates 3 confusion matrices (direct, indirect, all) and plots it.'''

    for model in MODELS:

        for c in ['direct', 'indirect', 'all']:

            # extract data
            if c == 'all':
                y_true = df_long.loc[df_long['evaluator'] == model, 'reference']
                y_pred_cat = df_long.loc[df_long['evaluator'] == model, 'response']
            else:
                y_true = df_long.loc[(df_long['evaluator'] == model) & (df_long['CONDITION'] == c), 'reference']
                y_pred_cat = df_long.loc[(df_long['evaluator'] == model) & (df_long['CONDITION'] == c), 'response']


            # confusion matrix
            cm = confusion_matrix(
                y_true,
                y_pred_cat,
                normalize='all',
                labels=['no', 'yes']
                )
            np.savetxt(f"reports/tables/confusion_matrix_{model.replace("/", "_")}_{c}.txt", cm, fmt="%.2f")

            ConfusionMatrixDisplay.from_predictions(
            y_true,
            y_pred_cat,
            display_labels=["no", "yes"],
            cmap='Blues',
            normalize='all',
            )
            plt.title(f"{model}\n{c}")
            plt.savefig(f"reports/figures/confusion_matrix_figure_{model.replace("/", "_")}_{c}.png")
            plt.close()

            # log
            print(f"Generated, plotted and saved confusion matrix for model {model} and condition {c}.")

def roc(df_long: pd.DataFrame, MODELS: list, filename_figure: str):
    """Generate one ROC subplot per model provider and save AUC values."""

    group_prefixes = {
        "OpenAI": "openai/",
        "Anthropic": "anthropic/",
        "Google": "google/",
        "Meta": "meta-llama/",
        "Qwen": "qwen/",
        "Mistral": "mistralai/",
    }


    df_evaluators = pd.DataFrame(
        [
            ("human/human", "none"),
            ("openai/gpt-5.4-nano", "closed"),
            ("openai/gpt-5.4-mini", "closed"),
            ("openai/gpt-5.4", "closed"),
            ("openai/gpt-5.5", "closed"),
            ("openai/gpt-5.6-luna", "closed"),
            ("openai/gpt-5.6-terra", "closed"),
            ("openai/gpt-5.6-sol", "closed"),

            ("anthropic/claude-opus-5", "closed"),
            ("anthropic/claude-opus-4.8", "closed"),
            ("anthropic/claude-sonnet-5", "closed"),
            ("anthropic/claude-sonnet-4.6", "closed"),
            ("anthropic/claude-haiku-4.5", "closed"),

            ("google/gemini-3.1-pro-preview", "closed"),
            ("google/gemini-2.5-pro", "closed"),
            ("google/gemini-3.7-flash", "closed"),
            ("google/gemini-3.6-flash", "closed"),
            ("google/gemini-3.5-flash-lite", "closed"),
            ("google/gemini-3.1-flash-lite", "closed"),

            ("google/gemma-4-26b-a4b-it", "open"),
            ("google/gemma-3-27b-it", "open"),

            ("meta-llama/llama-4-maverick", "open"),
            ("meta-llama/llama-4-scout", "open"),
            ("meta-llama/llama-3.3-70b-instruct", "open"),

            ("qwen/qwen3.7-max", "closed"),
            ("qwen/qwen3.7-plus", "closed"),
            ("qwen/qwen3.7-flash", "closed"),
            ("qwen/qwen3.8-max", "closed"),
            ("qwen/qwen3.8-2.4t-a95b", "open"),
            ("qwen/qwen3.8-27b", "open"),

            ("mistralai/mistral-large-2512", "open"),
            ("mistralai/mistral-small-2603", "open"),
            ("mistralai/ministral-14b-2512", "open"),
        ],
        columns=["evaluator", "evaluator_type"],
    )

    rows = []

    # Assign models to provider groups, excluding human
    grouped_models = {
        group: [
            model
            for model in MODELS
            if model != "human" and model.startswith(prefix)
        ]
        for group, prefix in group_prefixes.items()
    }

    # Remove groups that contain no models
    grouped_models = {
        group: models
        for group, models in grouped_models.items()
        if models
    }

    if not grouped_models:
        raise ValueError("No models matched the provider prefixes.")

    figure_path = Path("reports/figures")
    table_path = Path("reports/tables")

    figure_path.mkdir(parents=True, exist_ok=True)
    table_path.mkdir(parents=True, exist_ok=True)

    # Create a grid containing up to three subplots per row
    ncols = min(3, len(grouped_models))
    nrows = math.ceil(len(grouped_models) / ncols)

    fig, axes_array = plt.subplots(
        nrows=nrows,
        ncols=ncols,
        figsize=(4 * ncols, 4 * nrows),
        sharex=True,
        sharey=True,
        squeeze=False,
        constrained_layout=True,
    )

    axes = axes_array.flatten()
    for ax, (group, models) in zip(axes, grouped_models.items()):
        for model in models:
            model_df = (
                df_long.loc[
                    df_long["evaluator"].eq(model),
                    ["reference", "FUN_mean"],
                    
                ]
                .dropna()
            )

            if model_df.empty:
                print(f"No observations found for {model}; skipping.")
                continue

            y_true = model_df["reference"]
            y_score = (model_df["FUN_mean"] - 1) / 7

            fpr, tpr, _ = roc_curve(
                y_true,
                y_score,
                pos_label="yes",
            )

            roc_auc = auc(fpr, tpr)

            ax.plot(
                fpr,
                tpr,
                label=f"{model} (AUC = {roc_auc:.2f})",
            )

            # save
            rows.append({
            "evaluator_group": group,
            "evaluator": model,
            "auc": roc_auc,
            })

        # Random-classifier reference line
        ax.plot(
            [0, 1],
            [0, 1],
            linestyle="--",
            color="gray",
            label="Random",
        )

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_title(group)
        ax.grid(alpha=0.2)
        ax.legend(loc="lower right", fontsize=8)

    # Hide subplot positions not used by a provider
    for ax in axes[len(grouped_models):]:
        ax.set_visible(False)

    fig.supxlabel("False Positive Rate")
    fig.supylabel("True Positive Rate (Recall)")

    fig.savefig(
        figure_path / f"{filename_figure}.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
    )

    plt.show()

    result = pd.DataFrame(rows).merge(df_evaluators, on="evaluator", how="left")

    return fig, axes[:len(grouped_models)], result


def descriptive_values(df_long: pd.DataFrame, dv: str, ivs: list):
    '''
    Generates descriptive statistics (mean, sd, sem) for a dv after grouping by the indicated ivs.
    '''

    # aggregate
    aggregated = df_long.groupby(ivs).agg(
        mean=(dv, "mean"),
        sd=(dv, "std"),
        sem=(dv, "sem"),
    ).reset_index()

    # save
    suffix = "_X_".join(x for x in ivs)
    filename = f"reports/tables/{dv}_summarized_{suffix}.csv"
    aggregated.to_csv(filename, index=False)

    return aggregated


def descriptive_plots(df_long: pd.DataFrame, dv: str, ivs: list, dv_min: float, dv_max: float):
    '''
    Create and save a seaborn point plot for a dependent variable grouped by up to
    four independent variables.

    `ivs` must be of length 4. The elements of `ivs` are interpreted in the following order:
    `ivs[0]` as x-axis, `ivs[1]` as hue, `ivs[2]` as column facet, and `ivs[3]`
    as row facet. Use `None` for unused positions.
    '''

    # plot
    f = sns.catplot(
        data=df_long,
        x=ivs[0],
        y=dv,
        hue=ivs[1],
        col=ivs[2], 
        row=ivs[3],
        kind="point",
        markersize=3,
        dodge=0.2,
        errorbar="se",
        linestyle="none",
        capsize=0.1,
        err_kws={"linewidth": 1.5},
    )
    plt.ylim([dv_min, dv_max])
    plt.xticks(rotation=90)
    plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left")

    # save
    suffix = "_X_".join(x for x in ivs if x is not None)
    filename = f"reports/figures/{dv}_summarized_{suffix}.png"
    f.savefig(filename)
    plt.close(f.fig)


def run_anova(df_long: pd.DataFrame, dv: str, models: list[str]):
    """
    Runs a mixed anova (by item) comparing the dv of choice for a given model with the corresponding human data and saves the ANOVA table.
    """

    for model in models:

        print(f"Running mixed anova for model {model} and dv {dv}.")
        # select data for the model of interest and for the human evaluator
        temp_var = df_long[
            (df_long["evaluator"] == "human/human") | (df_long["evaluator"] == model)
        ]        

        # run the mixed anova
        aov = pg.mixed_anova(dv=dv,
                                between='CONDITION',
                                within='evaluator',
                                subject='CODE',
                                effsize='ng2',
                                correction='auto',
                                data=temp_var)


        # save to csv
        aov.to_csv(
            f"reports/tables/{dv}_anova_{model.replace("/", "_")}.csv",
            sep=";",
            float_format="%.3f",
            )


def lollipop_plot(df1: pd.DataFrame, df2: pd.DataFrame, dv: str):
    """
    Creates a lollipop plot comparing direct and indirect scores for each evaluator, saparating each model group provider in a separate subplot. The plot is saved as a PNG file in the reports/figures directory.
    """

    # restructure the data
    df2.rename(columns={"mean": "all"}, inplace=True)
    pivoted_df = (
        df1.pivot_table(
            index=["evaluator", "evaluator_provider", "evaluator_name", "evaluator_type"],
            columns="CONDITION",
            values="mean",
        )
        .reset_index()
    )
    pivoted_df = pivoted_df.merge(df2[["evaluator", "all"]], on="evaluator", how="left", validate="1:1")

    # assess all model providers available
    groups = pivoted_df["evaluator_provider"].unique().tolist()
    groups.insert(0, groups.pop(groups.index("human")))  # move human to the front of the list

    fig, axes = plt.subplots(
        nrows=len(groups),
        ncols=1,
        figsize=(12, 2 * len(groups)),
        sharex=True,
        constrained_layout=True,
    )

    for ax, group in zip(axes, groups):

         # select data for current subplot
        current_df = pivoted_df[
                pivoted_df["evaluator_provider"].eq(group)
            ].copy()

        # Sort each group by descending score for all items (direct + indirect) to ensure the lollipop plot is ordered correctly
        current_df = current_df.sort_values(
            "all",
            ascending=False,
        )

        positions = range(len(current_df))

        # plot lines
        ax.hlines(
            y=positions,
            xmin=current_df["direct"],
            xmax=current_df["indirect"],
            color="dimgrey",
            alpha=0.4,
            zorder=1,
        )

        # plot points for all
        ax.scatter(
            current_df["all"],
            positions,
            color="darkgrey",
            marker='.',            
            label="All",
            zorder=2,
        )

        # plot points for direct
        ax.scatter(
            current_df["direct"],
            positions,
            color="dodgerblue",
            label="Direct",
            zorder=3,
        )

        # plot points for indirect
        ax.scatter(
            current_df["indirect"],
            positions,
            color="orange",
            label="Indirect",
            zorder=4,
        )

        # make small adjustments
        ax.set_yticks(list(positions))
        ax.set_yticklabels(current_df["evaluator_name"])
        ax.invert_yaxis()
        if dv == "CER":
            ax.set_xlim(0, 4)
        if dv == "ACC":
            ax.set_xlim(0, 1)
        ax.set_title(group.capitalize())
        ax.grid(axis="x", alpha=0.3)
    axes[-1].set_xlabel("Score")
    axes[0].legend(loc="best")

    # save the figure
    fig.savefig(
        f"reports/figures/{dv}_lollipop_plot.png",
        dpi=300,
        bbox_inches="tight",
        facecolor="white",
        )
    plt.show()

    return pivoted_df, fig, axes


def rank(df: pd.DataFrame, value: str, variable_name: str):
    """
    Rank the evaluators based on a specific value and save the results to CSV files.
    """

    df.sort_values(
        by=value,
        ascending=False).to_csv(
        f"reports/tables/{variable_name}_ranking_{value}.csv", index=False, float_format='%.3f')

    df[df["evaluator_type"] == "open"].sort_values(
        by=value,
        ascending=False).to_csv(
        f"reports/tables/{variable_name}_ranking_open_{value}.csv", index=False, float_format='%.3f')

    df[df["evaluator_type"] == "closed"].sort_values(
        by=value,
        ascending=False).to_csv(
        f"reports/tables/{variable_name}_ranking_closed_{value}.csv", index=False, float_format='%.3f')
