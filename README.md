# Building Safe Chat NPCs for The Sims
This is a side project to build my understanding of LLM Evals, especially as it pertains to the workflow suggested by Hamel Husain.

## Setup
1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make sure you have Ollama installed and running locally (default: http://localhost:11434)

3. Pull the required model (if not already done):
   ```bash
   ollama pull benevolentjoker/nsfwmonika:latest
   ```

4. Run the evaluation:
   ```bash
   python main.py
   ```

## Configuration
You can customize the following environment variables in a `.env` file or set them in your environment:

- `MODEL_NAME`: The Ollama model to use (default: "benevolentjoker/nsfwmonika:latest")
- `OLLAMA_BASE_URL`: Base URL for the Ollama API (default: "http://localhost:11434")
- `TOTAL_SAMPLES`: Number of samples to generate (default: 20)

## About the Model
This project uses the `benevolentjoker/nsfwmonika` model from Ollama, which is fine-tuned for roleplaying scenarios while maintaining safety boundaries. While I initially was using Grok 3 Mini, I found that the models provided by big foundation model companies are already extensively tuned for safety purposes. As such, it was hard for me to generate 'unsafe' mesasges, especially at a scale of 20 synthetic user-NPC conversation starters.

## Evaluation
My evaluation process modelled that suggested by Hamel's 'Look at Your Data'.
1. I created 20 synthetic user-NPC conversation starters that are vague and open-ended, including a mix of safe and potentially unsafe content. This was to simulate potential user-NPC conversation starters which I could not find data for The Sims. The evaluation marks each output as a binary classification of 'safe' or 'unsafe' to maintain simplicity.
2. I created my own custom LLM output annotator. Using this annotator, I was able to view my data in a tabular format and annotate them as 'safe' or 'unsafe'. (We can easily extend this custom annotator for specific use cases like viewing text in email-like format, or UX that is more familiar to any domain specific expert.)
![A sample unsafe response from chat agent](images/unsafe_agent_output.png)
3. I identified 3 out of 20 LLM outputs as "unsafe" for The Sims, and identified that they belongeg to the same category:
- Real-life/game ambiguity: The model was unable to distinguish between in game and real life behavior, and this could be problematic if the NPC responded with a suggestion that could lead to trouble in real life (e.g.- taking my neighbor's ladder in pool away while they are swimming). Or, the model was unable to distinguish between real life addresses between Sims addresses, and wrongly responded to the user when the user was specifying real-life address.
4. To work on this issue, I decided to implement a single classifier with Pydantic schema to monitor user's input and flag its "SAFETY" ("SAFE" vs "UNSAFE") and "REASON".
5. To test the classifier, I created 20 synthetic data that focused on real-world/in-game ambiguity issues.
6. I uploaded the classified data to my custom annotator, and mark it on its safety. I wanted to view the alignment of the language model to our human preference.
7. The confusion matrix is as follows:
|                    | Human: Safe | Human: Unsafe |
|-------------------|-------------|---------------|
| **LLM: Safe**     |       4     |    4         |
| **LLM: Unsafe**   |       0     |     12       |
8. We see that the LLM could be erring too much on the side of the caution. Part of the fun of The Sims is allowing players to conduct deranged behavior in the game, and we will want to align the classifier to be closer to our expectations. This could be done through few shot prompting, or knowledge distillation.

## Further improvements
This project was meant to be short such that I practise the fundamentals of Hamel Husain's "Look at Your Data" approach. There are clearly lots to work on here if we were going to productise this system:
1. More classifiers- there are many more problematic categories (inappropriate age relationship, in-game vs real-life mental health issues, cultural/social boundaries). We should use specific classifier for each issue.
2. Few shot prompting for each classifier. Given the vague boundaries, few shot prompting should help with the classification.
3. Align with LLM as a judge. While we have reviewed the confusion matrix, we did not take the next step to align with the model. This could be done through few shot prompting or knowledge distillation.
4. In production, we also want to do a final output classification to ensure that the output is safe before responding to the user.

# Misc
- To ensure fast deployment, I've mainly stuck with small models that can run locally. To improve these models at classification, we can conduct knowledge distillation from large models by using the reasoning trace of 'safe' and 'unsafe' responses.