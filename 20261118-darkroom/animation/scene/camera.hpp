#pragma once

constexpr int width=528,height=304,waterFrames=180,loopFrames=360;
constexpr float framesPerSecond=25.f;
const V eye{91,-63,146},forward=norm(V{-18,158,113.7f}-eye),
        right=norm(cross(forward,{0,0,1})),up=cross(right,forward);
constexpr float focalLength=404.f,focusDistance=218.f,lensOpening=.43f;
