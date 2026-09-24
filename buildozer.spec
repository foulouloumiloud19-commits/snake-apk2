[app]
title = Rival Centipede
package.name = rivalcentipede
package.domain = org.miloud
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ogg,txt
version = 0.1
requirements = python3,kivy==2.2.1,plyer

orientation = portrait
fullscreen = 0
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True
android.api = 33
android.minapi = 21
android.ndk_api = 21

[buildozer]
log_level = 2
warn_on_root = 1
