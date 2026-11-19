#pragma once
#include "screens.hpp"
#include "joinery.hpp"
#include "curtain.hpp"
#include "shelf.hpp"
V safeOrigin,safeDirection,safeHorizontal,safeVertical;
void cabinet(){
 // The dry bench ends before the plumbing return. Open shelves are deep
 // enough for the stock boxes and the paper safe.
 box({1,184,84.2f},{281,72,4.6f},mat({.40f,.285f,.19f},.56f,.039f,Oak),.75f);
 box({1,148.15f,82.4f},{281,2.4f,6.9f},mat({.44f,.29f,.197f},.62f,.038f,Oak),.53f);
 for(float x:{-132.f,-62.f,54.f,136.f})for(float y:{153.f,212.f})box({x,y,41},{4.4f,4.4f,82},grey,.32f);
 box({0,211,19},{268,2.4f,5.7f},grey,.35f);
 box({-97.5f,184,29},{72,62,2.4f},wood,.33f);
 box({-97.5f,184,54},{72,62,2.4f},wood,.33f);
 paperBox({-93,172,30.2f},{39,29,6.2f},-5,card);
 paperBox({-95,172,36.4f},{37,28,5.3f},2,iron);
 paperBox({-107,171,55.2f},{33,28,6.5f},2.5f,black);
 paperDrawers();
}
void roomShell(){
 box({0,31,-2},{312,455,4},baseFloor);
 box({3,222,132},{297,7,264},wall);
 box({-143.3f,40,132},{7,368,264},wall);
 box({148.6f,60,128},{5,337,256},wall);
 box({2,48,262},{298,373,5},wall);
 box({-139.39f,37,78.7f},{1.18f,369,157.4f},tile);
 box({-89.2f,218.07f,69},{101,1.35f,138},tile);
 box({52,218.07f,56},{181.6f,1.35f,112},tile);
 box({-138.6f,37,157.5f},{1.4f,369,1.05f},ceramic,.3f);
 box({-89.4f,217.6f,138.2f},{101.5f,1.2f,1.1f},ceramic,.25f);
 box({52,217.6f,112.2f},{181.6f,1.2f,1.1f},ceramic,.25f);
 // Water pipes on the tiled wall, real compression fittings at bends.
 for(int j=0;j<2;j++){
  float z=102+j*6.8f;float x=-135.9f;
  tube({{x,207,z+13},{x,207,z+2},{x,204,z},{x,44,z},{x,26,z},{x,23,z-3},{x,23,68}},.94f,copper,12,2);
  for(float y:{32.f,75.f,117.f,163.f,195.f}){
   rod({x,y-.95f,z},{x,y+.95f,z},1.32f,brass,12);
   box({-137.6f,y,z},{2.8f,1.1f,1.4f},iron,.24f);
  }
 }
 V vc{-134,97,109};rod(vc,vc+V{3.3f,0,0},1.1f,brass);torus(vc+V{4.3f,0,0},{1,0,0},3.5f,.56f,redEnamel,28);
 for(int j=0;j<3;j++){float a=2*PI*j/3;rod(vc+V{4.3f,0,0},vc+V{4.3f,3.47f*std::cos(a),3.47f*std::sin(a)},.35f,redEnamel,7);}
 // Threaded steel conduit, small junctions and the ceiling return.
 tube({{-137,158,168},{-137,158,200},{-137,154,205},{-137,137,205},{-137,136,212},{-137,205,212},{-134,215,212},{-126,216,212},{134,216,212}},.62f,steel,10,3);
 for(float x:{-107.f,-63.f,-18.f,30.f,76.f,127.f}){box({x,216.4f,212},{1.5f,1.7f,2.1f},iron,.22f);}
 box({-135.9f,133,207},{4,7.4f,8.6f},grey,.7f);
 box({37.5f,216.9f,119.7f},{9.3f,2.6f,13},cream,.64f);
 for(float z:{116.5f,123.2f}){
  box({37.5f,215.4f,z},{5.2f,.55f,4.1f},charcoal,.65f);
  for(float x:{36.4f,38.5f})box({x,215.1f,z+.3f},{.42f,.14f,1.24f},black);
 }
 tube({{37.4f,214.7f,115.8f},{37.3f,212.6f,111},{35,210,101},{37,197,89},{47,186,86.9f},{58,181,88.3f}},.45f,rubber,9,6);
 cabinet();
}
void safelight(){
 Scope moved(translation({0,25,-8}));
 // A red-glass wall lamp on a pivoting yoke. The luminous surface sits
 // ahead of the louvres and the area source is just outside the glass.
 V p{-127,128,178},n=norm(V{.88f,-.205f,-.427f});
 V a=norm(cross(V{0,0,1},n)),b=cross(n,a);
 box({-137.5f,128,177},{2.4f,14,22},grey,1.4f);
 for(float y:{123.3f,132.7f})for(float z:{169.3f,184.7f})screw({-136.2f,y,z},{1,0,0},.6f);
 tube({{-136,122,174},{-131,122,174},{-124.4f,121,178},{-121.5f,121.3f,180}},1.04f,iron,10,3);
 lathe(p,n,{{-3,6.2f,black},{0,7.5f,iron},{2,9.9f,iron},{7,13.1f,black},{10.8f,15.2f,iron},{12.6f,15.4f,iron},{13.4f,14.8f,black},{13.7f,13.7f,copper}},48);
 diskUV(p+n*13.74f,a,b,13.63f,safelens,56);
 torus(p+n*13.8f,n,13.83f,.6f,iron,50);
 for(float y:{-7.f,0.f,7.f}){
  float w=std::sqrt(13.7f*13.7f-y*y);std::vector<V> q;
  for(int j=0;j<=10;j++){float t=j/10.f;q.push_back(p+n*(14.0f+.83f*std::sin(t*PI))+a*mix(-w,w,t)+b*y);}
  tube(q,.28f,black,7,1);
 }
 for(int j=0;j<5;j++){float ang=j*2*PI/5+.2f;screw(p+n*13.17f+a*std::cos(ang)*14.9f+b*std::sin(ang)*14.9f,n,.46f);}
 // A deep semi-circular visor cuts off upward spill. Its upper surface picks up
 // a reflected red edge, while the underside stays almost black.
 for(int j=0;j<33;j++){
  float t0=rad(7+165.f*j/33),t1=rad(7+165.f*(j+1)/33);
  auto side=[&](float t,float depth){V rr=a*std::cos(t)+b*std::sin(t);
   return p+rr*(15.45f+depth*.56f)+n*(11.8f+depth*(3.3f+8.6f*std::sin(t)));};
  quad(side(t0,0),side(t1,0),side(t1,1),side(t0,1),iron);
 }
 // A hinged flag on the far side shields the dry bench. The camera sees
 // its rolled lip and hinge, while the rinse still receives the full light.
 int flock=mat({.0027f,.0023f,.0031f},.97f,0,Flock);
 auto flag=[&](float depth,float elevation){return p+a*(14.3f+depth*.08f)+n*(10.5f+depth)+b*elevation;};
 quad(flag(0,-7.4f),flag(0,8.1f),flag(10.2f,6.8f),flag(10.2f,-5.9f),flock);
 rod(flag(10.2f,-5.9f),flag(10.2f,6.8f),.17f,flock,8);
 rod(flag(0,-7.4f),flag(0,8.1f),.48f,steel,12);
 safeOrigin=frame.pos(p+n*15.05f);safeDirection=n;safeHorizontal=a;safeVertical=b;
 tube({{-137,131,170},{-136.5f,130,156},{-136.3f,122,152},{-135.6f,117,160},{-134,120,170},{-130,124,175}},.55f,rubber,8,5);
}
void tray(V pos,float w,float d,float height,int col,float yaw=0){
 Scope s(turn(pos,yaw));pressed({},{{0,w-3,d-3,3,col},{height-.9f,w,d,3.5f,col},{height,w+.7f,d+.7f,3.9f,col},{height+.24f,w-.7f,d-.7f,3.1f,col},{height-.75f,w-2.1f,d-2.1f,2.8f,col},{.82f,w-5.2f,d-5.2f,2.6f,col}},true,true);
 for(int j=-3;j<=3;j++){float x=j*w*.10f;box({x,0,1.05f},{.8f,d-10,.7f},col,.32f);}
}
#include "washer.hpp"
void tong(V p,float a){
 Scope s(turn(p,a));tube({{0,0,.1f},{3.7f,0,.5f},{14,0,3.6f},{19,0,4.0f},{21,0,3.1f},{20,0,2.1f},{16,0,2.2f},{3,0,-.1f},{0,0,-.15f}},.38f,steel,9,4);
 for(float z:{.06f,-.22f})box({.1f,0,z},{2.6f,1.30f,.55f},rubber,.23f);
}
void wetStation(){
 box({-104,116,86.4f},{67,67,3.6f},grey,.7f);
 box({-102,149,94},{70,2.8f,16},glazed,.6f);
 for(float x:{-132.f,-74.f})for(float y:{88.f,143.f})box({x,y,42.4f},{3.2f,3.2f,84.8f},steel,.33f);
 tray({-100,127,88.2f},43,28,5.6f,ivory,-2);
 tray({-100,127,93.5f},42.7f,27.8f,5.3f,glazed,1);
 tong({-92,113.4f,98.5f},57);
 bottle({-80.8f,92.1f,88.2f},1.09f,0,-20);
 bottle({-101,98,88.2f},.77f,2,10);
 // A broad collapsible stock bottle is placed here in the finishing geometry.
 // A graduated cylinder with stamped lines, and a coiled drain hose.
 lathe({-75.9f,113,88.2f},{0,0,1},{{0,3.5f,steel},{.5f,3.6f,steel},{1,2.1f,grey},{13,2.65f,grey},{13.4f,2.86f,polished},{14,2.7f,steel}},32);
 for(int j=0;j<7;j++)box({-75.8f,110.48f,91.1f+j*1.38f},{j%2?.88f:1.65f,.14f,.20f},offwhite);
 tube({{-132,99,103},{-129,93,103},{-119,90,97},{-113,85,84},{-104,80,69},{-89,82,58},{-79,91,60},{-87,101,72},{-104,102,74},{-110,95,63},{-96,84,53},{-77,86,54},{-73,95,66},{-76,108,74}},1.05f,rubber,12,5);
 // Compact supply shelf is secured to the wall with two triangular brackets.
 box({-108,205,146},{57,24,2},wood,.46f);
 for(float x:{-129.f,-87.f}){
  box({x,216,140},{2.6f,2.3f,13.4f},iron,.29f);
  rod({x,215,135},{x,196,145},.68f,iron);
 }
 supplyGlassware();graduatedJug();
}
void timer(){
 Scope local(turn({57,174.8f,86.5f},-18));
 pressed({},{{0,24,15,2.4f,black},{1.3f,24.4f,15.3f,2.5f,black},{3,23.1f,14.8f,2.4f,iron}},true,true);
 V p{0,1.9f,13.5f},n=norm(V{0,-1,.185f}),r{1,0,0},up=norm(cross(n,r));
 lathe(p-n*4,n,{{0,10.4f,iron},{.7f,11.2f,black},{5.0f,11.6f,iron},{5.8f,11.8f,steel},{6.1f,11.4f,black}},60);
 diskUV(p+n*2.17f,r,up,10.52f,clockFace);
 torus(p+n*2.2f,n,10.94f,.36f,polished);
 knob({10.4f,.8f,12.2f},{1,0,0},2.3f,2.8f,black,16);
}
V linePoint(float t){
 float sag=4.9f*4*t*(1-t);
 return {-91+227*t,211-166*t,204-34.7f*t-sag};
}
void peg(V p,float yaw,float tilt=0){
 Scope s(turn(p,yaw,tilt,5));
 for(int k:{-1,1}){
  V top{0,k*.93f,3.25f},bottom{0,k*.20f,-3.65f};
  tube({top,{0,k*.53f,.3f},{0,k*.56f,-.7f},bottom},.42f,frameWood,4,2);
 }
 rod({-.76f,0,-.08f},{.76f,0,-.08f},.55f,steel,10);
 torus({.63f,0,-.08f},{1,0,0},.64f,.10f,iron,14);
}
void hangingPrint(float t,float width,float height,float yaw,int photo,float bow,float skew){
 V point=linePoint(t);float theta=rad(yaw);V along{std::cos(theta),std::sin(theta),0},normal{std::sin(theta),-std::cos(theta),0};
 float direction=photo==1?-1.f:1.f;
 auto sheet=[&](float u,float v){
  float h=(u-.5f)*width;
  float shoulder=(u-.5f)*(u-.5f)*4.0f;
  float curl=bow*(.12f+.76f*v)*std::sin(u*PI*1.34f+.7f*v)+v*v*(1.9f*std::cos(u*4.6f+v*2.4f)+.46f*std::sin(v*7))*direction;
  float lift=photo==3?2.24f*std::pow(u,4.2f)*std::pow(v,3.8f):0.f;
  return point+along*(h+v*v*skew)+normal*(curl+lift*.88f)+V{0,0,-1.35f-height*v
   -1.22f*shoulder*(1-v)*(1-v)+lift+(.85f*v+.62f)*std::sin((u-.5f)*PI*.85f)+v*v*1.25f*std::cos(u*4.9f)};
 };
 int photoMat=mats.size();mats.push_back(mats[pics[photo]]);mats.back().ratio=width/height;mats.back().hanging=true;mats.back().rough=.27f;mats.back().mirror=.016f;
 patch(28,20,sheet,photoMat);peg(point,yaw+5,4);
 if(photo==3){
  // A last drop gathers on the low edge of the curling fibre print.
  int drop=mat({.39f,.36f,.34f},.09f,.72f,ClearWater);
  auto base=sheet(.74f,1);
  lathe(base-V{0,0,.94f},{0,0,1},{{0,.04f,drop},{.11f,.26f,drop},{.30f,.31f,drop},{.55f,.21f,drop},{.76f,.09f,drop},{.96f,.07f,drop}},16);
 }
}
void dryingNegative(float t,float length,float yaw,float phase){
 // A ribbon of processed 35 mm film, twisted about gravity. The edge holes
 // are actual gaps in the mesh, so the wall is visible through them.
 V p=linePoint(t);peg(p,yaw);
 auto filmAt=[&](float u,float v){float a=rad(yaw+78*u-44*std::sin(2.1f*PI*u+phase));float off=(v-.5f)*3.55f;
  return p+V{3.7f*std::sin(2.15f*PI*u+phase)*u+off*std::cos(a),2.65f*std::sin(2.8f*PI*u+.35f)*u+off*std::sin(a),-2-u*length};};
 for(int i=0;i<56;i++)for(auto span:std::array<std::array<float,2>,5>{{{0,.034f},{.034f,.095f},{.095f,.905f},{.905f,.966f},{.966f,1}}}){
  bool track=span[0]>.03f&&span[0]<.04f||span[0]>.90f&&span[0]<.92f;
  if(track&&i%3==1)continue;
  float a=i/56.f,b=(i+1)/56.f;
  V A=filmAt(a,span[0]),B=filmAt(b,span[0]),C=filmAt(b,span[1]),D=filmAt(a,span[1]),n=norm(cross(B-A,C-A));
  Vertex va{A,n,{a,span[0]}},vb{B,n,{b,span[0]}},vc{C,n,{b,span[1]}},vd{D,n,{a,span[1]}};
  triangle(va,vb,vc,film);triangle(va,vc,vd,film);
 }
}
void lineAndPaper(){
 std::vector<V> rope;for(int j=0;j<=70;j++)rope.push_back(linePoint(j/70.f));
 tube(rope,.21f,frameWood,7,1);
 for(const V&p:{linePoint(0),linePoint(1)})torus(p,{0,1,0},1.08f,.28f,iron,16);
 dryingNegative(.102f,36.5f,-19,.43f);
 hangingPrint(.227f,18.6f,24.5f,-12,0,1.75f,1.2f);
 peg(linePoint(.376f),-26,-7);
 hangingPrint(.744f,33.1f,28.9f,-36.5f,3,2.85f,-1.30f);
 hangingPrint(.877f,32.0f,33.9f,-44,0,3.45f,1.25f);
 dryingNegative(.628f,29.3f,-22,0);
}
const V stoolCentre{60.8f,127.25f,0};
constexpr float stoolLevel=69.8f;
void stool(){
 V p=stoolCentre,seat=p+V{0,0,stoolLevel-53.8f};
 lathe(seat,{0,0,1},{{49,16.2f,black},{50.6f,18.2f,brown},{52.2f,18.6f,frameWood},{53.3f,17.9f,wood},{53.8f,16.8f,wood},{53.78f,15.6f,wood},{53.38f,12.8f,wood},{52.98f,7.3f,wood},{52.9f,.2f,wood}},64);
 for(float a:{24.f,145.f,265.f}){float ang=rad(a);screw(seat+V{12.1f*std::cos(ang),12.1f*std::sin(ang),53.40f},{0,0,1},.50f);}
 torus(p+V{0,0,24.f},{0,0,1},16.9f,.74f,steel,48);
 for(int k=0;k<4;k++){float a=rad(26+k*90);V q{std::cos(a),std::sin(a),0};
  tube({p+q*10+V{0,0,stoolLevel-3.4f},p+q*12+V{0,0,stoolLevel-10.3f},p+q*14.6f+V{0,0,34},p+q*18.7f+V{0,0,2.2f}},1.13f,iron,12,3);
  lathe(p+q*18.7f,{0,0,1},{{0,1.4f,rubber},{2.3f,1.38f,rubber}},16);
 }
}
void makeRoom(){
 roomShell();safelight();enlarger();washBasin();wetStation();timer();lineAndPaper();stool();
 paperBox({91,180,86.5f},{39,28,5.1f},-4,black);
 paperBox({92,180,91.6f},{36.8f,27,4.6f},4.7f,card);
 archivalWasher();
}
