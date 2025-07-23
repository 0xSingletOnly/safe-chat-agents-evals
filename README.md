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
3. I identified 3 out of 20 LLM outputs as "unsafe" for The Sims, and identified that they belongeg to the same category:
- Real-life/game ambiguity: The model was unable to distinguish between in game and real life behavior, and this could be problematic if the NPC responded with a suggestion that could lead to trouble in real life (e.g.- taking my neighbor's ladder in pool away while they are swimming). Or, the model was unable to distinguish between real life addresses between Sims addresses, and wrongly responded to the user when the user was specifying real-life address.
4. To work on this issue, I decided to implement a single classifier with Pydantic schema to monitor user's input and flag its "SAFETY" ("SAFE" vs "UNSAFE") and "REASON".
5. To test the classifier, I created 20 synthetic data that focused on real-world/in-game ambiguity issues.