# How do LLMs and humans compare in processing indirect speech?

## Overview

LLMs have proven to be impressive tools for mimicking human linguistic skills. Nonetheless, natural human language is characterized by multiple nuances and indirect meanings. For instance, if asked *"Would you like a piece of cake?"*, the answer *"I am on a diet"* would indirectly mean NO and would be a so called **indirect seech act (ISA)**.

So how do LLMs deal with indirect seech acts? While it is important to consider that ISAs are also difficult for humans to process (Boux et al. 2023a, 2023b), so far, LLMs have been found to be have inferior performance to humans (Orsini and Bunato, 2025; Koo et al., 2025; Solidjonov, 2026). However:
- the methodology in these study is variable (see Ma et al., 2025 and Sadigzada, 2016 for a discussion)
- a direct comparison to human performance is not always provided
- newer models have not been evaluated


> In this small study, I ask **how comprehension of indirect language (ISA) by cutting edge LLMs compares to human performance**. To do so, I rely on a set of direct and indirect question/reply pairs from my previous work (Boux et al. 2023a; Boux et al. 2023b) that have already been evaluated by humans who provided quantitative ratings. In addition, I present the same question/reply pairs to frontier LLMs, extract their responses and compare them to human responses.

## Methods 

### Question/reply pair

The question/reply pairs are taken from Boux et al. (2023). They consist of direct/indirect matched pairs, where the same reply can function as direct or indirect language depending on the preceding question.

- Person A: *"Have you met Martin lately?"* (question)
- Person B: *"I have not seen him for ages."* (direct reply)

and:

- Person A: *"Are you and Martin still good friends?"* (question)
- Person B: *"I have not seen him for ages."* (indirect reply)

### Human data

The human data is also taken from Boux et al. (2023), from the corresponding OSF repository [...]. Briefly, 28 human participants were presented with the question/reply pairs on a screen and were asked, among other things, to evaluate on a 7-point Likert scale how much the reply could be understood as a NO (1) or a YES (7). Intermediate integers were also possible, so using the value 4 indicated that the participant was completely unsure.


### LLM data

A set of frontier LLMs is selected for this experiment.

| Provider | Model name | Model type | Comment |
|---|---|---|---|
| OpenAI | `gpt-5.4-nano` | Closed weight | — |
|  | `gpt-5.4-mini` | Closed weight | — |
|  | `gpt-5.4` | Closed weight | — |
|  | `gpt-5.5` | Closed weight | — |
|  | `gpt-5.6-luna` | Closed weight | — |
|  | `gpt-5.6-terra` | Closed weight | — |
|  | `gpt-5.6-sol` | Closed weight | — |
| Anthropic | `claude-opus-5` | Closed weight | — |
|  | `claude-opus-4.8` | Closed weight | — |
|  | `claude-sonnet-5` | Closed weight | — |
|  | `claude-sonnet-4.6` | Closed weight | — |
|  | `claude-haiku-4.5` | Closed weight | — |
| Google | `gemini-3.1-pro-preview` | Closed weight | — |
|  | `gemini-2.5-pro` | Closed weight | — |
|  | `gemini-3.7-flash` | Closed weight | — |
|  | `gemini-3.6-flash` | Closed weight | — |
|  | `gemini-3.5-flash-lite` | Closed weight | — |
|  | `gemini-3.1-flash-lite` | Closed weight | — |
|  | `gemma-4-26b-a4b-it` | Open weight | — |
|  | `gemma-4-31b-it` | Open weight | Does not support JSON output |
|  | `gemma-3-27b-it` | Open weight | — |
|  | `gemma-3-12b-it` | Open weight | Data was collected only for direct responses, for unknown reasons |
|  | `gemma-3-4b-it` | Open weight | Data was not collected for unknown reasons |
| Meta | `llama-4-maverick` | Open weight | — |
|  | `llama-4-scout` | Open weight | — |
|  | `llama-3.3-70b-instruct` | Open weight | — |
| Qwen | `qwen3.7-max` | Closed weight | — |
|  | `qwen3.7-plus` | Closed weight | — |
|  | `qwen3.7-flash` | Closed weight | — |
|  | `qwen3.8-max` | Closed weight | — |
|  | `qwen3.8-2.4t-a95b` | Open weight | — |
|  | `qwen3.8-27b` | Open weight | — |
| Mistral AI | `mistral-large-2512` | Open weight | — |
|  | `mistral-small-2603` | Open weight | — |
|  | `ministral-14b-2512` | Open weight | — |

