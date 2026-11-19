#pragma once
void dryingScreens(){
 // Dovetailed shallow drying screens run in a low open cabinet. Only one
 // screen is pulled forward. The handhold is cut out of the front rail.
 int oak=mat({.42f,.28f,.21f},.67f,.040f,Oak),edge=mat({.42f,.32f,.23f},.57f,.048f,Oak);
 int screenMesh=mat({.19f,.225f,.226f},.82f,.012f,Mesh);
 const float left=-46.5f,right=36.0f,back=210.f;
 box({left,178.5f,50},{3.6f,63.f,66.f},oak,.39f);
 box({right,178.5f,50},{3.6f,63.f,66.f},oak,.39f);
 box({(left+right)*.5f,back,49},{right-left,2.7f,66.f},brown,.36f);
 for(int j=0;j<5;j++){
  float z=25.f+j*10.3f,front=150.0f-((j==3)?9.7f:((j==1)?2.1f:0.f));
  for(float x:{left+2.0f,right-2.0f})box({x,179.2f,z-1.08f},{1.9f,56,1.68f},wood,.26f);
  float mid=(left+right)/2,w=right-left-4.55f;
  for(int k=0;k<36;k++){
   float u0=k/36.f,u1=(k+1)/36.f;
   auto notch=[&](float u){float x=(u-.5f)*w/6.25f;return 2.38f*std::sqrt(std::max(0.f,1-x*x));};
   float x0=mid+(u0-.5f)*w,x1=mid+(u1-.5f)*w,a=z+3.63f-notch(u0),b=z+3.63f-notch(u1);
   quad({x0,front,z},{x1,front,z},{x1,front,b},{x0,front,a},oak);
   quad({x0,front,a},{x1,front,b},{x1,front+2.59f,b},{x0,front+2.59f,a},edge);
  }
  for(float x:{mid-w/2+1.2f,mid+w/2-1.2f})box({x,front+26.75f,z+1.5f},{2.4f,53.5f,3.0f},oak,.28f);
  quad({mid-w/2+2.4f,front+2.55f,z+1.5f},{mid+w/2-2.4f,front+2.55f,z+1.5f},
       {mid+w/2-2.4f,front+52.6f,z+1.5f},{mid-w/2+2.4f,front+52.6f,z+1.5f},screenMesh);
  for(float x:{mid-w/2+3.5f,mid+w/2-3.5f})screw({x,front-.045f,z+1.60f},{0,-1,0},.36f);
 }
}
