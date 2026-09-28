[app]
title = Snake Game
package.name = snakegame
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,wav,ogg
version = 0.1
requirements = python3,kivy
orientation = portrait
fullscreen = 1

[buildozer]
log_level = 2
warn_on_root = 1

[android]
android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True
android.release = False
