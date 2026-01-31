import os
from typing import Annotated, Optional
import matplotlib.pyplot as plt
import io
import base64

from fastmcp import FastMCP

mcp = FastMCP("Create plots from data")


@mcp.tool(description="Creates plot chart from provided data")
def create_line_plot(
    data: Annotated[
        dict[str, list[float]],
        "A dictionary where each key is a label and each value is a list of numerical data points to plot."
    ],
    title: Optional[Annotated[str, "The title of the plot to be displayed at the top of the chart."]] = None,
    x_label: Optional[Annotated[str, "The label for the x-axis of the plot."]] = None,
    y_label: Optional[Annotated[str, "The label for the y-axis of the plot."]] = None,
    legend: Optional[Annotated[bool, "A flag indicating whether to display a legend on the plot."]] = None,
) -> Annotated[str, "The filename of the saved plot image in PNG format."]:
    plt.figure(figsize=(4, 3))

    for label, values in data.items():
        plt.plot(values, label=label)

    plt.title(title)
    plt.xlabel(x_label)
    plt.ylabel(y_label)

    if legend:
        plt.legend()

    plt.tight_layout()

    img_name = "plots/plot_" + os.urandom(16).hex() + ".png"
    plt.savefig(img_name)
    plt.close()

    return img_name


if __name__ == "__main__":
    mcp.run(transport="streamable-http", port=8001)
