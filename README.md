# Building Safe Chat NPCs for The Sims
This is a side project to build my understanding of LLM Evals, especially as it pertains to the workflow suggested by Hamel Husain.

## Setup
I used Claude to create 20 synthetic user-NPC conversation starters. I wanted conversations that are vague and open-ended, but not too complex. I also included a mix of safe and unsafe content.

## Tools
I also created my own custom eval data annotator. I wanted to mark each output as 'safe' or 'unsafe'. I picked a binary output to keep things simple.