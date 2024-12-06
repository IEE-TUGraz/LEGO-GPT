import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def heatmap(df: pd.DataFrame, maximum_value_for_heatmap: float = None, xcaption: str = None) -> None:
    sns.set_style("whitegrid")
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
    })

    # Create color map from
    # IEE grün RGB: 0 128 128
    # TU rot RGB: 247 1 71
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#FFFFFF", "#F70147"])
    cmap = matplotlib.colors.LinearSegmentedColormap.from_list("", ["#FFFFFF", "#fc8dad"])  # Lighter red

    ax = sns.heatmap(df, cmap=cmap, fmt='.2f', vmax=maximum_value_for_heatmap, annot=True, cbar=True)

    # Add a horizontal line at the bottom of the heatmap
    ax.hlines([len(df) - 1], *ax.get_xlim(), colors='black', linestyles='dashed')

    # Add horizontal lines to make it easier to read
    # ax.hlines([range(len(df)-2)], *ax.get_xlim(), colors='lightgrey', linestyles='solid')
    # ax.hlines([len(df)], *ax.get_xlim(), colors='lightgrey', linestyles='solid')

    # Add vertical lines to make it easier to read
    # ax.vlines([range(len(df.columns) + 1)], *ax.get_ylim(), colors='lightgrey', linestyles='solid')

    # Move column labels to the top
    plt.tick_params(axis='both', which='major', labelsize=10, labelbottom=False, bottom=False, top=False, labeltop=True)

    # Make row labels italic
    labels = ax.get_yticklabels()
    for i, label in enumerate(labels):
        labels[i] = r"\textit{" + label.get_text() + "}"
    labels[-1] = r"\textbf{" + ax.get_yticklabels()[-1].get_text() + "}"  # Make last row label bold
    ax.set_yticklabels(labels)

    # Make x- and y-axis bold
    ax.set_ylabel(r"\textbf{" + ax.get_ylabel() + "}", fontsize=14)
    ax.set_title(r"\textbf{" + xcaption + "}", fontsize=14)

    # Iterate through all data values, make right-aligned and add '%'
    texts = ax.texts
    for i, text in enumerate(texts):
        if i > df.size - len(df.columns) - 1:
            text.set_text(r"\textbf{" + text.get_text() + r"}\%")
        else:
            text.set_text(text.get_text() + r"\%")
        text.set_ha('left')

    # Adjust colorbar labels
    cbar = ax.collections[0].colorbar
    labels = cbar.ax.get_yticklabels()
    for i, label in enumerate(labels):
        if i == len(labels) - 1:
            labels[i] = r"\textgreater" + label.get_text() + r"\%"
        else:
            labels[i] = label.get_text() + r"\%"
    cbar.set_ticklabels(labels)

    # Move plot to the right
    ax.figure.subplots_adjust(left=0.2, top=0.9, right=0.98, bottom=0.05)

    plt.show()
    print("Done")


# Example
if __name__ == '__main__':
    # Data preparation
    data = {'Federal State': ['Burgenland', 'Carinthia', 'Lower Austria', 'Upper Austria', 'East Tyrol', 'Styria', 'Salzburg', 'Tyrol', 'Vorarlberg', 'Vienna', 'Average'],
            'Run-of-River': [0.19, 0.00, 0.00, 0.00, 0.00, 0.01, 0.00, 0.00, 0.00, 0.00, 0.02],
            'Solar-PV': [0.00, 0.00, 0.01, 0.00, 0.00, 0.02, 0.00, 0.00, 0.00, 0.00, 0.00],
            'Thermal': [0.00, 0.65, 0.56, 0.63, 0.00, 0.14, 0.00, 17.78, 0.00, 0.24, 2.00],
            'Wind': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]}
    df = pd.DataFrame(data)
    df.set_index('Federal State', inplace=True)

    second_highest_number = float(np.sort(df.values.flatten())[-2])

    heatmap(df, maximum_value_for_heatmap=second_highest_number, xcaption="Relative Error")
