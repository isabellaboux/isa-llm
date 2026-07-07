# ISA-LLM

## Overview

LLM have proven an impressive tool in mimicking human linguistic skills. Nonetheless, natural human langauge is charachterized by multiple nuances and inplied meanings, which can be referred to as "pragmatic meaning". So how do LLMs deal with pragmatic meaning? While I am sure that many have already asked this question, and LLMs have bene criticized for not being always very good at it (REFs), it is important to consider that ISA are difficult to process for humans too (Boux et al. 2023). 

In this small study, I ask **how does LLM comprehension of indirect language (ISA) compare to human performance**. To this purpose, I rely on a set of direct and indirect question reply pairs from my previois work (Boux et al. 2023; Boux et a., ?) and that have been already evaluated by humans. In addition I present the same question/reply pairs to frontier LLMs and extract their responses.

## Methods 

### Question/reply pair

The question-reply pairs are taken from Boux et al. (2023). They consist of direct/indirect matched pairs, where the same reply can function as direct or indirect language dependong on the preceding question.

- Person A: *"Have you met Martin lately?"* (question)
- Person B: *"I have not seen him for ages."* (direct reply)

and:

- Person A: *"Are you and Martin still good friends?"* (question)
- Person B: *"I have not seen him for ages."* (indirect reply)

### Human data

The human data is also taken from Boux et al. (2023) from the corresponding OSF repository [...]. Briefly, 28 human subjects were presented with the question/reply pairs on a screen and were asked (among others) to evaluate on a 7-points likert scale how much the reply could be understood as a NO (1) or a YES (7). Intermediary integers were also possible so using the value (4) indicated thet the subject was completely unsure.


### LLM data

A set of frontier LLMs (currently `gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-5.4` - inclusion of further open and proprietary models is planned) is selected for this experiment.

All models are queried with the same exact parameters, currently via the **openAI api** and instructed to provided a structured .json output:
* identical system prompt
* `temperature=0`
* identical quation/reply pairs
* identical structure for the json output

The .json output includes:
* **score**: an integer value between 1 and 7, reflecting whether th emodel understands the reply as no (1) or yes (7) along an integer continuum;
* **rationale**, a concise justification for thithe scores.

The entire question/reply set is presented to each model 28 times, reflecting the number of human particiapants in the original human study. So each question/reply pairs receives 28 scores *per model*. This is to capture the fact hat, despite `temperature=0`, the  same model sometimes produces a slightly different output. In a forst preprocessing step, for each model and question/reply pair, all 28 scores were averaged, resulting in one score / model / question-reply pair.

## Results

### Classification (accuracy, confusion matrix, ROC curve)

The score (1-7) for humans and models was converted to a categorical value with 3 classes:
* when `score < 4` then `evaluation = 'no'`
* when `score == 4` then `evaluation = 'unsure'`
* when `score > 4` then `evaluation = 'yes'` 

Using the human evaluation as ground-truth, I calculated accuracy for each model. As is visible in Figure 1, overall all models underperformed compared to humans, regardless of (in)directness. However, all models did worse at matching human performance for indirect than direct question/reply pairs. Overall, the models ranked as follow in their generel performance: `gpt-5.4-nano` < `gpt-5.4-mini` < `gpt-5.4`. 

<div align="center">
    <img src="analysis/accuracy_summarized_evaluator_X_CONDITION.png" alt="confusion matrix" width="60%">
    <p><em>[Figure 1]: Accuracy of each model as a function of (in)directness. Human persformace is considered ground truth (and therefore is equal to 1). Error bars show standard error of the mean (SE).</em></p>
</div>

A closer look at the **confusion matrix** confirms this insight, showing also that none of the model displays a clear bias towards misclassifying "yes" as "no" and vice versa, as evidenced by the camparabel size of false positives and false negatives. "unsure" model responses are very rare (after averaging across 28 runs) and overall negligible.

<p align="center">
    <img src="analysis/confusion_matrix_figure_gpt-5.4-nano-2026-03-17.png" alt="confusion matrix" width="30%">
    <img src="analysis/confusion_matrix_figure_gpt-5.4-mini-2026-03-17.png" alt="confusion matrix" width="30%">
    <img src="analysis/confusion_matrix_figure_gpt-5.4.png" alt="confusion matrix" width="30%">
    <em> [Figure 2]: Normalized confusion matrix for the tested models, in a 3-class classification and using human responses as ground truth.</em>
</p>


The previous accuracy analysis is based on the fact that, as per instruction used in the system prompt, the models use the score value 4 as the decision threshold. But what if the models still captured the no-yes inference continuum, but with the threshold of 4 is just not the right one? The **ROC-curve** and the **ROC-AUC** value show that all models seem to capture the yes-no continuum in a way that is resonably close to human processing. Once again, `gpt-5.4` scores best. 

![image](analysis/roc_curve.png)

### Certainty

The score (1-7) is processed to become a certainty score, such that more extreme values (1 and 7) indicate higher certainty towards either NO or YES and intermediate values (2, 3, 5, 6) indicte less certainty whereas 4  indicates full uncertainty. The certainty score ranged from 1-4.


## Conclusion

> Different models (`gpt-5.4-nano`, `gpt-5.4-mini`, `gpt-5.4`) performed differently when compared to human performance in understanding direct and indirect speech acts. Overall, a gradient could be observed such that the largest model `gpt-5.4` was the best overall at matching human performance, and also had the smallest false positive rate (response mistakenly classified as NO rather than YES). Other open or proprietary models from other providers should be tested too.

## Tech stack

Python:
* `numpy` and `pandas` for data manipulation
* `openAI` for gathering the data from LLMS
* `seaborn` and `matplotlib`
* `pydantic` for enforcing a json data scheme as LLM output
* `scikit-learn` for classification metrics
* `pingouin` for inferential statistics


## Future work

TO DO in `collect_data.ipynb`
- [ ] change API so that it is compatible with all models of interest (incl. large open models ideally)

TO DO in `analyse.ipynb`:
- [ ] both ROC curve and confusion matrix should be calculated separately for direct and indirect SAs: there is in fact a misclassification bias, but only in indirect SAs!
- [ ] FOOD FOR THOUGHT: if any inferential statistics is conducted, it could be appropriate to conduct it by-subject, rather than by-item?



