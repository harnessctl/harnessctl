---
name: platform-export
description: Cross-platform Godot 4 export — Windows, macOS, Linux, Android, iOS. Prerequisites, export_presets.cfg, CLI commands, and platform gotchas.
---

# Platform Export

Export a Godot 4 project to Windows, macOS, Linux, Android, and iOS.

## Prerequisites (All Platforms)

- **Godot 4** with export templates installed:
  ```bash
  # Download matching templates (replace version)
  godot --headless --export-templates-install /path/to/Godot_v4.x-stable_export_templates.tpz
  ```
- **Project validates cleanly:** `timeout 60 godot --headless --quit 2>&1` — no errors

## Platform-Specific Prerequisites

### Windows

- **Host:** Windows, macOS, or Linux
- **Optional:** `rcedit` for icon/metadata embedding (Windows host only)
- No code signing required for distribution outside Microsoft Store

### macOS

- **Host:** macOS required for signed/notarized builds; cross-compile from Linux/Windows produces unsigned `.app`
- **Optional:** Xcode command line tools, Apple Developer account (for notarization)
- **Codesigning:** `codesign` + Developer ID certificate for distribution outside App Store

### Linux

- **Host:** Any (Windows, macOS, Linux)
- No special requirements — simplest export target

### Android

- **Host:** Windows, macOS, or Linux
- **OpenJDK 17** — `java -version` must report 17.x
- **Android SDK** — with platform-tools and build-tools
- **Debug keystore** — generated or provided
- **Editor settings** configured with Java/SDK/keystore paths:
  ```
  export/android/java_sdk_path
  export/android/android_sdk_path
  export/android/debug_keystore
  export/android/debug_keystore_user
  export/android/debug_keystore_pass
  ```

### iOS

- **Host:** macOS only (Xcode required)
- **Xcode** with iOS SDK
- **Apple Developer account** with provisioning profiles and signing certificates
- **Team ID** and **Bundle Identifier** configured
- Most complex export target — requires physical macOS machine

---

## Export Workflow

### 1. Configure project.godot

Add platform-specific settings as needed:

```ini
[rendering]

# Android/iOS — required for mobile GPU compatibility:
textures/vram_compression/import_etc2_astc=true

# Desktop — optional quality settings:
anti_aliasing/quality/msaa_3d=2
```

**CRITICAL for Android:** Without `textures/vram_compression/import_etc2_astc=true`, export silently fails with a blank configuration error.

### 2. Create export_presets.cfg

Place in project root. Each platform is a numbered `[preset.N]` section. Include only the platforms you need.

#### Windows Preset

```ini
[preset.0]

name="Windows"
platform="Windows Desktop"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
patches=[]
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.0.options]

custom_template/debug=""
custom_template/release=""
binary_format/embed_pck=true
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
codesign/enable=false
application/modify_resources=false
application/icon=""
application/console_wrapper_icon=""
application/icon_interpolation=4
application/file_version=""
application/product_version=""
application/company_name=""
application/product_name=""
application/file_description=""
application/copyright=""
application/trademarks=""
application/export_angle=0
ssh_remote_deploy/enabled=false
```

#### macOS Preset

```ini
[preset.1]

name="macOS"
platform="macOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
patches=[]
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.1.options]

custom_template/debug=""
custom_template/release=""
binary_format/architecture="universal"
codesign/enable=false
codesign/identity=""
codesign/certificate_file=""
codesign/certificate_password=""
codesign/provisioning_profile=""
codesign/entitlements/custom_file=""
codesign/entitlements/allow_jit_code_execution=false
codesign/entitlements/allow_unsigned_executable_memory=false
codesign/entitlements/allow_dyld_environment_variables=false
notarization/enable=false
application/icon=""
application/bundle_identifier="com.example.PROJECTNAME"
application/signature=""
application/app_category="Games"
application/short_version="1.0"
application/version="1.0"
application/copyright=""
application/min_macos_version="10.13"
application/export_angle=0
ssh_remote_deploy/enabled=false
```

#### Linux Preset

```ini
[preset.2]

name="Linux"
platform="Linux"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
patches=[]
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.2.options]

custom_template/debug=""
custom_template/release=""
binary_format/embed_pck=true
binary_format/architecture="x86_64"
texture_format/s3tc_bptc=true
texture_format/etc2_astc=false
ssh_remote_deploy/enabled=false
```

#### Android Preset

```ini
[preset.3]

name="Android"
platform="Android"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
patches=[]
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.3.options]

custom_template/debug=""
custom_template/release=""
gradle_build/use_gradle_build=false
gradle_build/gradle_build_directory=""
gradle_build/android_source_template=""
gradle_build/export_format=0
architectures/armeabi-v7a=false
architectures/arm64-v8a=true
architectures/x86=false
architectures/x86_64=false
keystore/debug=""
keystore/debug_user=""
keystore/debug_password=""
keystore/release=""
keystore/release_user=""
keystore/release_password=""
version/code=1
version/name="1.0"
package/unique_name="com.example.PROJECTNAME"
package/name=""
package/signed=true
package/app_category=2
package/retain_data_on_uninstall=false
package/exclude_from_recents=false
package/show_in_android_tv=false
package/show_in_app_library=true
package/show_as_launcher_app=false
launcher_icons/main_192x192=""
launcher_icons/adaptive_foreground_432x432=""
launcher_icons/adaptive_background_432x432=""
launcher_icons/adaptive_monochrome_432x432=""
graphics/opengl_debug=false
xr_features/xr_mode=0
screen/immersive_mode=true
screen/support_small=true
screen/support_normal=true
screen/support_large=true
screen/support_xlarge=true
user_data_backup/allow=false
command_line/extra_args=""
apk_expansion/enable=false
apk_expansion/SALT=""
apk_expansion/public_key=""
permissions/custom_permissions=PackedStringArray()
permissions/internet=false
```

