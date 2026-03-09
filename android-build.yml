name: Build Android APK

on:
  workflow_dispatch:
  push:
    branches: [ "main", "master" ]
    paths:
      - "buildozer.spec"
      - "main.py"
      - "app_mobile_kivy.py"
      - "correcao_qrcode_simples.py"
      - ".github/workflows/android-build.yml"

jobs:
  build-apk:
    runs-on: ubuntu-22.04
    timeout-minutes: 90

    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Setup Java
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "17"

      - name: Install system deps
        run: |
          sudo apt-get update
          sudo apt-get install -y \
            git zip unzip autoconf automake libtool pkg-config \
            zlib1g-dev libncurses5-dev libffi-dev libssl-dev \
            libsqlite3-dev libjpeg-dev libfreetype6-dev libpng-dev \
            openjdk-17-jdk

      - name: Install build tools
        run: |
          python -m pip install --upgrade pip setuptools wheel
          python -m pip install cython buildozer

      - name: Build debug APK
        run: |
          buildozer android debug

      - name: Upload APK artifact
        uses: actions/upload-artifact@v4
        with:
          name: CorrecaoProvaQR-apk
          path: |
            bin/*.apk
          if-no-files-found: error
