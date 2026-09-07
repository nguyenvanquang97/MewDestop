#import "NekoWindowBridge.h"

@implementation NekoWindowBridge

+ (void)configureWindowForDesktopPet:(NSWindow *)window {
    if (!window) return;
    
    // 1. Transparency setup
    [window setOpaque:NO];
    [window setBackgroundColor:[NSColor clearColor]];
    [window setHasShadow:NO];
    
    // 2. Borderless
    [window setStyleMask:NSWindowStyleMaskBorderless];
    
    // 3. Floating on top of normal windows
    [window setLevel:NSFloatingWindowLevel];
    
    // 4. Visible across all Mission Control desktops / Spaces
    [window setCollectionBehavior:(NSWindowCollectionBehaviorCanJoinAllSpaces | 
                                   NSWindowCollectionBehaviorStationary | 
                                   NSWindowCollectionBehaviorIgnoresCycle)];
}

+ (void)setIgnoresMouseEvents:(BOOL)ignore forWindow:(NSWindow *)window {
    if (!window) return;
    [window setIgnoresMouseEvents:ignore];
}

+ (void)setAlwaysOnTop:(BOOL)onTop forWindow:(NSWindow *)window {
    if (!window) return;
    [window setLevel:(onTop ? NSFloatingWindowLevel : NSNormalWindowLevel)];
}

@end