#### iOS Preset

```ini
[preset.4]

name="iOS"
platform="iOS"
runnable=true
dedicated_server=false
custom_features=""
export_filter="all_resources"
include_filter=""
exclude_filter=""
export_path=""
patches=[]
encryption_include_filters=""
encryption_exclude_filters=""
encrypt_pck=false
encrypt_directory=false
script_export_mode=2

[preset.4.options]

custom_template/debug=""
custom_template/release=""
application/app_store_team_id=""
application/provisioning_profile_uuid_debug=""
application/provisioning_profile_uuid_release=""
application/bundle_identifier="com.example.PROJECTNAME"
application/signature=""
application/short_version="1.0"
application/version="1.0"
application/icon_1024x1024=""
application/launch_screens_interpolation=4
application/export_project_only=false
application/min_ios_version="12.0"
architectures/arm64=true
capabilities/access_wifi=false
capabilities/push_notifications=false
user_data/accessible_from_files_app=false
user_data/accessible_from_itunes_share=false
privacy/camera=false
privacy/microphone=false
privacy/photolibrary=false
icons/iphone_120x120=""
icons/iphone_180x180=""
icons/ipad_76x76=""
icons/ipad_152x152=""
icons/ipad_167x167=""
storyboard/use_launch_screen_storyboard=true
storyboard/image_scale_mode=0
storyboard/custom_image@2x=""
storyboard/custom_image@3x=""
storyboard/use_custom_bg_color=false
storyboard/custom_bg_color=Color(0, 0, 0, 1)
```

Replace `PROJECTNAME` in `package/unique_name` and `bundle_identifier` with the actual project name (lowercase, no spaces/special chars).

### 3. Export

```bash
mkdir -p build

# Windows — produces .exe + .pck
godot --headless --export-debug "Windows" build/game.exe

# macOS — produces .zip containing .app bundle
godot --headless --export-debug "macOS" build/game.zip

# Linux — produces executable binary
godot --headless --export-debug "Linux" build/game.x86_64

# Android — produces .apk
godot --headless --export-debug "Android" build/game.apk

# iOS — produces Xcode project (.xcodeproj)
godot --headless --export-debug "iOS" build/game.ipa
```

The preset name in quotes must match the `name=` field in `export_presets.cfg`.

For release builds, use `--export-release` instead of `--export-debug`.

---

## Platform Gotchas

### Windows

- `binary_format/embed_pck=true` creates a single `.exe` with data embedded — simpler distribution
- Without `rcedit`, the `.exe` has no custom icon or version metadata (functional, just generic icon)
- Windows Defender SmartScreen may block unsigned executables — users need to click "Run anyway"

### macOS

- Unsigned apps trigger Gatekeeper — users must right-click → Open on first launch
- For distribution: `codesign --deep -s "Developer ID Application: ..." game.app`
- Notarization: `xcrun notarytool submit game.zip --apple-id ... --team-id ... --password ...`
- Universal binary (`architecture="universal"`) supports both Intel and Apple Silicon

### Linux

- Mark executable: `chmod +x game.x86_64`
- AppImage or Flatpak wrapping for broader distribution (out of scope for basic export)
- `texture_format/s3tc_bptc=true` required for desktop GPU compatibility

### Android

- **Blank config error** — missing `textures/vram_compression/import_etc2_astc=true` in project.godot
- **Keystore error** — all three editor settings (`debug_keystore`, `debug_keystore_user`, `debug_keystore_pass`) must be set together or none (falls back to debug keystore)
- **`cannot connect to daemon`** — benign, no adb server running
- **Gradle-only fields** — `min_sdk`, `target_sdk`, `compress_native_libraries` cause errors when `use_gradle_build=false`
- ARM64 only (`arm64-v8a=true`) covers 98%+ of modern Android devices

### iOS

- Export produces an Xcode project — must open in Xcode on macOS to build `.ipa`
- Provisioning profiles must match the bundle identifier exactly
- Debug builds require a development provisioning profile; TestFlight/App Store requires distribution profile
- Physical device testing requires the device UDID in the provisioning profile
- Most common failure: mismatched Team ID, bundle ID, or expired provisioning profile

---

## Touch Input (Mobile)

For Android/iOS, add touch controls to the project:

```gdscript
# In project.godot:
# [input_devices]
# pointing/emulate_touch_from_mouse=true
# pointing/emulate_mouse_from_touch=true

# Or add virtual joystick/buttons in a CanvasLayer
# Use InputEventScreenTouch and InputEventScreenDrag for direct touch
```

## Multi-Platform project.godot

When targeting multiple platforms, combine rendering settings:

```ini
[rendering]

# Desktop quality
anti_aliasing/quality/msaa_3d=2
lights_and_shadows/directional_shadow/soft_shadow_filter_quality=3

# Mobile compatibility
textures/vram_compression/import_etc2_astc=true
```

Desktop exports ignore ETC2/ASTC (they use S3TC/BPTC). Mobile exports ignore MSAA/shadow quality settings they don't support. Both can coexist.
