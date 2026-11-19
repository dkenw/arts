#pragma once
// The handles are open on the underside; the fingernail-polished lower lip
// and its shadow sit at different depths. Dimensions are in centimetres.
void cupPull(V p,int metal,int rim){
 Scope placing(translation(p));
 int under=mat({.11f,.093f,.075f},.71f,.03f,Grain);
 box({0,-.10f,0},{12.6f,.33f,3.72f},metal,.15f);
 auto shell=[](float u,float v){
  float a=PI*u,b=PI*.515f*v;
  return V{5.1f*std::cos(a),-.40f-3.15f*std::sin(a)*std::sin(b),
           -.56f+2.29f*std::sin(a)*std::cos(b)};
 };
 patch(24,8,shell,metal);
 patch(24,3,[&](float u,float v){V q=shell(u,1);return mix(q,V{q.x,-.34f,q.z+.16f+.32f*std::sin(PI*u)},v);},under);
 std::vector<V> lip;for(int i=0;i<=24;i++)lip.push_back(shell(i/24.f,1));
 tube(lip,.117f,rim,6,1);
 for(int s:{-1,1})screw({s*5.60f,-.31f,.10f},{0,-1,0},.34f);
}
void paperDrawers(){
 int woodcase=mat({.278f,.209f,.182f},.72f,.025f,Oak);
 int frameLacquer=mat({.31f,.248f,.212f},.68f,.046f,Oak);
 int field=mat({.258f,.205f,.183f},.77f,.025f,Oak);
 int ledge=mat({.39f,.291f,.208f},.55f,.054f,Oak);
 int brassOld=mat({.42f,.330f,.21f},.47f,.16f,Brushed);
 int brassRub=mat({.54f,.425f,.28f},.37f,.20f,Brushed);
 int label=mat({.51f,.473f,.40f},.88f,.002f,Paper);
 box({97,184.7f,40.4f},{82.5f,64.5f,75.7f},woodcase,.74f);
 // The drawers get deeper toward the floor.
 const std::array<float,5> edges{{12.9f,34.0f,51.4f,65.55f,77.2f}};
 for(int j=0;j<4;j++){
  float lo=edges[j]+.35f,hi=edges[j+1]-.35f,cz=(lo+hi)*.5f;
  float front=151.81f-(j==2?1.15f:0.f);
  box({97,front,cz},{78.7f,1.6f,hi-lo},frameLacquer,.39f);
  box({97,front-.84f,cz},{71.25f,.36f,hi-lo-4.15f},field,.15f);
  for(int side:{-1,1}){
   box({97,front-1.01f,cz+side*(hi-lo-3.88f)*.5f},{72.5f,.54f,.81f},ledge,.23f);
   box({97+side*35.7f,front-.99f,cz},{.79f,.52f,hi-lo-3.95f},ledge,.21f);
  }
  // Two early brass cup pulls and one replaceable index card per drawer.
  for(float x:{73.8f,120.2f})cupPull({x,front-1.25f,cz+.10f},brassOld,brassRub);
  float yr=front-1.23f,z=cz+.56f;
  frontLabel(97,yr-.08f,z,8.44f,3.25f,label);
  for(int s:{-1,1}){
   box({97,yr-.22f,z+s*1.64f},{9.70f,.48f,.47f},brassOld,.15f);
   box({97+s*4.64f,yr-.22f,z},{.48f,.48f,3.38f},brassOld,.12f);
  }
  for(int k=0;k<4;k++)if(k!=j)
   frontLabel(94.35f+k*1.29f,yr-.11f,z+.21f-.08f*(k%2),.80f,.22f,mark);
 }
 for(float x:{56.78f,137.22f})box({x,151.45f,44.7f},{1.9f,3.1f,68.4f},ledge,.36f);
 box({97,153.1f,9.7f},{82.5f,5.25f,5.5f},woodcase,.48f);
}
