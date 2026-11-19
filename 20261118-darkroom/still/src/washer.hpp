#pragma once
// A plumbed archival washer. The front, two sides and rippled top bound one
// continuous refractive volume. The removable print racks are bent wire pairs.
void archivalWasher(){
 const int dripTray=mat({.36f,.38f,.35f},.42f,.24f,Brushed);
 const int trim=mat({.295f,.30f,.275f},.39f,.17f,Brushed);
 const int oldNickel=mat({.35f,.34f,.275f},.48f,.19f,Brushed);
 const int foot=mat({.08f,.075f,.077f},.84f,.009f,Grain);
 const int glass=mat({.026f,.031f,.029f},.15f,.42f,WasherGlass);
 const int fluid=mat({.025f,.031f,.033f},.098f,.55f,WaterGlass);
 tray({-96,182.75f,86.5f},79.2f,57.2f,1.11f,dripTray);
 // Stopcock fed from the horizontal supply; the return drains into the pan.
 V valve{-135.75f,150.5f,108.85f};
 rod(valve,valve+V{4.0f,0,0},1.57f,copper,12);
 lathe(valve+V{3.6f,0,0},{1,0,0},{{0,1.77f,oldNickel},{1.13f,1.88f,brass},{1.55f,1.40f,oldNickel},{3.05f,1.39f,oldNickel},{3.45f,1.77f,brass}},12);
 rod(valve+V{5.5f,0,0},valve+V{5.5f,0,3.6f},.72f,oldNickel,10);
 rod(valve+V{5.5f,-2.6f,3.65f},valve+V{5.5f,2.6f,3.65f},.55f,redEnamel,10);
 V feed=washerPose.pos({-22.30f,7.05f,32.7f});
 tube({valve+V{7.0f,0,0},{-126,151,107.1f},{-119,153.5f,98.3f},{-115,158,96.6f},
       {-111.5f,164.f,99.5f},feed+V{-1.10f,-2.9f,-2.1f},feed},.78f,rubber,12,6);
 Scope local(washerPose);
 constexpr float X=23.8f,Y=10.50f,base=2.45f,top=32.55f,level=washerLevel;
 for(int a:{-1,1})for(int b:{-1,1}){
  lathe({a*(X-2.2f),b*(Y-1.75f),0},{0,0,1},{{0,1.08f,foot},{.44f,1.38f,foot},{1.50f,1.27f,foot}},14);
 }
 box({0,0,1.78f},{2*X+1.6f,2*Y+1.5f,1.17f},trim,.40f);
 box({0,0,2.39f},{2*X-.23f,2*Y-.20f,.45f},glazed,.16f);
 for(int a:{-1,1})for(int b:{-1,1}){
  float x=a*X,y=b*Y;
  box({x+.04f*a,y-.92f*b,(top+base)*.5f},{.49f,2.1f,top-base},oldNickel,.16f);
  box({x-1.05f*a,y+.03f*b,(top+base)*.5f},{2.25f,.48f,top-base},oldNickel,.15f);
  for(float z:{4.25f,29.50f})
   lathe({x-.75f*a,y+.25f*b,z},{0,float(b),0},{{0,.32f,iron},{.15f,.29f,trim}},10);
 }
 // The very thin dry lips are visible above the slightly lower waterline.
 for(int a:{-1,1}){
  quad({a*X,-Y,base},{a*X,Y,base},{a*X,Y,level},{a*X,-Y,level},glass);
  quad({-X,a*Y,base},{X,a*Y,base},{X,a*Y,level},{-X,a*Y,level},glass);
  box({a*X,0,top-.13f},{.76f,2*Y+.65f,.63f},trim,.23f);
  box({0,a*Y,top-.13f},{2*X+.72f,.74f,.63f},trim,.23f);
  rod({-X+.5f,a*Y,level},{X-.5f,a*Y,level},.102f,glint,7);
 }
 patch(77,41,[&](float u,float v){
  float x=mix(-X,X,u),y=mix(-Y,Y,v);
  return V{x,y,level+washerWave(x,y)*step(0,1.1f,std::min(X-std::abs(x),Y-std::abs(y)))};
 },fluid);
 // Polished wire protects each print on both sides. The higher thumb grips
 // are scalloped and offset. The submerged rack can be seen through the tank.
 int wire=mat({.275f,.31f,.305f},.36f,.17f,Brushed);
 for(int i=0;i<5;i++){
  float y=-7.6f+3.80f*i,cz=top+.77f+.15f*(i%2);
  for(int a:{-1,1}){
   float x=a*20.1f;
   tube({{x-1.10f*a,y,3.3f},{x,y,5.2f},{x,y,cz-1.8f},{x-1.25f*a,y,cz+.15f},
    {x-4.35f*a,y,cz+.46f},{x-5.7f*a,y,cz-.75f},{x-5.95f*a,y,cz-3.45f}},.295f,wire,8,4);
  }
  std::vector<V> keeper;
  for(int k=0;k<=32;k++){
   float x=-18.0f+36*k/32.f;
   float arch=std::sqrt(std::max(0.f,1-x*x/35.6f));
   keeper.push_back({x,y,cz-1.24f-2.91f*arch});
  }
  tube(keeper,.252f,wire,8,1);
  // Finely spaced wire bails give a sheet room to swell in the rinse water.
  for(int side:{-1,1}){
   float x=side*12.0f;
   tube({{x-4.15f,y,cz-1.19f},{x-3.55f,y,25.4f},{x-2.f,y,6.4f},
        {x,y,4.41f},{x+2.f,y,6.4f},{x+3.56f,y,25.4f},{x+4.15f,y,cz-1.19f}},.215f,wire,7,4);
  }
 }
 // One thin smoked divider is lifted by a finger recess. The lips carry
 // actual milled perforations. The open wire compartments remain visible.
 int divider=mat({.236f,.285f,.265f},.46f,.12f,Paint);
 int edge=mat({.342f,.391f,.356f},.37f,.16f,Paint);
 constexpr float by=5.82f;
 auto finger=[](float x){float dx=std::abs(x-2.15f);
  return 31.67f-4.16f*(1-step(2.0f,7.23f,dx))-.58f*step(18.65f,21.05f,std::abs(x));};
 for(int i=0;i<64;i++){
  float x0=mix(-21.15f,21.15f,i/64.f),x1=mix(-21.15f,21.15f,(i+1)/64.f);
  float z0=finger(x0),z1=finger(x1);
  quad({x0,by,24.8f},{x1,by,24.8f},{x1,by,z1},{x0,by,z0},divider);
  quad({x0,by,z0},{x1,by,z1},{x1,by+.28f,z1},{x0,by+.28f,z0},edge);
 }
 constexpr int perforations=12;constexpr float pitch=42.3f/perforations;
 for(int i=0;i<perforations;i++){
  float x=-21.15f+pitch*i;
  box({x+.56f,by+.12f,15.1f},{1.12f,.28f,19.4f},divider);
  box({x+(pitch+1.12f)*.5f,by+.12f,22.7f},{pitch-1.12f,.28f,4.22f},divider);
  box({x+(pitch+1.12f)*.5f,by+.12f,7.8f},{pitch-1.12f,.28f,4.8f},divider);
 }
 // Water enters through a diffusing manifold near the floor of the tank.
 tube({{-22.3f,7.05f,32.7f},{-22.3f,7.2f,34.18f},{-21,7.2f,35.05f},
    {-19.2f,7.1f,34.0f},{-19.1f,7.1f,28.0f},{-19.0f,7.1f,7.3f},{-17.1f,7.1f,5.2f},
    {13.4f,7.1f,5.0f}},.69f,trim,9,4);
 for(float z:{12.f,23.f})rod({-19,7.1f,z},{-19,7.1f,z+.41f},.85f,foot,9);
 // Short standpipe carries the overflow safely down to the drain tray.
 float xp=X+1.35f;
 tube({{X-1.55f,5.1f,level-1.75f},{X+.9f,5.1f,level-1.75f},{xp+1.5f,5.1f,level-3.35f},
      {xp+1.6f,5.0f,8.0f},{xp+2.15f,3.95f,5.7f},{xp+5.1f,2.20f,3.3f}},.63f,oldNickel,10,4);
 torus({X+.05f,5.1f,level-1.75f},{1,0,0},1.14f,.25f,trim,14);
}
