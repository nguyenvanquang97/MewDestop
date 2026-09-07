# NekoDesk macOS Native Bridge

## Overview
This native module provides Objective-C/Swift integration with macOS `NSWindow` and `AppKit` APIs.

Godot 4's built-in `DisplayServer.window_set_mouse_passthrough()` on macOS sets `[window setIgnoresMouseEvents:]` and window hit-testing under the hood. In the event that custom `NSWindow` behaviors are needed (such as `NSWindowCollectionBehaviorCanJoinAllSpaces`, ignoring Mission Control cycles, or custom floating levels), this bridge provides direct hooks.

## Files
- `NekoWindowBridge.h`: C/Obj-C API declaration.
- `NekoWindowBridge.m`: Implementation targeting macOS Cocoa / AppKit.

## Key Properties Configured:
1. `[window setOpaque:NO]` & `[window setBackgroundColor:[NSColor clearColor]]`: Ensures true per-pixel transparency.
2. `[window setStyleMask:NSWindowStyleMaskBorderless]`: Removes title bar, close buttons, and window frames.
3. `[window setLevel:NSFloatingWindowLevel]`: Keeps the pet above normal desktop application windows without locking modal dialogs.
4. `[window setCollectionBehavior:NSWindowCollectionBehaviorCanJoinAllSpaces]`: Keeps the pet present when switching macOS Spaces or Virtual Desktops.
5. `[window setIgnoresMouseEvents:YES/NO]`: Allows native click-through when mouse is outside the pet's hitbox.
