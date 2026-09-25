[app]
title = Snake Game
package.name = snakegame
package.domain = org.test
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 0.1

# المكتبات الأساسية بدون تعارض
requirements = python3,kivy

orientation = portrait
fullscreen = 0

# المعماريات المدعومة رسمياً
android.archs = arm64-v8a, armeabi-v7a

# إصدارات أندرويد المتوافقة مع سيرفرات البناء الحالية
android.api = 33
android.minapi = 21

# الموافقة على رخص SDK تلقائياً
android.accept_sdk_license = True
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