All models are queried with exactly the same parameters, currently via the **OpenAI API**, and are instructed to provide a structured JSON output:
* identical system prompt
* `temperature=0`
* identical question/reply pairs
* identical structure for the JSON output

The JSON output includes:
* **score**: an integer value between 1 and 7, reflecting whether the model understands the reply as no (1) or yes (7) along an integer continuum;
* **rationale**: a concise justification for this score.

The entire question/reply set is presented to each model 14 times, reflecting the number of human participants in the original human study. Thus, each question/reply pair receives 28 scores *per model*. This is to capture the fact that, despite `temperature=0`, the same model sometimes produces a slightly different output. In a first preprocessing step, for each model and question/reply pair, all 28 scores were averaged, resulting in one score per model per question/reply pair.

## Results

### Classification (accuracy, ROC curve)

The score (1-7) for humans and models was converted to a binary value:
* when `score <= 4` then `evaluation = 'no'`
* when `score > 4` then `evaluation = 'yes'` 

Using the human evaluation as ground truth, I calculated accuracy for each model. As visible in Figure 1, all models slightly underperformed relative to humans. However, all models did worse at matching human performance for indirect than for direct question/reply pairs.

When considering accuracy for both direct and indirect replies, the best performing models were:

| Rank | Provider | Model | Direct | Indirect | Direct + Indirect |
|---|---|---|---|---|---|
| 1 | google | gemini-3.7-flash |1.000 | 0.993 | 0.996
| 2 | google | gemini-3.1-pro-preview |1.000 | 0.993 |0.996
| 3 | google | gemini-3.6-flash | 1.000 | 0.986 |0.993

The best models among open-weights ones were.

| Rank | Provider | Model | Direct | Indirect | Direct + Indirect |
|---|---|---|---|---|---|
| 1 | qwen | qwen3.8-2.4t-a95b | 1.000 | 0.986 | 0.993
| 2 | qwen | qwen3.8-27b | 0.993 |0.964 | 0.978
| 3 | mistralai | mistral-large-2512 | 0.978 | 0.949 | 0.964

<div align="center">
    <img src="reports/figures/ACC_lollipop_plot.png" alt="confusion matrix" width="60%">
    <p><em>[Figure 1]: Accuracy of each model for direct (blue) and indirect (orange) replies, separated by model provider. Human performance is taken as ground truth (and therefore is equal to 1).</em></p>
</div>

<!-- A closer look at the **confusion matrix** confirms this insight. In addition, it shows that the smaller `gpt-5.4-nano` and `gpt-5.4-mini` models tend to misclassify "yes" as "no" and vice versa, as evidenced by the comparable sizes of false positives and false negatives. "Unsure" model responses are very rare after averaging across 28 runs and are overall negligible.

<p align="center">
    <img src="reports/figures/confusion_matrix_figure_gpt-5.4-nano-2026-03-17_direct.png" alt="confusion matrix" width="30%">
    <img src="reports/figures/confusion_matrix_figure_gpt-5.4-mini-2026-03-17_direct.png" alt="confusion matrix" width="30%">
    <img src="reports/figures/confusion_matrix_figure_gpt-5.4_direct.png" alt="confusion matrix" width="30%">
    <br>
    <img src="reports/figures/confusion_matrix_figure_gpt-5.4-nano-2026-03-17_indirect.png" alt="confusion matrix" width="30%">
    <img src="reports/figures/confusion_matrix_figure_gpt-5.4-mini-2026-03-17_indirect.png" alt="confusion matrix" width="30%">
    <img src="reports/figures/confusion_matrix_figure_gpt-5.4_indirect.png" alt="confusion matrix" width="30%">
    <br>
    <em>[Figure 2]: Normalized confusion matrix for each model, separately for direct (upper row) and indirect replies (bottom row), in a binary classification using human responses as ground truth.</em>
