# Core Bamboo Diagram Generator

This tool generates an interactive schematic "bamboo" diagram from drill core structural orientation data, specifically designed for geologists to quickly visualize structural trends and data gaps.

## Features

* Parses `.txt` files containing structural measurements (e.g., `STRUCTURE-EIS-24PMD0002.txt` format).
* Generates schematic core segments, classifying them as "Oriented" (OR) or "Lost" (LOST).
* Displays representative orientation angles (Dip Direction or Beta) and dominant structural feature types.
* Provides interactive hover popups with detailed information for each segment, including all features within that interval, their angles, confidence, contact types, and comments.
* Outputs an interactive HTML plot that can be shared and viewed in any web browser.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/radixplore-labs/core-bamboo-diagram.git](https://github.com/radixplore-labs/core-bamboo-diagram.git)
    cd core-bamboo-diagram
    ```
2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: `venv\Scripts\activate`
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

To generate a bamboo diagram, run the script from your terminal:

```bash
python bamboo_plotter.py <path_to_your_input_file.txt>
