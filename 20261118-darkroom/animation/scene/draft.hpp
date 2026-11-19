#pragma once

namespace draft {
constexpr float seconds=loopFrames/framesPerSecond;
float wrapped(float time){return time-seconds*std::floor(time/seconds);}
float pressure(float time){
 float t=wrapped(time);
 float first=step(.18f,1.64f,t)*(1-step(2.01f,3.95f,t));
 float release=step(3.66f,4.63f,t)*(1-step(4.77f,5.79f,t));
 float second=step(6.32f,8.34f,t)*(1-step(8.53f,10.34f,t));
 return first*(.91f+.09f*step(1.14f,1.75f,t))-.15f*release+.68f*second;
}

// Two damped responses to the same breath of air. The stitched edge and the
// inner folds carry different amounts of cloth below the tieback.
struct Response {
 static constexpr int hz=200;
 static constexpr int count=loopFrames*hz/25;
 std::array<std::array<float,2>,count+1> displacement{};
 Response(){
  std::array<float,2> x{},v{};
  for(int i=0;i<=count;i++){
   float t=float(i)/hz;
   for(int j=0;j<2;j++){
    float w=j?4.12f:4.91f,damping=j?.57f:.58f;
    float drive=pressure(t-(j?.21f:0.f));
    displacement[i][j]=x[j]*(1-step(12.53f,13.42f,t));
    v[j]+=(w*w*(drive-x[j])-2*damping*w*v[j])/hz;
    x[j]+=v[j]/hz;
   }
  }
 }
 std::array<float,2> at(float time)const{
  float n=wrapped(time)*hz;
  int i=std::clamp(int(n),0,count-1);
  float leading=mix(displacement[i][0],displacement[i+1][0],n-i);
  float trailing=mix(displacement[i][1],displacement[i+1][1],n-i);
  // At less than a hundredth of a pixel the cloth has visually settled.
  // Ease it to its exact coordinates so the palette cannot chatter on a threshold.
  float settle=step(.0011f,.0055f,std::max(std::abs(leading),std::abs(trailing)));
  constexpr float fabricResponse=.74f;
  return {leading*settle*fabricResponse,trailing*settle*fabricResponse};
 }
};
}
