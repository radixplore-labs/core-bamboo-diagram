import pandas as pd
import numpy as np
import plotly.graph_objects as go
import argparse # For command-line arguments

def load_and_parse_data(file_path):
    """
    Loads and parses the raw data from the specified text file.

    Args:
        file_path (str): The path to the STRUCTURE-EIS-24PMD0002.txt file.

    Returns:
        pd.DataFrame: The raw data as a pandas DataFrame.
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file content is empty or headers are missing.
    """
    try:
        with open(file_path, 'r') as f:
            file_content = f.read()
        if not file_content:
            raise ValueError(f"File content is empty: {file_path}")
    except FileNotFoundError:
        raise FileNotFoundError(f"Error: File not found at '{file_path}'. Please ensure the file exists.")
    except Exception as e:
        raise Exception(f"Error reading file content: {e}")

    lines = file_content.strip().split('\n')

    header_line_index = -1
    for i, line in enumerate(lines):
        if line.startswith('H1000'):
            header_line_index = i
            break
    if header_line_index == -1:
        raise ValueError("H1000 header not found in the file.")

    column_names = [col for col in lines[header_line_index].split('\t')[1:] if col.strip()]

    data_start_index = -1
    for i in range(header_line_index + 1, len(lines)):
        if lines[i].startswith('D'):
            data_start_index = i
            break
    if data_start_index == -1:
        raise ValueError("No data rows (starting with 'D') found after the H1000 header.")

    data_rows = []
    for i in range(data_start_index, len(lines)):
        line = lines[i]
        if line.startswith('D'):
            row_values = line.split('\t')[1:]
            if len(row_values) >= len(column_names):
                data_rows.append(row_values[:len(column_names)])
            else:
                print(f"Warning: Skipping malformed row at line {i+1}: {line}")

    return pd.DataFrame(data_rows, columns=column_names)

def clean_and_filter_data(df_raw):
    """
    Cleans and filters the raw DataFrame, converting types and dropping NaNs.

    Args:
        df_raw (pd.DataFrame): The raw DataFrame loaded from the file.

    Returns:
        pd.DataFrame: The cleaned and filtered DataFrame.
    Raises:
        ValueError: If the DataFrame is empty after filtering.
    """
    df_cleaned = df_raw.copy()
    numeric_cols = ['FROM', 'TO', 'Ori_Confindence', 'Alpha', 'Beta', 'Dip', 'Dip_Dir']
    for col in numeric_cols:
        df_cleaned[col] = pd.to_numeric(df_cleaned[col], errors='coerce')

    df_filtered = df_cleaned.dropna(subset=['FROM', 'TO', 'Alpha', 'Ori_Confindence']).copy()

    if df_filtered.empty:
        raise ValueError("DataFrame is empty after filtering. No valid data for plotting.")

    df_filtered.sort_values(by='FROM', inplace=True)
    df_filtered.reset_index(drop=True, inplace=True)
    return df_filtered