</p> -->


The previous accuracy analysis is based on the fact that, as specified in the system prompt, the models use the score value 4 as the threshold in a binary decision. But what if the models still capture the no/yes inference continuum, and the threshold of 4 is simply not the right one? The **ROC curve** and the **ROC-AUC** show that all models seem to capture the yes/no continuum in a way that is reasonably close to human processing (Figure 2).


<div align="center">
    <img src="reports/figures/roc_curve_by_group_all.png" alt="confusion matrix" width="80%">
    <p><em>[Figure 2]: ROC curve for all models, evaluated simultaneously on both direct and indirect replie, separated by provider.</em></p>
</div>

When considering accuracy for both direct and indirect replies, the best performing models were:

| Rank | Provider | Model | Direct | Indirect | Direct + Indirect |
|---|---|---|---|---|---|
| 1 | google | gemini-3.7-flash |1.000 | 1.000 | 1.000
| 2 | google | gemini-3.1-pro-preview |1.000 | 1.000 | 1.000
| 3 | google | gemini-3.6-flash | 1.000 | 1.000 | 1.000

The best models among open-weights ones were:

| Rank | Provider | Model | Direct | Indirect | Direct + Indirect |
|---|---|---|---|---|---|
| 1 | qwen | qwen3.8-2.4t-a95b | 1.000 | 0.991 | 0.997
| 2 | qwen | qwen3.8-27b |1.000 | 0.986| 0.996
| 3 | google | gemma-4-26b-a4b-it | 0.997 | 0.991 | 0.995


### Certainty

So far, we have looked at categorical responses (NO/YES) derived from a continuous scale (1-7) with a threshold set at 4. Looking only at categorized responses, however, might hide subtler patterns in the data, for instance how certain (i.e., confident) humans or LLMs are in their responses.

A certainty score is obtained by transforming the original score (1-7) provided by the LLMs such that more extreme values (1 and 7) indicate higher certainty toward either NO or YES, while intermediate values (2, 3, 5, 6) indicate less certainty and 4 indicates full uncertainty. The certainty score ranges from 1 to 4.

Compared to humans, most LLMs were overall more confident interpreting replies regardless of in/directnes. However, similar to humans, most LLMs had a tendency to be less confident interpreting indirect than direct replies.

<div align="center">
    <img src="reports/figures/CER_lollipop_plot.png" alt="certainty lollipop" width="80%">
    <p><em>[Figure 4]: Certainty scores obtained for direct and indirect replies for both human and LLM evaluators, reported separately for each provider (sem).</em></p>
</div>

To assess whoch models were most similar to human performanc in terms of confidence, 


## Conclusion

> Different models performed differently when compared to human performance in understanding direct and indirect speech acts. [DETAILS]

## Limitations

In general, it is difficutlt to define what it beans to be good at understanding indirect cpeech acts and what ground truth is. If aat all,  ground truth might be the intention of the person who produced the indirect reply. In this present work, LLm performance was compared to human performance and therefore merely answer the questions of which LLms tend to meahve most similarly to humans.

Simmilar to the human study (boux et al., 2023) the LLm was asked to rate whethe ra reply could be understood as "yes" or "no" in a 7 point likert scale, where teh middle value indicated uncertainty or ambiguity. Thismethod of assessment has its limitations, in partiicular does not correspond to how people and LLms process speech nder natural circumstances, where a rating is typicalyl not needed, but just an appropriate response. A way to address this issue would be to send agents based onto different LLMs indirect requests and assess the likelihood that the relevant tool is called by the LLM.

