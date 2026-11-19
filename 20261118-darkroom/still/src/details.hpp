#pragma once
void vent(){
 // Twin staggered louvres form a light trap in the wet wall.
 V c{-138.1f,90,196};box(c,{2.25f,29,18},iron,.9f);
 box(c+V{1.2f,0,0},{.52f,26.8f,15.7f},ventDark,.43f);
 for(int j=0;j<7;j++){
  float z=189.8f+j*1.99f;quad({-136.3f,77.4f,z},{-135.25f,77.4f,z+1.1f},{-135.25f,102.6f,z+1.1f},{-136.3f,102.6f,z},grey);
 }
 for(float y:{76.7f,103.2f})for(float z:{188.4f,203.5f})screw({-136.9f,y,z},{1,0,0},.43f);
}
void contacts(){
 Scope shift(translation({3,0,-6.8f}));
 int contact=mat({.94f,.89f,.78f},.74f,.025f,FullImage,10);
 // A contact sheet and two test strips are held with yellowing masking tape.
 auto proof=[](float u,float v){return V{52.0f+u*29.2f+v*.88f,216.60f-.35f*u-.59f*u*u*v*v,
                               150.5f-v*22.4f-u*1.05f+.37f*u*u*v*v};};
 patch(11,9,proof,contact);
 for(float x:{54.1f,76.0f}){
  quad({x,216.00f,151.2f},{x+4.6f,216.0f,151.6f},{x+4.9f,215.97f,148.75f},{x+.35f,215.97f,148.25f},card);
 }
 for(int i=0;i<2;i++){
  float x=82+i*2.1f,z=146.8f-i*9;
  patch(24,3,[=](float u,float v){return V{x+u*(14.3f-i*1.2f)-.55f*v,216.65f-.56f*u*u,z-v*4.5f+u*(1.2f-i*.5f)};},sheets[1]);
  quad({x+4,216.1f,z+1.1f},{x+7.3f,216.1f,z+1.3f},{x+7.35f,216.0f,z-.75f},{x+4.3f,216.0f,z-.9f},card);
 }
}
void focuser(){
 Scope local(turn({-31.55f,164.25f,86.5f},-19));
 pressed({},{{0,10,12,2.3f,black},{.65f,10.9f,12.8f,2.3f,black},{1.57f,9.6f,11.1f,2.0f,grey}},true,true);
 tube({{-2.5f,2.1f,1.2f},{-3.4f,1.6f,4.4f},{-3.4f,.2f,8.7f},{-1.5f,-1.6f,12.4f},{.7f,-1.9f,13.6f}},1.16f,grey,13,4);
 V a=norm(V{.10f,-.50f,.86f}),p{.2f,.4f,7.7f};
 lathe(p,a,{{0,1.9f,black},{1.1f,2.45f,steel},{2.3f,2.65f,black},{3.3f,2.38f,steel},
 {9.7f,2.34f,polished},{10.2f,2.69f,black},{12.2f,2.67f,black},{13,3.05f,rubber},{13.8f,3.1f,rubber}},32);
 diskUV(p+a*13.82f,{1,0,0},norm(cross(a,{1,0,0})),2.0f,black,26);
 quad({-3.2f,-3.7f,1.65f},{3.2f,-3.7f,1.65f},{3.2f,.6f,4.82f},{-3.2f,.6f,4.82f},polished);
 knob({-3.45f,0,9},{-1,0,0},1.1f,1.25f,black,12);
}
void accordion(){
 V o{-116.3f,104.8f,88.2f};std::vector<Ring> rings={{0,6.6f,black},{1.2f,7.25f,charcoal},{2,7.1f,rubber}};
 for(int j=0;j<=14;j++)rings.push_back({2.35f+j*.92f,j%2?7.3f:5.8f,j%2?rubber:charcoal});
 rings.push_back({16.1f,6.8f,charcoal});rings.push_back({18,4.0f,rubber});rings.push_back({19.8f,2.9f,black});
 lathe(o,{0,0,1},rings,36);knob(o+V{0,0,19.8f},{0,0,1},3.05f,2.9f,redEnamel,22);
}
void hardware(){
 // The timer has a switching foot and the column carriage has a real power lead.
 {Scope s(turn({57,174.8f,86.5f},-18));
  box({-5.5f,-5.7f,3.25f},{5.9f,2.35f,.68f},cream,.38f);
  box({2.1f,-5.5f,3.16f},{3.2f,2.16f,.55f},black,.25f);
  auto pilot=mat({.52f,.15f,.05f},.27f,.08f,Plain,0,{.45f,.057f,.017f});
  oval({5.6f,-5.5f,3.34f},{.55f,.43f,.29f},pilot,12,6);
 }
 // Lint, an old squeegee and a few red-lit nicks on the wash station.
 {Scope s(turn({-112.8f,140.2f,99.55f},-6));
  tube({{0,0,0},{2,0,.44f},{12,0,2.1f},{17,0,2.4f}},.72f,grey,9,4);
  box({.3f,-.1f,.12f},{2,8.9f,.77f},rubber,.23f);
 }
 // Isolated chipped-glaze marks in three wall tiles. The hairline follows
 // the wall's own surface; it never runs across the pipes in front.
 for(auto points:std::vector<std::vector<V>>{
  {{-138.79f,108,128.9f},{-138.79f,110.2f,127.6f},{-138.79f,111.6f,125.5f},{-138.79f,114.1f,124.7f}},
  {{-138.79f,111.6f,125.5f},{-138.79f,111.1f,122.6f},{-138.79f,111.9f,121}},
  {{-138.79f,59.1f,126.7f},{-138.79f,61.5f,123.5f},{-138.79f,60.8f,121.1f},{-138.79f,62.3f,118.2f}}
 })tube(points,.077f,oxide,5,1);
 // A faint film of tarnish along old soldered pipe collars.
 for(float y:{72.f,118.f,161.f})torus({-135.9f,y,101.96f},{0,1,0},1.19f,.14f,oxide,14);
 // Small metal tang at the right end of the carrier, with a strip of developed film.
 {Scope s(turn({12,161,86.5f},-16));
  patch(17,2,[](float u,float v){return V{11.5f+u*11.3f,-3.1f+v*3.5f-.64f*u,
    73.96f-2.03f*u*u+.23f*std::sin(u*4.8f)+v*.12f};},film);
  for(int j=0;j<2;j++)screw({13.6f,31.6f,82.3f+j*.86f},{1,0,0},.35f);
 }
}
void printTongs(){
 // The bowed, spring-steel arms have bamboo grips. The two lips of the basin
 // support the tongs at the tips and the heel, spanning its near corner.
 Scope local(turn({.7f,11.55f,89.84f},55.1f));
 int bamboo=mat({.65f,.43f,.21f},.52f,.032f,Wood);
 int stained=mat({.20f,.054f,.035f},.74f,.016f,Grain);
 for(int side:{-1,1}){
  auto centre=[=](float u){
   float s=std::sin(PI*u),y=side*(.23f+1.43f*(1-u)+.62f*s);
   return V{u*30.8f,y,.28f+.74f*s+.21f*u};
  };
  tube({centre(0),centre(.22f),centre(.58f),centre(.83f),centre(1)},.30f,steel,8,5);
  // One continuous tapered cross-section for each flat wooden arm.
  std::vector<V> prev;
  for(int j=0;j<=28;j++){
   float u=.075f+.81f*j/28.f;V c=centre(u);
   float a=std::pow(std::max(0.f,std::sin(PI*j/28.f)),.43f);
   float wd=.27f+.33f*a,hh=.24f+.16f*a;
   std::vector<V> row;
   for(int k=0;k<8;k++){float t=k*PI*.25f;row.push_back(c+V{0,wd*std::cos(t),hh*std::sin(t)});}
   if(j)for(int k=0;k<8;k++)quad(prev[k],prev[(k+1)%8],row[(k+1)%8],row[k],bamboo);
   prev=std::move(row);
  }
  V tip=centre(.038f);
  box(tip,{2.60f,1.18f,.75f},stained,.26f);
  for(int k=0;k<4;k++)rod(tip+V{-.82f+.48f*k,-.43f,.343f},tip+V{-.82f+.48f*k,.43f,.343f},.070f,stained,5);
  for(float u:{.25f,.72f}){V c=centre(u);lathe(c+V{0,0,.33f},{0,0,1},{{0,.19f,brass},{.12f,.16f,brass}},10);}
 }
 tube({{27.76f,-.78f,.61f},{30.08f,-.77f,.60f},{31.16f,-.39f,.52f},{31.35f,0,.49f},{31.16f,.39f,.52f},{30.08f,.77f,.60f},{27.76f,.78f,.61f}},.29f,polished,9,4);
}
void rimDrops(){
 int waterSkin=mat({.34f,.36f,.37f},.075f,.71f,ClearWater);
 RNG rand(6184);
 for(int i=0;i<36;i++){
  float s=rand.next(),r=.075f+.36f*std::pow(rand.next(),2.f);
  V p;
  if(i<17)p={-69.f+64.f*s,78.95f-.52f*rand.next(),89.63f};
  else if(i<27)p={-59.f+64.f*s,13.15f+.63f*rand.next(),89.63f};
  else p={18.15f+.52f*rand.next(),39+25*s,89.63f};
  oval(p,{r*(1+.35f*rand.next()),r,.60f*r},waterSkin,10,5);
 }
}
void details(){
 blackoutDrape();vent();contacts();focuser();dryingScreens();accordion();hardware();printTongs();rimDrops();
 int brand=mat({.92f,.87f,.72f},.79f,.015f,FullImage,11);
 {Scope s(turn({92,180,96.2f},4.7f));quad({-17,12.6f,.025f},{17,12.6f,.025f},{17,-12.6f,.025f},{-17,-12.6f,.025f},brand);}
 // A strip curls across the dry bench, then over the edge. The four exposure
 // steps continue over the bend without changing the camera in the picture.
 int strip=mat({.96f,.91f,.80f},.63f,.026f,FullImage,13);
 patch(8,52,[](float u,float v){
  float s=v*32.0f,across=(u-.5f)*7.2f;
  float x=43.7f-.23f*s+across;
  float y=161.8f-s-.18f*across,z=86.79f+.10f*std::sin(.43f*s)+.10f*u;
  constexpr float bend=15.4f,r=2.50f;
  if(s>bend){
   float angle=std::min(PI*.5f,(s-bend)/r);
   float drop=std::max(0.f,s-bend-r*PI*.5f);
   y=146.40f-r*std::sin(angle)-(.18f+.24f*std::sin(angle))*across-.48f*std::sin(drop*.26f);
   z=86.85f-r*(1-std::cos(angle))-drop+.10f*u+.29f*u*drop/12.7f;
  }
  return V{x,y,z};},strip);
 // Pencil, drying clips and a loupe. They all sit on the countertop.
 {Scope s(turn({-29.5f,154.7f,86.82f},-11));lathe({0,0,.01f},{1,0,0},{{0,.32f,redEnamel},{13.1f,.32f,redEnamel},{14.5f,.14f,frameWood},{14.8f,.02f,black}},6);}
 lathe({-37.7f,175.1f,86.51f},{0,0,1},{{0,2.4f,black},{1.0f,2.55f,black},{1.5f,2.4f,steel},{3.8f,1.9f,black},{4.1f,2.0f,steel}},26);
 // Air entrained by the jet collects just downstream. Each cap meets the
 // displaced water surface and can pick up a small crescent from the lamp.
 int bubbleFilm=mat({.08f,.07f,.07f},.07f,.02f,BubbleFilm);
 for(V bubble:std::array<V,5>{{{1.16f,-.58f,.32f},{1.60f,-.74f,.19f},{2.93f,-.78f,.35f},
                               {3.39f,-.62f,.18f},{4.55f,-.23f,.14f}}}){
  patch(20,7,[&](float u,float v){
   float a=2*PI*u,t=v*1.29f,r=bubble.z*std::sin(t);
   float x=rippleOrigin.x+bubble.x+r*std::cos(a),y=rippleOrigin.y+bubble.y+r*std::sin(a);
   return V{x,y,rinse::height(x,y)-.018f+bubble.z*(std::cos(t)-std::cos(1.29f))};
  },bubbleFilm);
 }
}
