#pragma once

// Trace the red light that enters the rinse. Subtract the corresponding flat
// water illumination already present in the direct-light pass, so a bright
// thread of focused light takes its energy from the darker water beside it.
struct BasinLight {
 static constexpr float left=-123.f,front=16.5f,pitch=.48f;
 static constexpr int cols=291,rows=124;
 std::vector<float> difference=std::vector<float>(cols*rows);

 void deposit(V target,float flux){
  float x=(target.x-left)/pitch,y=(target.y-front)/pitch;
  int i=std::floor(x),j=std::floor(y);
  if(i<0||j<0||i>=cols-1||j>=rows-1)return;
  float u=x-i,v=y-j;
  difference[j*cols+i]+=flux*(1-u)*(1-v);
  difference[j*cols+i+1]+=flux*u*(1-v);
  difference[(j+1)*cols+i]+=flux*(1-u)*v;
  difference[(j+1)*cols+i+1]+=flux*u*v;
 }
 void refractIntoBasin(V point,V incoming,V normal,float flux){
  constexpr float eta=1.f/1.333f;
  float c=-dot(incoming,normal);
  if(c<=0)return;
  V direction=norm(eta*incoming+(eta*c-std::sqrt(1-eta*eta*(1-c*c)))*normal);
  V start=point+direction*.054f;Hit hit;hit.t=29.f;
  if(!trace(Ray(start,direction),hit))return;
  V target=start+direction*hit.t;
  if(target.z>81.8f||mats[tris[hit.id].mat].kind!=Brushed)return;
  float fresnel=.0204f+.9796f*std::pow(1-c,5.f);
  deposit(target,flux*c*(1-fresnel)/normal.z);
 }
 void bake(){
  constexpr float ds=.37f;constexpr int samples=12;
  const Lamp &lamp=lights[1];
  for(float y=17.86f;y<74.12f;y+=ds)for(float x=-121.44f;x<14.42f;x+=ds){
   // An inset rounded boundary excludes the raised, dry lip.
   float qx=std::max(0.f,std::abs(x+53.5f)-62.72f);
   float qy=std::max(0.f,std::abs(y-46.f)-22.9f);
   if(qx*qx+qy*qy>5.2f*5.2f)continue;
   float h=rinse::height(x,y),e=.045f;
   V surfacePoint{x,y,h};
   float sx=(rinse::height(x+e,y)-rinse::height(x-e,y))/(2*e);
   float sy=(rinse::height(x,y+e)-rinse::height(x,y-e))/(2*e);
   V normal=norm(V{-sx,-sy,1});
   RNG seed(hash32(int((x-left)*100.f)*1709u+int((y-front)*100.f)*3923u));
   for(int s=0;s<samples;s++){
    float u=(s%4+seed.next())/4.f,v=(s/4+seed.next())/3.f;
    V to=lamp.p+lamp.rx*(2*u-1)+lamp.ry*(2*v-1)-surfacePoint;
    float d2=dot(to,to);V l=to/std::sqrt(d2);
    if(l.z<=0)continue;
    float outgoing=std::max(0.f,dot(lamp.n,-l));
    if(outgoing==0)continue;
    float visible=transmission(surfacePoint+normal*.055f,surfacePoint+to).x;
    if(visible<.001f)continue;
    float flux=lamp.power*outgoing*safeDistribution(l)*visible/(d2+90.f)
              *(ds*ds/(pitch*pitch*samples));
    refractIntoBasin(surfacePoint,-l,normal,flux);
    refractIntoBasin(surfacePoint,-l,{0,0,1},-flux);
   }
  }
  // One sub-centimetre reconstruction filter, narrower than the projected
  // luminous aperture across the depth of the bath.
  std::vector<float> filtered=difference;
  for(int j=1;j<rows-1;j++)for(int i=1;i<cols-1;i++){
   int k=j*cols+i;
   filtered[k]=(4*difference[k]+2*(difference[k-1]+difference[k+1]+difference[k-cols]+difference[k+cols])+
                difference[k-cols-1]+difference[k-cols+1]+difference[k+cols-1]+difference[k+cols+1])/16.f;
  }
  difference.swap(filtered);
 }
 float lookup(V p)const{
  float x=(p.x-left)/pitch,y=(p.y-front)/pitch;
  int i=std::floor(x),j=std::floor(y);
  if(i<0||j<0||i>=cols-1||j>=rows-1)return 0;
  int k=j*cols+i;
  return mix(mix(difference[k],difference[k+1],x-i),mix(difference[k+cols],difference[k+cols+1],x-i),y-j);
 }
} basinLight;
