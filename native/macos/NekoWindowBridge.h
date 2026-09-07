#import <Cocoa/Cocoa.h>

@interface NekoWindowBridge : NSObject

/// Configures an NSWindow for transparent, borderless, floating desktop companion behavior
+ (void)configureWindowForDesktopPet:(NSWindow *)window;

/// Enables or disables click-through on the entire window
+ (void)setIgnoresMouseEvents:(BOOL)ignore forWindow:(NSWindow *)window;

/// Sets whether the window stays floating on top of all application windows
+ (void)setAlwaysOnTop:(BOOL)onTop forWindow:(NSWindow *)window;

@end
