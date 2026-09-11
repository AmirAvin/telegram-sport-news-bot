name: Live Football Bot

on:
  workflow_dispatch:
  schedule:
    - cron: "*/2 * * * *"

permissions:
  contents: write

jobs:
  live-bot:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: pip install requests

      - name: Run Live Bot
        env:
          SPORTMONKS_TOKEN: ${{ secrets.SPORTMONKS_TOKEN }}
          BOT_TOKEN: ${{ secrets.BOT_TOKEN }}
          CHANNEL_ID: ${{ secrets.CHANNEL_ID }}
        run: python live_bot.py

      - name: Upload Sportmonks Test
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: sportmonks-test
          path: sportmonks_test.txt
