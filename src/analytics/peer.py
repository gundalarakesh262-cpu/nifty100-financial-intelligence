{
  "nbformat": 4,
  "nbformat_minor": 0,
  "metadata": {
    "colab": {
      "provenance": [],
      "authorship_tag": "ABX9TyM6zeYgo4ozWdssBus8EcjJ",
      "include_colab_link": true
    },
    "kernelspec": {
      "name": "python3",
      "display_name": "Python 3"
    },
    "language_info": {
      "name": "python"
    }
  },
  "cells": [
    {
      "cell_type": "markdown",
      "metadata": {
        "id": "view-in-github",
        "colab_type": "text"
      },
      "source": [
        "<a href=\"https://colab.research.google.com/github/gundalarakesh262-cpu/nifty100-financial-intelligence/blob/main/src/analytics/peer.py\" target=\"_parent\"><img src=\"https://colab.research.google.com/assets/colab-badge.svg\" alt=\"Open In Colab\"/></a>"
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "from openpyxl import load_workbook\n",
        "\n",
        "excel_path = \"output/peer_comparison.xlsx\"\n",
        "\n",
        "wb = load_workbook(excel_path)\n",
        "\n",
        "print(\"Total sheets:\", len(wb.sheetnames))\n",
        "print(\"Sheet names:\", wb.sheetnames)\n",
        "\n",
        "for sheet_name in wb.sheetnames:\n",
        "    ws = wb[sheet_name]\n",
        "    headers = [cell.value for cell in ws[1]]\n",
        "\n",
        "    percentile_cols = [\n",
        "        h for h in headers\n",
        "        if isinstance(h, str) and h.endswith(\"_percentile\")\n",
        "    ]\n",
        "\n",
        "    normal_metric_cols = [\n",
        "        h for h in headers\n",
        "        if h not in [\"company_id\", \"company_name\"]\n",
        "        and isinstance(h, str)\n",
        "        and not h.endswith(\"_percentile\")\n",
        "    ]\n",
        "\n",
        "    last_row_values = [cell.value for cell in ws[ws.max_row]]\n",
        "\n",
        "    print(\"\\nSheet:\", sheet_name)\n",
        "    print(\"Rows:\", ws.max_row)\n",
        "    print(\"Columns:\", ws.max_column)\n",
        "    print(\"Metric columns:\", len(normal_metric_cols))\n",
        "    print(\"Percentile columns:\", len(percentile_cols))\n",
        "    print(\"Last row starts with:\", last_row_values[:2])"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/"
        },
        "id": "qnAu2Py1ZQRq",
        "outputId": "f92a6445-2134-4234-da78-6fc1ebec3896"
      },
      "execution_count": 8,
      "outputs": [
        {
          "output_type": "stream",
          "name": "stdout",
          "text": [
            "Total sheets: 11\n",
            "Sheet names: ['Automobiles', 'Consumer Finance', 'FMCG', 'IT Services', 'Life Insurance', 'Oil & Gas', 'Pharmaceuticals', 'Power & Utilities', 'Private Banks', 'Public Sector Banks', 'Steel']\n",
            "\n",
            "Sheet: Automobiles\n",
            "Rows: 9\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Consumer Finance\n",
            "Rows: 5\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: FMCG\n",
            "Rows: 9\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: IT Services\n",
            "Rows: 7\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Life Insurance\n",
            "Rows: 6\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Oil & Gas\n",
            "Rows: 7\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Pharmaceuticals\n",
            "Rows: 7\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Power & Utilities\n",
            "Rows: 9\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Private Banks\n",
            "Rows: 7\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Public Sector Banks\n",
            "Rows: 6\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n",
            "\n",
            "Sheet: Steel\n",
            "Rows: 6\n",
            "Columns: 20\n",
            "Metric columns: 8\n",
            "Percentile columns: 10\n",
            "Last row starts with: [None, None]\n"
          ]
        }
      ]
    },
    {
      "cell_type": "code",
      "source": [
        "from peer import load_peer_groups, generate_peer_comparison_excel\n",
        "import pandas as pd\n",
        "from google.colab import files\n",
        "\n",
        "ratios = pd.read_csv(\"financial_ratios_generated.csv\")\n",
        "peer_groups = load_peer_groups(\"peer_groups_cleaned.csv\")\n",
        "\n",
        "ratios[\"fiscal_year\"] = pd.to_numeric(ratios[\"fiscal_year\"], errors=\"coerce\")\n",
        "\n",
        "latest = (\n",
        "    ratios\n",
        "    .dropna(subset=[\"fiscal_year\"])\n",
        "    .sort_values([\"company_id\", \"fiscal_year\"])\n",
        "    .groupby(\"company_id\")\n",
        "    .tail(1)\n",
        "    .reset_index(drop=True)\n",
        ")\n",
        "\n",
        "generate_peer_comparison_excel(\n",
        "    latest,\n",
        "    peer_groups,\n",
        "    output_path=\"output/peer_comparison.xlsx\"\n",
        ")\n",
        "\n",
        "files.download(\"output/peer_comparison.xlsx\")"
      ],
      "metadata": {
        "colab": {
          "base_uri": "https://localhost:8080/",
          "height": 453
        },
        "id": "oVPqVMBuc4yA",
        "outputId": "d27f0747-c971-4328-98a3-7fd2f2bf77bc"
      },
      "execution_count": 9,
      "outputs": [
        {
          "output_type": "error",
          "ename": "ModuleNotFoundError",
          "evalue": "No module named 'peer'",
          "traceback": [
            "\u001b[0;31m---------------------------------------------------------------------------\u001b[0m",
            "\u001b[0;31mModuleNotFoundError\u001b[0m                       Traceback (most recent call last)",
            "\u001b[0;32m/tmp/ipykernel_1418/3961797134.py\u001b[0m in \u001b[0;36m<cell line: 0>\u001b[0;34m()\u001b[0m\n\u001b[0;32m----> 1\u001b[0;31m \u001b[0;32mfrom\u001b[0m \u001b[0mpeer\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mload_peer_groups\u001b[0m\u001b[0;34m,\u001b[0m \u001b[0mgenerate_peer_comparison_excel\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[0m\u001b[1;32m      2\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mpandas\u001b[0m \u001b[0;32mas\u001b[0m \u001b[0mpd\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      3\u001b[0m \u001b[0;32mfrom\u001b[0m \u001b[0mgoogle\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mcolab\u001b[0m \u001b[0;32mimport\u001b[0m \u001b[0mfiles\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      4\u001b[0m \u001b[0;34m\u001b[0m\u001b[0m\n\u001b[1;32m      5\u001b[0m \u001b[0mratios\u001b[0m \u001b[0;34m=\u001b[0m \u001b[0mpd\u001b[0m\u001b[0;34m.\u001b[0m\u001b[0mread_csv\u001b[0m\u001b[0;34m(\u001b[0m\u001b[0;34m\"financial_ratios_generated.csv\"\u001b[0m\u001b[0;34m)\u001b[0m\u001b[0;34m\u001b[0m\u001b[0;34m\u001b[0m\u001b[0m\n",
            "\u001b[0;31mModuleNotFoundError\u001b[0m: No module named 'peer'",
            "",
            "\u001b[0;31m---------------------------------------------------------------------------\u001b[0;32m\nNOTE: If your import is failing due to a missing package, you can\nmanually install dependencies using either !pip or !apt.\n\nTo view examples of installing some common dependencies, click the\n\"Open Examples\" button below.\n\u001b[0;31m---------------------------------------------------------------------------\u001b[0m\n"
          ],
          "errorDetails": {
            "actions": [
              {
                "action": "open_url",
                "actionText": "Open Examples",
                "url": "/notebooks/snippets/importing_libraries.ipynb"
              }
            ]
          }
        }
      ]
    },
    {
      "cell_type": "code",
      "source": [],
      "metadata": {
        "id": "ly0fCiXafDBt"
      },
      "execution_count": null,
      "outputs": []
    }
  ]
}