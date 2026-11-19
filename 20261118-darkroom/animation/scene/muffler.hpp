#pragma once
// The 24 cm measurement follows the weave through a fold, rather than
// its foreshortened silhouette. All lengths here are in the room's cm.
struct ClothSection { V p,across; float crimp,support; };
struct Muffler{
 static constexpr float width=24.0f;
 std::vector<ClothSection> knots;
 struct Sample{V p,across;float crimp,support,arc;};
 std::vector<Sample> rows;
 float length=0;
 Muffler(){
  auto k=[&](V p,V across,float fold,float support){knots.push_back({p,across,fold,support});};
  // Short fringed end in view, U-fold over the outboard edge, then the long
  // panel comes back across the top and falls well below the picture.
  k({-15.3f,-13.5f,-9.6f},{.83f,-.55f,.11f},.48f,0);
  k({-15.0f,-13.0f,-3.7f},{.81f,-.58f,.09f},.49f,0);
  k({-14.0f,-12.3f,-.45f},{.77f,-.63f,.06f},.46f,.2f);
  k({-11.0f,-10.4f,1.06f},{.62f,-.78f,.05f},.41f,1);
  k({-4.2f,-6.7f,.64f},{.38f,-.93f,.03f},.40f,1);
  k({4.9f,-4.5f,.82f},{.20f,-.98f,.05f},.49f,1);
  k({12.8f,-3.8f,1.25f},{.06f,-1,.04f},.58f,1);
  k({16.9f,-4.3f,1.04f},{-.22f,-.98f,.06f},.68f,.55f);
  k({18.9f,-4.7f,-1.19f},{-.23f,-.97f,.05f},.76f,0);
  k({19.9f,-4.3f,-7.2f},{-.31f,-.95f,.04f},.92f,0);
  k({20.9f,-3.9f,-19.0f},{-.34f,-.94f,.03f},1.01f,0);
  k({22.1f,-2.3f,-29.4f},{-.36f,-.93f,.10f},.98f,0);
  k({22.5f,-.9f,-32.9f},{-.51f,-.86f,.12f},.92f,0);
  k({20.6f,1.1f,-34.10f},{-.67f,-.74f,.06f},.90f,0);
  k({18.9f,2.5f,-31.65f},{-.62f,-.78f,.04f},.94f,0);
  k({18.45f,4.3f,-20.2f},{-.53f,-.85f,.05f},1.07f,0);
  k({19.3f,5.4f,-9.2f},{-.51f,-.86f,.06f},.97f,0);
  k({19.0f,6.2f,-2.4f},{-.43f,-.90f,.1f},.88f,0);
  k({17.6f,6.0f,1.06f},{-.29f,-.96f,.11f},.78f,.54f);
  k({13.8f,4.4f,2.72f},{-.24f,-.97f,.08f},.68f,1);
  k({7.3f,1.2f,3.38f},{.40f,-.91f,.15f},.74f,1);
  k({3.7f,-4.0f,3.16f},{.84f,-.54f,.19f},.80f,1);
  k({2.3f,-11.5f,2.44f},{.97f,-.23f,.17f},.69f,1);
  k({1.4f,-16.8f,1.68f},{.99f,-.13f,.13f},.61f,.62f);
  k({1.2f,-19.15f,-1.52f},{.99f,-.08f,.10f},.60f,0);
  k({.45f,-20.15f,-7.8f},{.98f,-.20f,.08f},.65f,0);
  k({-1.3f,-20.7f,-17.8f},{.96f,-.29f,.05f},.76f,0);
  k({-2.3f,-21.3f,-26.3f},{.98f,-.20f,.06f},.80f,0);
  k({-2.0f,-21.1f,-29.2f},{.99f,-.11f,.06f},.74f,0);
  // The short end fell to the lit side of the seat; the long end falls
  // toward the camera. Ease the change of direction across the supported rows.
  for(size_t j=0;j<std::min<size_t>(7,knots.size());j++){
   Frame f=turn({},-58.0f*(1-step(2.1f,6.4f,float(j))));
   knots[j].p=f.dir(knots[j].p);knots[j].across=f.dir(knots[j].across);
  }
  V last{};
  for(int i=0;i+1<int(knots.size());i++){
   auto a=knots[std::max(0,i-1)],b=knots[i],c=knots[i+1],d=knots[std::min(int(knots.size())-1,i+2)];
   float span=len(c.p-b.p);V t0=norm(c.p-a.p)*span,t1=norm(d.p-b.p)*span;
   for(int j=0;j<=16;j++){
    if(i&&j==0)continue;
    float t=j/16.f,t2=t*t,t3=t*t2,e=t2*(3-2*t);
    V p=b.p*(2*t3-3*t2+1)+t0*(t3-2*t2+t)+c.p*(-2*t3+3*t2)+t1*(t3-t2);
    if(!rows.empty())length+=len(p-last);
    rows.push_back({p,norm(mix(b.across,c.across,e)),mix(b.crimp,c.crimp,e),mix(b.support,c.support,e),length});last=p;
   }
  }
 }
 V point(float u,float v)const{
  float s=sat(v)*length;
  auto it=std::lower_bound(rows.begin(),rows.end(),s,[](const Sample& a,float d){return a.arc<d;});
  size_t j=std::clamp(size_t(it-rows.begin()),size_t(1),rows.size()-1);
  const auto &a=rows[j-1],&b=rows[j];float k=(s-a.arc)/std::max(.0001f,b.arc-a.arc);
  V centre=mix(a.p,b.p,k),t=norm(b.p-a.p),w=mix(a.across,b.across,k);
  w=norm(w-t*dot(t,w));V n=norm(cross(t,w));
  float span=(u-.5f)*width,relief=mix(a.crimp,b.crimp,k),contact=mix(a.support,b.support,k);
  // Integrating a unit tangent across each row conserves its laid-flat width.
  float sideways=0,height=0;
  for(int i=0;i<22;i++){
   float d=span*(i+.5f)/22;
   float tilt=relief*(.77f*std::sin(d*.44f+.51f*std::sin(s*.054f))
     +.27f*std::sin(d*.81f-s*.063f+.9f))+.09f*std::sin(s*.09f);
   sideways+=std::cos(tilt)*span/22;height+=std::sin(tilt)*span/22;
  }
  V q=centre+w*sideways+n*height;
  float r=std::hypot(q.x,q.y);
  if(r>16.8f&&contact>0){
   const float bend=2.0f,excess=r-16.8f,theta=std::min(PI*.5f,excess/bend);
   float reach=16.8f+bend*std::sin(theta),drop=bend*(1-std::cos(theta))+std::max(0.f,excess-bend*PI*.5f);
   float factor=mix(1.f,reach/r,contact);q.x*=factor;q.y*=factor;q.z-=drop*contact;
  }
  r=std::hypot(q.x,q.y);
  if(r<18.55f&&q.z> -5.8f){
   float seat=-.89f+.90f*step(6.5f,16.7f,r);
   if(q.z<seat+.14f){
    if(contact>.38f||r<13.2f||q.z>-.75f)q.z=seat+.14f;
    else{float lift=(18.72f+.10f*std::sin(s*.5f))/std::max(.1f,r);q.x*=lift;q.y*=lift;}
   }
  }
  return q;
 }
};
void woolScarf(){
 Scope here(turn(stoolCentre+V{0,0,stoolLevel},64.0f));
 Muffler cloth;
 int woven=mat({.43f,.32f,.29f},.95f,.004f,MufflerWool);mats[woven].ratio=cloth.length;
 int seam=mat({.28f,.17f,.17f},.97f,0,Yarn);
 int dark=mat({.25f,.16f,.17f},.98f,0,Yarn),oat=mat({.73f,.58f,.44f},.97f,0,Yarn),madder=mat({.53f,.28f,.21f},.97f,0,Yarn);
 patch(43,222,[&](float u,float v){return cloth.point(u,v);},woven);
 for(float u:{.002f,.998f}){
  std::vector<V> edge;for(int j=0;j<=205;j++)edge.push_back(cloth.point(u,j/205.f));
  tube(edge,.18f,seam,6,1);
 }
 // Knotted twill fringe, mostly paired, with a few short worn tips.
 RNG seed(5507);
 for(float v:{0.f,1.f})for(int j=0;j<16;j++){
  float u=(j+.51f+.22f*(seed.next()-.5f))/16;
  V p=cloth.point(u,v),out=norm(p-cloth.point(u,v==0?.003f:.997f));
  V side=norm(cloth.point(u+.012f,v)-cloth.point(u-.012f,v));
  float reach=4.62f+seed.next()*1.84f,drift=(seed.next()-.5f)*1.65f;
  if(j==11)reach*=.70f;
  V knot=p+out*.56f,tip=knot+out*.60f+side*drift+V{0,-.18f,-reach};
  int m=(j==3||j==4||j==10||j==11)?dark:(j%4==0?madder:oat);
  tube({cloth.point(u-.019f,v),knot,cloth.point(u+.019f,v)},.165f,m,6,2);
  tube({knot,knot+out*.34f+side*(drift*.20f)+V{0,0,-reach*.35f},tip},.248f,m,7,4);
  if(j%3!=1)tube({knot+out*.39f+V{0,0,-reach*.53f},tip-side*.32f+V{.02f,-.03f,.18f},tip-side*.47f+V{0,0,-.58f}},.131f,m,6,3);
 }
 std::cerr<<"Muffler woven length "<<cloth.length<<" cm, width "<<cloth.width<<" cm before fringe\n";
}
