# PDF Summary Extractor

This project extracts summaries and other relevant information from PDF research papers using the ChatPDF API.

## Getting Started

### Prerequisites

- Python 3.x
- Poetry

### Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/HuberNicolas/academia-maestro.git
    cd academia-maestro
    ```

2. **Install the required dependencies using Poetry:**

    ```bash
    poetry install
    ```

3. **Create necessary folders:**

    ```bash
    mkdir Reading Summary
    ```

4. **Add your research papers:**

    Place your PDF research papers in the `Reading` folder.

5. **Configure the API key:**

    Create a file named `.env.local` in the root directory of the project and add your ChatPDF API key:

    ```plaintext
    CHATPDF_KEY=your_api_key_here
    ```

## Usage

1. **Run the script:**

    Execute the Python script to start processing the PDF files and extracting the required information:

    ```bash
    poetry run python academia-maestro.py
    ```

2. **Output:**

    The JSON files with the extracted information will be saved in the `Summary` folder.

## Script Details

The script performs the following tasks:

1. Loads environment variables from `.env` and `.env.local` files.
2. Traverses the `Reading` folder to find all PDF files.
3. Uploads each PDF file to the ChatPDF API and retrieves a source ID.
4. Uses the source ID to request specific information from the PDF, including:
    - A short summary (abstract)
    - The problem addressed by the paper
    - The methodology used
    - The main contributions of the paper
    - The limitations of the study
    - The value of the paper despite its limitations
5. Saves the extracted information in JSON format in the `Summary` folder.

## Example

Below is an example of how the JSON output will look like:

```json
{
    "Provide a short sumamry: What is the paper about (abstract)?": "Summary of the Paper...",
    "What problem did they want to solve?": "Problem addressed...",
    "What Methodology did they use?": "Methodology...",
    "What is the main contribution of the paper?": "Main contribution...",
    "What are limitations?": "Limitations...",
    "Although Limitations, why is it still considerably good?": "Value despite limitations..."
}
