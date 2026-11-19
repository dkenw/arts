#pragma once
// Sparse airborne flecks and broad, weak in-scatter. Both lights, the camera,
// and the surface-depth test use the same centimetre space as the room.
void airInTheLight(std::vector<float>& rgb,const std::vector<float>& depth,
                   int w,int h,V eye,V forward,V right,V up,float focal){
 const V axis=norm(safeDirection*.78f-safeVertical*.61f-safeHorizontal*.08f);
 const V wide=norm(cross(V{0,0,1},axis)),thin=norm(cross(axis,wide));
 V centre=safeOrigin+axis*73.f;
 for(int y=0;y<h;y++)for(int x=0;x<w;x++){
  const int i=y*w+x;
  V ray=norm(forward+right*((x+.5f-w*.5f)/focal)+up*((h*.5f-y-.5f)/focal));
  V toward=centre-eye; float t=dot(toward,ray);
  float det=82.f*82.f-dot(toward,toward)+t*t;
  if(det<=0)continue;
  float near=std::max(.1f,t-std::sqrt(det)),far=std::min(depth[i],t+std::sqrt(det));
  if(far<=near)continue;
  float accum=0;
  for(int j=0;j<14;j++){
   V p=eye+ray*mix(near,far,(j+.5f)/14),d=p-safeOrigin;
   float along=dot(d,axis);
   if(along<3||along>152)continue;
   float a=dot(d,wide)/(9.4f+along*.245f),b=dot(d,thin)/(5.5f+along*.151f);
   float r2=a*a+b*b;if(r2>3.6f)continue;
   float field=std::exp(-1.9f*r2)*step(3,12,along)*(1-step(91,150,along));
   if(field<.02f||blocked(p,safeOrigin))continue;
   // The penumbra broadens with distance from the comparatively wide glass.
   float vane=.86f+.14f*std::cos(4.7f*b+.57f*a)*std::exp(-along*.008f);
   float haze=.72f+.33f*noise(p.x*.030f+p.z*.014f,p.y*.028f,229);
   accum+=field*vane*haze/(1+.00035f*along*along);
  }
  float light=accum*(far-near)/14*.0047f;
  rgb[i*3]+=light;rgb[i*3+1]+=light*.118f;rgb[i*3+2]+=light*.048f;
 }
 auto fleck=[&](V pos,float power,V tint,float width){
  V rel=pos-eye;float t=dot(rel,forward);if(t<=0)return;
  float sx=w*.5f+focal*dot(rel,right)/t-.5f,sy=h*.5f-focal*dot(rel,up)/t-.5f;
  float radius=std::max(.31f,(width+.09f*std::abs(t-218)/150)*w/528.f);
  int reach=std::ceil(2.8f*radius);
  for(int j=std::max(0,int(sy)-reach);j<=std::min(h-1,int(sy)+reach);j++)
   for(int i=std::max(0,int(sx)-reach);i<=std::min(w-1,int(sx)+reach);i++){
    int k=j*w+i;if(depth[k]+.02f<len(rel))continue;
    float dx=i-sx,dy=j-sy,amount=power*std::exp(-.5f*(dx*dx+dy*dy)/(radius*radius));
    for(int c=0;c<3;c++)rgb[k*3+c]+=amount*tint[c];
   }
 };
 RNG seed(1964);
 for(int i=0;i<116;i++){
  float t=std::cbrt(.005f+.985f*seed.next()),hgt=lensPos.z-paperLevel;
  float u=seed.next()-.5f,v=seed.next()-.5f,aperture=.29f+.13f*seed.next();
  V p=lensPos+projX*(u*projWidth*t)+projY*(v*projDepth*t)-V{0,0,hgt*t};
  float light=lightInAir(p);
  if(light<.35f||blocked(p,lensPos-V{0,0,.21f}))continue;
  float brightness=.017f+.19f*std::pow(seed.next(),3.f);
  fleck(p,light*brightness/(.50f+t*t),{.78f,1.0f,.91f},aperture);
 }
 for(int i=0;i<90;i++){
  float t=10+98*seed.next(),x=(seed.next()-.5f)*1.66f,y=(seed.next()-.5f)*1.62f;
  V p=safeOrigin+axis*t+wide*(x*(9.4f+t*.245f))+thin*(y*(5.5f+t*.151f));
  float val=.035f+.18f*std::pow(seed.next(),4.f);
  if(blocked(p,safeOrigin))continue;
  fleck(p,val*std::exp(-.92f*(x*x+y*y))/(1+.0004f*t*t),{1,.19f,.10f},.25f+.11f*seed.next());
 }
}
