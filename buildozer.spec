[app]
title = CorrecaoProvaQR
package.name = correcao_prova_qr
package.domain = org.iema

source.dir = .
source.include_exts = py,png,jpg,jpeg,webp,pdf,json,kv
source.exclude_dirs = __pycache__,.git,.venv,venv,build,dist

version = 1.0.0

requirements = python3,kivy,opencv,numpy,qrcode,pillow,reportlab

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

android.permissions = CAMERA,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

log_level = 2

[buildozer]
warn_on_root = 1
