[app]
title = Rival Centipede
package.name = rivalcentipede
package.domain = org.foulolou
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ogg,txt
version = 1.0

requirements = python3,pygame,plyer

orientation = portrait
fullscreen = 1

android.permissions = VIBRATE
android.archs = arm64-v8a, armeabi-v7a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
