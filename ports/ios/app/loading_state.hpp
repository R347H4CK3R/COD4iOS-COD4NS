#pragma once
// Presentation timing uses monotonic elapsed time, independent of UIKit.
namespace kisak::loading {
enum class Result { Loading, Ready, Failed, TimedOut };
inline Result state(bool active,bool idle,bool gameOver,double elapsed) {
    if(active && gameOver) return Result::Failed;
    if(active && !idle) return Result::Ready;
    if(elapsed>=90.0) return Result::TimedOut;
    return Result::Loading;
}
}
