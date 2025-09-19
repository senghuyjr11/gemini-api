# Manga Prompt Agent & Gemini API Integration

A Python toolkit to create, customize, and refine prompts for manga generation, with support for leveraging the Gemini API as part of your prompt engineering workflow.

## Overview

This repository is designed for manga creators and AI artists who want to systematically generate high-quality prompts for manga (or anime-style) image generation. It provides modules to help you:

- Compose, structure, and refine prompts specifically for manga agents.
- Optionally use Google’s Gemini API to enhance or expand prompt ideas.
- Prepare prompts for direct use in diffusion models or other generative AI pipelines.

## Features

- Tools for manga/anime prompt creation and editing
- Gemini API integration for smart prompt enhancement (optional)
- Workflow to prepare prompts for manga diffusion models
- 100% Python, easy to integrate into your existing projects

## Installation

Clone the repository and install dependencies:

```bash
git clone https://github.com/senghuyjr11/gemini-api.git
cd gemini-api
pip install -r requirements.txt
```

## Usage

1. (Optional) Get a Gemini API key from: https://aistudio.google.com/app/apikey  
2. Create a `.env` file and add your key:
    ```env
    GOOGLE_API_KEY=your_gemini_api_key_here
    ```
3. Use this toolkit to:
    - Build and refine manga prompts.
    - (Optionally) Leverage Gemini to generate or expand ideas.
    - Export prompts for input into manga diffusion models or your preferred generative tools.

## Contributing

Pull requests are welcome!

## License

MIT License (see [LICENSE](LICENSE)).