Fianally, another interesting qustion to ask is what logics to LLMs use to understand indirect speech acts. In linguistic literaturre (Grice, 19xx; Searle, 19xx) certain euristics have been described. As the present raw data incldudes also a rationale why the LLMs understood teh replies in a certain way, it would be interesting to see if they use heuristics similar to what has been qualitatively described in humans. However, as far as I can tell, __quantitative__ data from huiman does not exist, so a direct comparison is not possible. 

## Tech stack

Python:
* `numpy` and `pandas` for data manipulation
* `OpenRouter` for gathering the data from LLMs
* `seaborn` and `matplotlib`
* `pydantic` for enforcing a JSON data schema as LLM output
* `scikit-learn` for classification metrics
* `pingouin` for inferential statistics
* `logging` for runtime event logging


## Future work

TO DO in `collect_data.ipynb`:
- [x] change API so that it is compatible with all models of interest (incl. large open models ideally)
- [ ] further refactor (put functions in a separae file)?
- [ ] consider randomizing stimulus presentation

TO DO in `analyse.ipynb`:
- [ ] Add a data validation. Check that every code is present and that no code is absent.
- [ ] Change visualization of accuracy from pointplots to condiitonal petal plots (in separate panels for each provider, odered by putative model complexity with line separating open and closed models
- [ ] Confusion matrix should have the same color limits acoross all models
- [] ROC curve also by provider (possibly with color difference between open and closed models)
- [ ] CER analysis also with petal plots, similar to accuracy.
- [ ] Consider adding metadata about the models to enrich the analysis (e.g. number of parameters)
- [ ] FOOD FOR THOUGHT: if any inferential statistics are conducted, it could be more appropriate to conduct them by subject (or run) rather than by item to maximize comparability to human data. This however would require using individual human subject data, which participants did not consent to share. Not possible unless those data are not synced to git.


### References

* Boux, I., Margiotoudi, K., Dreyer, F., Tomasello, R., & Pulvermüller, F. (2023a). Cognitive Features of Indirect Speech Acts. Language, Cognition and Neuroscience, 38(1), 40–64. https://doi.org/10.1080/23273798.2022.2077396

* Boux, I., & Pulvermüller, F. (2023b). Does the right temporo-parietal junction play a role in processing indirect speech acts? A transcranial magnetic stimulation study. Neuropsychologia, 188, 108588. https://doi.org/10.1016/j.neuropsychologia.2023.108588

* Koo, Y., Lee, J., Park, D., Park, S., & Lee, S. (2025). Evaluating Large language models on Understanding Korean indirect Speech acts (arXiv:2502.10995). arXiv. https://doi.org/10.48550/arXiv.2502.10995

* Ma, B., Li, Y., Zhou, W., Gong, Z., Liu, Y. J., Jasinskaja, K., Friedrich, A., Hirschberg, J., Kreuter, F., & Plank, B. (2025). Pragmatics in the Era of Large Language Models: A Survey on Datasets, Evaluation, Opportunities and Challenges. In W. Che, J. Nabende, E. Shutova, & M. T. Pilehvar (Eds.), Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) (pp. 8679–8696). Association for Computational Linguistics. https://doi.org/10.18653/v1/2025.acl-long.425

* Orsini, M., & Brunato, D. (n.d.). Direct and Indirect Interpretations of Speech Acts: Evidence from Human Judgments and Large Language Models.

* Sadigzada, Z. (2026). Pragmatic Failure in Agentic LLM Systems: An Analysis Through Gricean Maxims and Speech Act Theory. Global Spectrum of Research and Humanities, 3(2), 71–84. https://doi.org/10.69760/gsrh.0260302009

* Solidjonov, D. (2026). Pragmatic competence without embodiment? Evaluating LLM performance on implicature, presupposition, and speech acts. Journal of Cultural Cognitive Science. https://doi.org/10.1007/s41809-026-00200-5
