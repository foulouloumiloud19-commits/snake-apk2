[app]

# (string) Title of your application
title = Rival Centipede

# (string) Package name
package.name = rivalcentipede

# (string) Package domain (needed for android packaging)
package.domain = org.foulolou

# (str) Source code where the main.py lives
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,ogg,txt

# (string) Application versioning
version = 1.0

# (list) Application requirements
# تم تصحيحها بإضافة pygame و plyer وحذف kivy
requirements = python3,pygame,plyer

# (str) Supported orientation (one of landscape, sensorLandscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen
fullscreen = 1

# (list) Permissions
android.permissions = VIBRATE

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (int) Target Android API
android.api = 33

# (int) Minimum API your APK will support
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (bool) Accept SDK license
android.accept_sdk_license = True

# (bool) Allow backup
android.allow_backup = True

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 1
