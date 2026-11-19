#pragma once
struct Section{float z,w,d,r;int material;};
// A pressed or rolled rectangular cross-section with genuine radiused corners.
std::vector<V> roundContour(float w,float d,float r,float z,int div=7){
 r=std::min({r,.49f*w,.49f*d});std::vector<V> row;
 for(int corner=0;corner<4;corner++){float a=-90+90*corner,sx=(corner<2?1:-1),sy=(corner==0||corner==3?-1:1);
  for(int j=0;j<=div;j++){float angle=rad(a+90.f*j/div);row.push_back({sx*(w*.5f-r)+r*std::cos(angle),sy*(d*.5f-r)+r*std::sin(angle),z});}
 }return row;
}
void pressed(V o,std::vector<Section> rings,bool bottom,bool top){
 std::vector<V> prev;
 for(size_t k=0;k<rings.size();k++){auto a=rings[k];auto row=roundContour(a.w,a.d,a.r,a.z);
  if(k){for(size_t i=0;i<row.size();i++){int j=(i+1)%row.size();quad(o+prev[i],o+prev[j],o+row[j],o+row[i],a.material);}}
  if((bottom&&k==0)||(top&&k+1==rings.size()))for(size_t i=0;i<row.size();i++)face(o+V{0,0,a.z},o+row[i],o+row[(i+1)%row.size()],a.material);
  prev.swap(row);
 }
}
void diskUV(V center,V right,V up,float radius,int m,int n=60){
 V normal=norm(cross(right,up));for(int j=0;j<n;j++){
  float a=2*PI*j/n,b=2*PI*(j+1)/n;
  auto vert=[&](float t){return Vertex{center+(right*std::cos(t)+up*std::sin(t))*radius,normal,{.5f+.5f*std::cos(t),.5f-.5f*std::sin(t)}};};
  triangle({center,normal,{.5,.5}},vert(a),vert(b),m);
 }
}
void frontLabel(float x,float y,float z,float w,float h,int m){
 quad({x-w/2,y,z+h/2},{x+w/2,y,z+h/2},{x+w/2,y,z-h/2},{x-w/2,y,z-h/2},m);
}
void knob(V base,V axis,float radius,float reach,int material,int flutes=0){
 auto t=norm(axis);lathe(base,t,{{0,radius*.71f,iron},{.16f*reach,radius*.72f,iron},{.21f*reach,radius*.94f,material},{.30f*reach,radius,material},{.88f*reach,radius,material},{reach,radius*.87f,material}},32);
 if(flutes){V a=norm(cross(std::abs(t.z)>.9?V{1,0,0}:V{0,0,1},t)),b=cross(t,a);
  for(int j=0;j<flutes;j++){float ang=j*2*PI/flutes;V k=base+(.975f*radius)*(a*std::cos(ang)+b*std::sin(ang));
   rod(k+t*(reach*.32f),k+t*(reach*.81f),std::max(.10f,radius*.045f),material,5);}
 }
}
void screw(V c,V n,float r=.44f){V dir=norm(n),a=norm(cross(std::abs(dir.z)>.8?V{0,1,0}:V{0,0,1},dir));V b=cross(a,dir);
 lathe(c,dir,{{0,r,steel},{.12f,r*.86f,polished}},14);rod(c+.145f*dir-(a+b*.42f)*r*.57f,c+.145f*dir+(a+b*.42f)*r*.57f,r*.095f,black,5);}
