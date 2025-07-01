## Methodology for Creating the Interactive Bamboo Diagram

This document outlines the step-by-step methodology employed to transform raw drill core structural orientation data into an interactive, schematic "bamboo" diagram using Python and Plotly. The process involves data parsing, intelligent segment generation, and dynamic visualization.

### 1. Data Acquisition and Initial Pre-processing

The initial data is sourced from a tab-separated text file (e.g., `STRUCTURE-EIS-24PMD0002.txt`). The script first performs the following operations:

* **File Parsing:** The text file is read line by line. It identifies a specific header line (starting with `H1000`) to extract column names, and then parses subsequent data rows (starting with `D`).
* **DataFrame Creation:** The parsed data is loaded into a pandas DataFrame, providing a structured format for manipulation.
* **Data Type Conversion:** Key columns, such as `FROM`, `TO`, `Ori_Confindence`, `Alpha`, `Beta`, `Dip`, and `Dip_Dir`, are converted to numeric types. Non-numeric entries in these columns are coerced to `NaN` (Not a Number).
* **Essential Data Filtering:** Rows where critical orientation data (`FROM`, `TO`, `Alpha`, `Ori_Confindence`) are missing (`NaN`) are removed. This ensures that only records suitable for orientation analysis are considered.
* **Sorting:** The DataFrame is sorted by the `FROM` depth to maintain a consistent stratigraphic order for plotting.

### 2. Schematic Core Segment Generation

The core of the "bamboo" diagram involves dividing the entire drill hole into fixed-length schematic segments. For each segment, the following logic is applied:

* **Interval Definition:** The total depth range of the drill hole is divided into contiguous, non-overlapping intervals of a predefined `segment_length` (e.g., 3.0 meters).
* **Feature Aggregation:** For each defined segment, the script identifies all individual structural features (e.g., bedding, faults, veins) from the filtered data that fall within its depth interval.
* **Segment Classification (OR/LOST):**
    * If any oriented features are found within a segment, it is classified as "Oriented" (OR).
    * If no oriented features are present, the segment is classified as "Lost" (LOST).
* **Representative Angle Determination (for OR segments):**
    * The `Dip_Dir` (Dip Direction) is prioritized from features with the highest `Ori_Confindence` (Orientation Confidence) within the segment.
    * If `Dip_Dir` is unavailable, the `Beta` angle is used as a proxy for direction, again prioritizing higher confidence features.
    * A label indicating the representative angle (e.g., "305° (Beta)") is generated.
* **Dominant Feature Identification (for OR segments):** The most frequently occurring `StrFeature` (Structural Feature) among the highest confidence features within the segment is identified as the "Dominant Feature."
* **Hover Text Construction:** A detailed HTML-formatted string (`hover_text`) is dynamically created for each segment. This string includes:
    * Segment depth range and status (OR/LOST).
    * Representative angle and dominant feature (for OR segments).
    * Highest confidence level (for OR segments).
    * A comprehensive list of *all* individual features within that segment, including their `FROM` depth, `Dip_Dir`, `Dip`, `Alpha`, `Beta`, `Ori_Confindence`, `ContactType`, and `Comments`. Missing values are gracefully handled (e.g., "N/A" or empty string).

### 3. Interactive Plot Construction (Plotly)

The processed schematic segments are then rendered into an interactive Plotly graph:

* **Layout Definition:** Parameters such as `core_height`, `segment_width`, `row_spacing`, and `max_segments_per_row` are used to define the visual dimensions and arrangement of the "bamboo" segments in a grid-like layout.
* **Core Segment Rectangles:** Each schematic segment is drawn as a rectangle (`go.layout.Shape`). "LOST" segments are filled with a light gray, while "OR" segments have an off-white background, both with black borders.
* **Interactive Hover Areas:** Invisible `go.Scatter` traces with `mode='markers'` are placed at the center of each segment. These markers have `opacity=0` but are given a sufficient `size` to cover their respective segments. The crucial `hovertemplate='%{hovertext}<extra></extra>'` is used to ensure that the pre-generated `hover_text` is displayed when the user hovers over a segment, suppressing default trace information.
* **Annotations:**
    * "OR" or "LOST" labels are placed above each segment.
    * Depth labels (`FROM` and `TO`) are positioned at the bottom-left and bottom-right of each segment, respectively, with added padding.
    * For "OR" segments, the representative angle is displayed, color-coded based on `highest_confidence` (e.g., dark green for high, dark orange for medium, dark red for low).
    * The "Dominant Feature" label is placed below the angle.
* **Orientation Arrow:** A "DOWNH" arrow is added at the bottom of the plot to indicate the direction of increasing depth.
* **Plot Customization:** The overall plot layout is configured with a title, hidden axes, and a `hovermode="closest"` setting for optimal interactivity.

### 4. Output

The final interactive plot is generated as an HTML file (`.html`) using `fig.write_html()`. This HTML file can be opened in any web browser, allowing users to interact with the diagram (hover for details, zoom, pan) without needing Python installed. The script also supports direct display in compatible Python environments if no output path is specified.

This methodology ensures a robust, visually informative, and user-friendly tool for geological core orientation analysis.