def generate_schematic_segments(df_filtered, segment_length=3.0):
    """
    Generates schematic core segments (OR/LOST) from filtered data.

    Args:
        df_filtered (pd.DataFrame): Cleaned and filtered DataFrame.
        segment_length (float): Length of each schematic core segment in meters.

    Returns:
        list: A list of dictionaries, each representing a schematic segment.
    """
    min_depth = df_filtered['FROM'].min()
    max_depth = df_filtered['TO'].max()

    start_interval_depth = np.floor(min_depth / segment_length) * segment_length
    end_interval_depth = np.ceil(max_depth / segment_length) * segment_length + segment_length
    depth_intervals = np.arange(start_interval_depth, end_interval_depth, segment_length)

    schematic_segments = []

    for i in range(len(depth_intervals) - 1):
        seg_start = depth_intervals[i]
        seg_end = depth_intervals[i+1]

        features_in_segment = df_filtered[
            (df_filtered['FROM'] >= seg_start) & (df_filtered['FROM'] < seg_end)
        ]

        segment_type = 'LOST'
        angle_label = None
        feature_type_label = None
        highest_confidence = 0
        hover_text_details = []

        if not features_in_segment.empty:
            segment_type = 'OR'
            highest_confidence = features_in_segment['Ori_Confindence'].max()

            high_conf_features = features_in_segment[(features_in_segment['Ori_Confindence'] == highest_confidence)]
            feature_type_label = high_conf_features['StrFeature'].mode()[0] if not high_conf_features.empty else features_in_segment['StrFeature'].mode()[0]

            representative_angle_value = None
            angle_source_note = ""

            high_conf_features_with_dip_dir = features_in_segment[
                (features_in_segment['Ori_Confindence'] == highest_confidence) & (features_in_segment['Dip_Dir'].notna())
            ]
            if not high_conf_features_with_dip_dir.empty:
                representative_angle_value = high_conf_features_with_dip_dir.iloc[0]['Dip_Dir']
            else:
                any_oriented_feature_with_dip_dir = features_in_segment[
                    (features_in_segment['Ori_Confindence'] >= 1) & (features_in_segment['Dip_Dir'].notna())
                ]
                if not any_oriented_feature_with_dip_dir.empty:
                    representative_angle_value = any_oriented_feature_with_dip_dir.iloc[0]['Dip_Dir']
                else:
                    high_conf_features_with_beta = features_in_segment[
                        (features_in_segment['Ori_Confindence'] == highest_confidence) & (features_in_segment['Beta'].notna())
                    ]
                    if not high_conf_features_with_beta.empty:
                        representative_angle_value = high_conf_features_with_beta.iloc[0]['Beta']
                        angle_source_note = " (Beta)"
                    else:
                        any_oriented_feature_with_beta = features_in_segment[
                            (features_in_segment['Ori_Confindence'] >= 1) & (features_in_segment['Beta'].notna())
                        ]
                        if not any_oriented_feature_with_beta.empty:
                            representative_angle_value = any_oriented_feature_with_beta.iloc[0]['Beta']
                            angle_source_note = " (Beta)"

            if representative_angle_value is not None:
                angle_label = f"{int(representative_angle_value)}°{angle_source_note}"
            else:
                angle_label = "OR"

            # Populate hover text for OR segments with improved formatting
            hover_text_details.append(f"<b>Depth:</b> {seg_start:.1f}m - {seg_end:.1f}m")
            hover_text_details.append(f"<b>Status:</b> {segment_type}")
            hover_text_details.append(f"<b>Representative Angle:</b> {angle_label}")
            hover_text_details.append(f"<b>Dominant Feature:</b> {feature_type_label}")
            hover_text_details.append(f"<b>Highest Confidence:</b> {highest_confidence}")
            hover_text_details.append("<br><b>--- Features in Segment ---</b>")
            for _, feature_row in features_in_segment.iterrows():
                # Safely format numbers, handling NaN
                dip_dir_str = f"{feature_row['Dip_Dir']:.0f}°" if pd.notna(feature_row['Dip_Dir']) else "N/A"
                dip_str = f"{feature_row['Dip']:.0f}°" if pd.notna(feature_row['Dip']) else "N/A"
                alpha_str = f"{feature_row['Alpha']:.0f}°" if pd.notna(feature_row['Alpha']) else "N/A"
                beta_str = f"{feature_row['Beta']:.0f}°" if pd.notna(feature_row['Beta']) else "N/A"
                conf_str = f"{feature_row['Ori_Confindence']:.0f}" if pd.notna(feature_row['Ori_Confindence']) else "N/A"
                contact_type_str = feature_row['ContactType'] if pd.notna(feature_row['ContactType']) else "N/A"
                comments_str = feature_row['Comments'] if pd.notna(feature_row['Comments']) else ""

                hover_text_details.append(
                    f"  <b>- {feature_row['StrFeature']}</b> at {feature_row['FROM']:.2f}m:<br>"
                    f"    Dip_Dir={dip_dir_str}, Dip={dip_str}<br>"
                    f"    Alpha={alpha_str}, Beta={beta_str}<br>"
                    f"    Conf={conf_str}, Contact Type: {contact_type_str}<br>"
                    f"    Comments: {comments_str}<br>" # Added extra line break for spacing
                )
        else:
            # Populate hover text for LOST segments
            hover_text_details.append(f"<b>Depth:</b> {seg_start:.1f}m - {seg_end:.1f}m")
            hover_text_details.append(f"<b>Status:</b> {segment_type}")
            hover_text_details.append("<i>No oriented features found in this interval.</i>")

        schematic_segments.append({
            'type': segment_type,
            'start_depth': seg_start,
            'end_depth': seg_end,
            'angle_label': angle_label,
            'feature_type_label': feature_type_label,
            'highest_confidence': highest_confidence,
            'hover_text': "<br>".join(hover_text_details)
        })
    return schematic_segments

