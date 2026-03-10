[app]
title = Ball Fights
package.name = ballfights
package.domain = com.devongoodman
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf
version = 1.0.0
requirements = python3,pygame==2.6.1
p4a.bootstrap = sdl2
p4a.branch = develop

# Android configuration
android.permissions = INTERNET
android.api = 34
android.minapi = 21
android.ndk_api = 21
android.archs = arm64-v8a
android.accept_sdk_license = True

# App settings
orientation = landscape
fullscreen = 1
android.allow_backup = True

# Build
log_level = 2
warn_on_root = 1

[buildozer]
log_level = 2
warn_on_root = 1
