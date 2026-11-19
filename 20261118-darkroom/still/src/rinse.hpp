#pragma once

// A damp fibre print floats just below the surface. Its raised corner, the
// jet and the steel all share this waterline and the same world coordinates.
namespace rinse {
constexpr float wavePhase=3.2f;
constexpr float level=82.25f, paperX=-56.0f, paperY=44.9f;
constexpr float angle=-17.5f, paperW=39.f, paperH=29.7f;

V sheet(float u,float v){
 float x=(u-.5f)*paperW,y=(.5f-v)*paperH,a=rad(angle);
 return {paperX+x*std::cos(a)-y*std::sin(a),paperY+x*std::sin(a)+y*std::cos(a),
       82.10f+1.35f*std::pow(u,4.4f)*std::pow(1-v,2.f)+.16f*std::sin(u*4.25f+v*.8f)};
}

float height(float x,float y){
 float dx=x-rippleOrigin.x,dy=y-rippleOrigin.y;
 float d=std::hypot(dx,dy);
 // Crest spacing opens out between packets. An ever smaller share of their
 // energy returns from the sloping near and far sides of the basin.
 auto returning=[&](float imageY,float phase){
  float r=std::hypot(dx,y-imageY);
  return .056f*std::sin(1.32f*r+phase-wavePhase*.81f)*std::exp(-r/48.f);
 };
 float direction=(dx*.81f+dy*.59f)/(d+.8f);
 float across=(dy*.78f-dx*.625f)/(d+.8f);
 float wave=1.56f*d-wavePhase+.53f*std::sin(.29f*d+.44f*direction)+.33f*direction+.36f*across*std::sin(.22f*d);
 float envelope=(.74f+.26f*std::cos(.33f*d+.83f*direction-.30f*wavePhase))*.29f*std::exp(-d/28.f)/std::sqrt(1+.10f*d);
 float outward=envelope*(std::sin(wave)+.15f*std::sin(2*wave-.65f));
 float impact=-.35f*std::exp(-d*d/1.65f)+.13f*std::exp(-std::pow((d-1.42f)/.55f,2.f));
 float incoming=returning(2*18.2f-rippleOrigin.y,1.33f)+returning(2*74.1f-rippleOrigin.y,-.41f);
 float broad=.036f*std::sin(.28f*x-.41f*y+.60f*std::sin(y*.086f))
            +.029f*std::sin(.19f*x+.31f*y-.27f*std::cos(x*.13f));
 // Invert the print's placement so that the small capillary ridge meets its
 // physical edge. The crest disappears wherever the stock lies underwater.
 float a=rad(angle),sx=x-paperX,sy=y-paperY;
 float u=.5f+(sx*std::cos(a)+sy*std::sin(a))/paperW;
 float v=.5f-(-sx*std::sin(a)+sy*std::cos(a))/paperH;
 float edgeX=(std::abs(u-.5f)-.5f)*paperW,edgeY=(std::abs(v-.5f)-.5f)*paperH;
 float outside=std::hypot(std::max(edgeX,0.f),std::max(edgeY,0.f))+std::min(std::max(edgeX,edgeY),0.f);
 float contact=0, damping=1;
 if(outside<5.f){
  float raised=sheet(sat(u),sat(v)).z-level;
  float affinity=step(-.13f,.14f,raised);
  contact=.155f*affinity*std::exp(-std::abs(outside)/.42f);
  damping=mix(1,.44f,affinity*(1-step(.02f,3.7f,outside)));
 }
 float wetting=.125f*std::exp(-std::max(.0f,28.15f-std::abs(y-46.f))/.31f);
 return level+damping*(outward+incoming+broad)+impact+contact+wetting;
}

V waterSurface(float u,float v){
 constexpr float hw=67.95f,hh=28.15f,r=5.2f;
 float y=(2*v-1)*hh;
 float round=std::max(0.f,std::abs(y)-hh+r);
 float halfWidth=hw-r+std::sqrt(std::max(0.f,r*r-round*round));
 float x=-53.5f+(2*u-1)*halfWidth;
 y+=46.f;
 return {x,y,height(x,y)};
}
} // namespace rinse