def create_plotly_diagram(schematic_segments, hole_id, output_html_path=None):
    """
    Creates and displays an interactive Plotly schematic bamboo diagram.

    Args:
        schematic_segments (list): List of dictionaries representing schematic segments.
        hole_id (str): The ID of the drill hole.
        output_html_path (str, optional): Path to save the interactive HTML plot.
                                          If None, displays in environment.
    """
    core_height = 1.5
    segment_width = 7 # Increased width further for more padding
    row_spacing = 3.5
    max_segments_per_row = 8

    num_rows = int(np.ceil(len(schematic_segments) / max_segments_per_row))
    fig_height_scale_factor = 100
    fig_height = num_rows * fig_height_scale_factor + 100

    fig = go.Figure()
    shapes = []
    annotations = []
    hover_traces = []

    top_y_coordinate = 0

    # Explicitly initialize current_row and segment_in_row_count here
    current_row = 0
    segment_in_row_count = 0

    for i, segment in enumerate(schematic_segments):
        row_idx = i // max_segments_per_row
        col_idx = i % max_segments_per_row

        x_start = col_idx * segment_width
        y_offset_for_this_row = row_idx * (core_height + row_spacing)
        y_center = top_y_coordinate - y_offset_for_this_row - (core_height / 2)

        # Core Rectangle colors
        if segment['type'] == 'LOST':
            fill_color = '#cccccc' # Light gray for LOST
            line_color = '#999999'
            label_color_top = '#666666'
        else: # 'OR' type
            fill_color = '#f0f0f0' # Very light gray/off-white for OR
            line_color = '#000000'
            label_color_top = '#000000'

        shapes.append(
            go.layout.Shape(
                type="rect",
                x0=x_start, y0=y_center - core_height / 2,
                x1=x_start + segment_width, y1=y_center + core_height / 2,
                fillcolor=fill_color,
                line=dict(color=line_color, width=0.8),
                layer="below"
            )
        )

        # Add a transparent scatter trace for hover functionality
        hover_traces.append(
            go.Scatter(
                x=[x_start + segment_width / 2], # X at center of segment
                y=[y_center], # Y at center of segment
                mode='markers',
                marker=dict(opacity=0, size=core_height * 50), # Invisible marker, size covers segment
                hovertemplate='%{hovertext}<extra></extra>', # Use %{hovertext} and remove trace name
                hovertext=[segment['hover_text']], # Pass hovertext as a list
                showlegend=False,
                hoverlabel=dict( # Custom hover label styling
                    bgcolor="white", # White background
                    font=dict(color="black", family="Arial", size=11), # Black text, Arial font
                    bordercolor="lightgray", # Light gray border
                    namelength=-1 # Ensures full name/text is shown
                )
            )
        )

        # "LOST" or "OR" label at the top of the core segment
        annotations.append(
            go.layout.Annotation(
                x=x_start + segment_width / 2,
                y=y_center + core_height / 2 + 0.40,
                text=segment['type'],
                showarrow=False,
                font=dict(size=12, color=label_color_top, family="Arial", weight="bold")
            )
        )

        # --- Depth Labels ---
        # Adjusted x positions for more padding
        annotations.append(
            go.layout.Annotation(
                x=x_start + 0.3, # Increased padding from left edge
                y=y_center - core_height / 2 - 0.25,
                text=f"{segment['start_depth']:.1f}m",
                showarrow=False,
                font=dict(size=10, color='gray', family="Arial"),
                xanchor='left', yanchor='top'
            )
        )

        # Only label end_depth on the right for the last segment in a row or the very last segment overall
        is_last_in_row = (col_idx == max_segments_per_row - 1)
        is_last_segment_overall = (i == len(schematic_segments) - 1)

        if is_last_in_row or is_last_segment_overall:
            annotations.append(
                go.layout.Annotation(
                    x=x_start + segment_width - 0.3, # Increased padding from right edge
                    y=y_center - core_height / 2 - 0.25,
                    text=f"{segment['end_depth']:.1f}m",
                    showarrow=False,
                    font=dict(size=10, color='gray', family="Arial"),
                    xanchor='right', yanchor='top'
                )
            )

        # Angle label and orientation arrow for 'OR' segments
        if segment['type'] == 'OR':
            arrow_start_x = x_start + 0.5
            arrow_end_x = x_start + segment_width - 0.5
            arrow_y = y_center

            shapes.append(
                go.layout.Shape(
                    type="line",
                    x0=arrow_start_x, y0=arrow_y,
                    x1=arrow_end_x, y1=arrow_y,
                    line=dict(color="green", width=2),
                    layer="above"
                )
            )

            arrow_head_x = arrow_end_x
            arrow_head_y = arrow_y
            arrow_size = 0.2
            shapes.append(
                go.layout.Shape(
                    type="path",
                    path=f"M {arrow_head_x},{arrow_head_y} L {arrow_head_x - arrow_size},{arrow_head_y + arrow_size / 2} L {arrow_head_x - arrow_size},{arrow_head_y - arrow_size / 2} Z",
                    fillcolor="green",
                    line_color="green",
                    layer="above"
                )
            )

            if segment['angle_label']:
                if segment['highest_confidence'] == 3:
                    angle_label_color = 'darkgreen'
                elif segment['highest_confidence'] == 2:
                    angle_label_color = 'darkorange'
                elif segment['highest_confidence'] == 1:
                    angle_label_color = 'darkred'
                else:
                    angle_label_color = 'darkgray'

                annotations.append(
                    go.layout.Annotation(
                        x=x_start + segment_width / 2,
                        y=y_center + 0.4, # Adjusted y position for more gap from arrow
                        text=segment['angle_label'],
                        showarrow=False,
                        font=dict(size=11, color=angle_label_color, family="Arial", weight="bold")
                    )
                )

            # Feature type label below the angle label
            if segment['feature_type_label']:
                annotations.append(
                    go.layout.Annotation(
                        x=x_start + segment_width / 2,
                        y=y_center - 0.4, # Adjusted y position for more gap
                        text=segment['feature_type_label'],
                        showarrow=False,
                        font=dict(size=10, color='darkblue', family="Arial")
                    )
                )

        # Update counters for layout
        segment_in_row_count = segment_in_row_count + 1
        if segment_in_row_count >= max_segments_per_row:
            current_row = current_row + 1
            segment_in_row_count = 0

    # Add all hover traces to the figure
    for trace in hover_traces:
        fig.add_trace(trace)

    # --- 6. General Plotly Layout Customization ---
    max_drawn_y = top_y_coordinate + core_height / 2 + 0.25 + 0.5 # Topmost annotation + padding
    min_drawn_y = -(num_rows -1) * (core_height + row_spacing) - (core_height / 2) - 0.25 - 0.5 # Bottommost annotation + padding

    fig.update_layout(
        title_text=f"Interactive Schematic Core Orientation Diagram for Hole: {hole_id}",
        title_x=0.5,
        title_font_size=20,
        title_font_family="Arial",
        title_font_color="black",
        height=fig_height,
        width=1600,
        xaxis=dict(
            visible=False,
            range=[0, max_segments_per_row * segment_width]
        ),
        yaxis=dict(
            visible=False,
            range=[min_drawn_y, max_drawn_y],
            scaleanchor="x",
            scaleratio=1
        ),
        shapes=shapes,
        annotations=annotations,
        plot_bgcolor='white',
        margin=dict(l=20, r=20, t=50, b=20),
        hovermode="closest"
    )

    downh_arrow_x_center = (max_segments_per_row * segment_width) / 2
    downh_arrow_y_pos = min_drawn_y - 0.5

    fig.add_annotation(
        x=downh_arrow_x_center + 1,
        y=downh_arrow_y_pos,
        ax=downh_arrow_x_center - 1,
        ay=downh_arrow_y_pos,
        xref="x", yref="y", axref="x", ayref="y",
        text="DOWNH",
        showarrow=True,
        arrowhead=3,
        arrowsize=1,
        arrowwidth=2,
        arrowcolor="black",
        font=dict(size=16, color="black", family="Arial", weight="bold"),
        xanchor='center', yanchor='middle'
    )

    if output_html_path:
        fig.write_html(output_html_path, auto_open=False)
        print(f"Plot saved to {output_html_path}")
    else:
        fig.show()

def main():
    parser = argparse.ArgumentParser(description="Generate an interactive schematic bamboo diagram from drill core data.")
    parser.add_argument("file_path", type=str, help="Path to the input STRUCTURE-EIS-24PMD0002.txt file.")
    parser.add_argument("--output", "-o", type=str, help="Optional path to save the interactive HTML plot (e.g., plot.html). If not provided, the plot will be displayed.")
    args = parser.parse_args()

    try:
        df_raw = load_and_parse_data(args.file_path)
        df_filtered = clean_and_filter_data(df_raw)
        
        # Extract hole ID for the title
        hole_id = df_filtered['HOLE_ID'].iloc[0] if not df_filtered.empty else "Unknown Hole"

        schematic_segments = generate_schematic_segments(df_filtered)
        create_plotly_diagram(schematic_segments, hole_id, args.output)

    except (FileNotFoundError, ValueError, Exception) as e:
        print(f"An error occurred: {e}")
        exit(1)

if __name__ == "__main__":
    main()