void ledge(V p,V size,int m){box(p,size,m,.6f);}
void bottle(V p,float k,int label,float turnDeg=0){
 Scope s(turn(p,turnDeg));V axis{0,0,1};float R=5.6f*k;
 std::vector<Ring> profile;auto put=[&](float z,float r,int m){profile.push_back({z*k,r*k,m});};
 put(0,4.8,amber);put(.45,5.38,amber);put(1.3,5.55,amber);put(17,5.55,amber);
 put(19,5.35,amber);put(21,4.65,amber);put(22.8,3.15,amber);put(23.4,2.46,amber);
 put(25.1,2.48,amber);put(25.3,2.85,amber);put(25.9,2.85,amber);put(26.1,2.55,amber);
 lathe({},axis,profile,40);
 knob({0,0,25.6f*k},axis,2.92f*k,3*k,rubber,26);
 if(label>=0)patch(22,1,[&](float u,float v){float a=rad(-156+141*u);float r=R+.017f;return V{r*std::cos(a),r*std::sin(a),(15.4f-9.8f*v)*k};},stickers[label]);
 torus({0,0,1.25f*k},axis,5.5f*k,.10f*k,amber,36);
}
void can(V p,float r,float h,int m){
 lathe(p,{0,0,1},{{0,r*.92f,m},{.42f,r,m},{h-.8f,r,m},{h-.55f,r*1.04f,steel},{h,r,steel}},32);
 torus(p+V{0,0,.7f},{0,0,1},r,.23f,steel);
}
void paperBox(V p,V dim,float yaw,int col,int label=7){
 Scope s(turn(p,yaw));box({0,0,dim.z*.48f},{dim.x-.3f,dim.y-.3f,dim.z*.94f},col,.3f);
 box({0,0,dim.z*.86f},{dim.x,dim.y,dim.z*.29f},col,.32f);
 frontLabel(0,-dim.y/2-.04f,dim.z*.51f,dim.x*.65f,dim.z*.59f,stickers[label-4]);
}
void enlarger(){
 // Offset column with separate carriage and pinion; the lens always points
 // straight down onto the registered aperture in the four-blade easel.
 Scope dry(turn({12,161,86.5f},-16));
 projX=frame.a;projY=frame.b;
 box({0,13,1.35f},{61,58,2.7f},wood,.7f);
 for(float x:{-25.f,25.f})for(float y:{-9.f,36.f})lathe({x,y,-.65f},{0,0,1},{{0,2,black},{.8f,2.2f,rubber}},16);
 pressed({0,33,2.7f},{{0,17,13,2,black},{1.3f,17,13,2,grey},{3,12,10,1.5f,grey},{4.5f,10,8,1.4f,grey}},true,true);
 box({0,34,60.2f},{7,6.8f,111},iron,.6f);
 box({0,30.55f,60.2f},{3.2f,.9f,110.5f},steel,.18f);
 rod({-3.85f,31.7f,5.4f},{-3.85f,31.7f,114.6f},.66f,polished);
 rod({3.85f,31.7f,5.4f},{3.85f,31.7f,114.6f},.66f,polished);
 box({0,34,116.1f},{8.1f,7.4f,2.6f},black,.7f);
 for(int h=12;h<111;h+=2)box({.8f,30.06f,float(h)},{2.2f,.35f,.40f},iron);
 for(int h=15;h<112;h+=5)box({-2.67f,30.33f,float(h)},{h%10?.6f:1.f,.08f,.18f},offwhite);
 box({0,32.3f,82.8f},{11.1f,10.4f,19},grey,1.5f);
 box({0,29,87},{10.3f,12,5.3f},iron,.8f);
 for(float x:{-3.7f,3.7f}){
  box({x,17.5f,88.5f},{2.7f,20,4.7f},grey,.7f);
  rod({x,27.2f,78.4f},{x,13.1f,88.1f},1.42f,grey,12);
 }
 knob({5.4f,32,82},{1,0,0},4.25f,4.1f,black,21);
 rod({8.8f,32,82},{8.8f,35.7f,79.3f},.74f,steel);
 rod({8.8f,35.7f,79.3f},{12.5f,35.7f,79.3f},.86f,black);
 pressed({0,1,0},{{77,24,24,2,black},{78.8f,29,28,3,black},{80,30,29,3.4f,grey},
 {86,31.5f,30,4.1f,cream},{96,29.5f,29.1f,4,cream},{101.2f,23.8f,23.4f,3.7f,cream},{102.4f,21.5f,21.5f,3.4f,iron}},true,true);
 pressed({0,1,0},{{99,25.6f,25,3,iron},{99.55f,25.6f,25,3,steel}},false,false);
 lathe({0,2,102.5f},{0,0,1},{{0,8.6f,black},{1.2f,8.7f,iron},{2.4f,7.2f,iron},{2.8f,7,black}},44);
 for(int i=0;i<3;i++)lathe({0,2,105.2f+i*.93f},{0,0,1},{{0,6.1f,black},{.25f,7.1f,iron},{.55f,7.1f,black}},36);
 // Real vent recesses and the proud nickel badge sit in front of the enamel.
 for(int j=0;j<6;j++){
  float x=-7.85f+j*3.14f;
  box({x,-14.12f,92.1f},{1.32f,.25f,5.02f},black,.23f);
  box({x-.57f,-14.2f,92.05f},{.18f,.14f,4.36f},grey,.062f);
 }
 frontLabel(0,-14.19f,84.25f,17.55f,4.96f,stickers[4]);
 for(float x:{-9.6f,9.6f})screw({x,-14.21f,84.4f},{0,-1,0},.40f);
 for(int j=0;j<5;j++){
  float y=-6.3f+j*3.32f;
  box({15.43f,y,87.65f},{.30f,1.1f,4.9f},black,.17f);
 }
 // A rack-height scale and a brass cursor remain legible in the shadow.
 box({-2.43f,30.49f,44},{1.55f,.22f,72},cream,.06f);
 for(int h=10;h<80;h+=2)box({-2.63f,30.25f,float(h)},{h%10?.54f:1.16f,.08f,.23f},charcoal);
 box({-2.8f,28.7f,75.4f},{4.7f,.48f,.46f},brass,.12f);
 box({0,-.4f,75.3f},{24.5f,23,2.9f},black,.6f);
 box({-.8f,-.25f,73.8f},{29,21.8f,.77f},polished,.2f);
 box({-14.9f,-3,73.2f},{7.5f,6.2f,1.15f},charcoal,.36f);
 box({0,0,71.9f},{20,18,2.1f},iron,.4f);
 std::vector<Section> ribs;for(int j=0;j<=14;j++){float v=j/14.f,w=mix(10.f,19.1f,v)+(j%2?2.1f:-.4f);
  ribs.push_back({58.8f+v*12.6f,w,w*.9f,.58f,j%2?charcoal:black});}
 pressed({},ribs,true,true);
 box({.1f,.15f,58.5f},{13.4f,12.3f,1.1f},iron,.36f);
 lathe({0,0,51.95f},{0,0,1},{{0,3.2f,black},{.45f,3.7f,polished},{.95f,3.8f,black},{1.4f,3.5f,black},{2,4.1f,steel},{2.5f,4.2f,black},{3.7f,4.1f,black},{4.15f,3.68f,polished},{5.9f,3.6f,black},{6.4f,4.16f,black}},42);
 diskUV({0,0,51.94f},{1,0,0},{0,-1,0},2.59f,whiteLight,40);
 lensPos=frame.pos({0,0,51.92f});
 rod({9.4f,4,59.2f},{9.4f,4,77.6f},.56f,steel);
 knob({9,4,63.1f},{1,0,0},2.54f,3.3f,black,18);
 tube({{7,-1.5f,58.9f},{8,-2,54.1f},{10.5f,-2,52.4f},{14.5f,1.8f,52.4f}},.44f,polished,9,3);
 lathe({14.3f,2,51.7f},{0,0,1},{{0,3.7f,iron},{.49f,3.8f,black},{.65f,3.36f,redEnamel}},30);
 tube({{7.9f,11,95},{14,15,95},{14.4f,25,82},{9,32,66},{10,35,43},{13,38,25},{22,47,9},{25,51,15},{27,54,30}},.63f,rubber,10,6);
 // Four masking blades sit physically above the paper.
 box({0,0,3.65f},{45.8f,36.2f,1.8f},black,1.f);
 box({0,0,4.76f},{44.9f,35.1f,.68f},grey,.62f);
 box({0,0,paperLevel-86.5f-.055f},{39.8f,30.6f,.11f},palePaper);
 for(float y:{-15.5f,15.5f})box({0,y,5.28f},{42.2f,2.6f,.25f},iron,.09f);
 for(float x:{-20.4f,20.4f})box({x,0,5.37f},{3.3f,32,.25f},iron,.09f);
 for(int j=0;j<22;j++)box({-18.4f+j*1.71f,-16.13f,5.426f},{.17f,j%5?.57f:1.17f,.035f},offwhite);
 knob({21.8f,-12.5f,5.41f},{0,0,1},.95f,.75f,black);
}
#include "rinse.hpp"
void washBasin(){
 V o{-53.5f,46,0};
 int bathBottom=mat({.16f,.18f,.20f},.41f,.16f,Brushed);
 std::vector<Section> rings={
 {61,137,58,6,steel},{63,142,62,6.5f,steel},{83.3f,145,66,6.5f,steel},
 {87.7f,147,68,6.6f,steel},{89,147.3f,68.5f,6.7f,polished},{89.65f,146.1f,67.4f,6.3f,polished},
 {89.6f,141,62,5.5f,steel},{88.4f,138.8f,59.7f,5.0f,polished},{85.6f,137.2f,58.0f,5.f,steel},
 {74,131.5f,52,5.3f,steel},{69.9f,125,45.5f,6.7f,bathBottom},{69.2f,116,37.6f,6.1f,bathBottom}};
 pressed(o,rings,true,true);
 rippleOrigin={-32,47,rinse::level};

 mats[sheets[3]].ratio=rinse::paperW/rinse::paperH;

 lathe({1.5f,45,69.25f},{0,0,1},{{0,3.7f,iron},{.32f,3.9f,steel},{.44f,3.3f,black}},30);
 for(int j=0;j<5;j++){float a=j*PI/5;rod({1.5f+3.05f*std::cos(a),45+3.05f*std::sin(a),69.75f},{1.5f-3.05f*std::cos(a),45-3.05f*std::sin(a),69.75f},.14f,steel,6);}
 for(float x:{-117.f,10.f})for(float y:{19.f,73.f}){rod({x,y,3},{x,y,64},2.0f,steel);lathe({x,y,0},{0,0,1},{{0,2.6f,rubber},{1.7f,2.3f,rubber},{3.7f,2,steel}},16);}
 for(float y:{19.f,73.f})rod({-117,y,17},{10,y,17},1,steel);
 rod({10,19,17},{10,73,17},1.0f,steel);
 tube({{0,44,63},{0,44,47},{0,44,30},{0,46,25},{0,53,24},{0,59,29},{0,61,36},{-2,67,38},{-25,68,38}},2.5f,glazed,14,4);
 // A broad-spouted laboratory tap, two independent cross handles, and a thin stream.
 box({-35,77,90.15f},{33,10,1.7f},steel,.9f);
 for(float x:{-46.f,-24.f}){
  lathe({x,76,90.9f},{0,0,1},{{0,3.05f,chrome},{.78f,3.3f,polished},{1.4f,2.8f,polished},{2.2f,1.6f,chrome},{7.9f,1.65f,polished},{9,2.05f,chrome},{9.7f,1.8f,polished},{12.7f,1.15f,chrome}},28);
  for(int j=0;j<4;j++){float a=rad(19+90*j);V p{x,76,103.5f},v{std::cos(a),std::sin(a),.12f};
   rod(p,p+v*3.7f,.52f,chrome,10);oval(p+v*3.85f,{.81f,.81f,.72f},polished,14,7);}
  lathe({x,76,103.3f},{0,0,1},{{0,1.05f,chrome},{.65f,.88f,ivory}},20);
 }
 rod({-46,76,98.4f},{-24,76,98.4f},1.43f,polished);
 lathe({-35,76,96.2f},{0,0,1},{{0,2.05f,chrome},{3.4f,2.2f,polished},{4.9f,1.7f,chrome},{6.1f,1.5f,polished}},26);
 tube({{-35,76,101},{-35,76,115},{-35,75.5f,126.4f},{-34.6f,72,133},{-34,66,136.2f},{-33,59,136},{-32.5f,52,132.8f},{-32,47.8f,127.5f},{-32,47,121.8f}},1.35f,chrome,18,5);
 lathe({-32,47,120.3f},{0,0,1},{{0,1.68f,steel},{.5f,1.78f,chrome},{2.3f,1.65f,polished},{2.8f,1.4f,chrome}},28);
 rinse::jetMaterial=mat({.28,.36,.38},.08f,.80f,ClearWater);
 // Striped cotton crosses the rounded steel lip and hangs down its face.
 patch(40,39,[](float u,float v){
  float fold=std::sin(u*4.35f*PI+.72f*std::sin(v*3.1f)+.40f)+( .24f+.14f*v)*std::cos(u*8*PI-v*2.8f);
  float y=39+u*27+2.2f*v*std::cos(u*4.0f)+1.1f*std::sin(v*3.3f);
  float x,z;
  if(v<.23f){float t=v/.23f;x=mix(12.7f,17.6f,t);z=mix(86.9f,90.02f,t)+.39f*fold;}
  else if(v<.36f){float t=(v-.23f)/.13f;x=17.6f+2.91f*std::sin(t*PI*.5f);z=90.02f-1.65f*(1-std::cos(t*PI*.5f))+.35f*fold;}
  else{float t=(v-.36f)/.64f;x=20.51f+(.35f+2.27f*t)*fold+.85f*t;z=88.37f-t*(28.2f+2.8f*std::sin(u*5.9f))+.30f*fold;}
  return V{x,y,z};},linen);
}
