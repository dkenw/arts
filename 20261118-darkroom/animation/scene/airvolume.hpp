#pragma once

// Integrate moving dust density through the physical projection cone. Each
// pixel stores spatial integrals of three currents. Only their phase changes
// between exposures, so the lens aperture and the negative can be sampled once.
struct IlluminatedAir {
 struct Integral{std::array<float,3> sine{},cosine{};};
 std::map<uint32_t,Integral> pixels;
 void prepare(){
  int x0=width,y0=height,x1=0,y1=0;
  for(int layer:{0,1})for(int u:{-1,1})for(int v:{-1,1}){
   V at=lensPos+projX*(u*(layer?projWidth*.5f:lensRadius))
               +projY*(v*(layer?projDepth*.5f:lensRadius));
   if(layer)at.z=paperLevel;
   auto q=project(at);
   x0=std::min(x0,int(std::floor(q.x))-2);y0=std::min(y0,int(std::floor(q.y))-2);
   x1=std::max(x1,int(std::ceil(q.x))+2);y1=std::max(y1,int(std::ceil(q.y))+2);
  }
  float heightCm=lensPos.z-paperLevel;
  constexpr int steps=20,side=3;
  for(int y=std::max(0,y0);y<=std::min(height-1,y1);y++)
   for(int x=std::max(0,x0);x<=std::min(width-1,x1);x++){
    Integral m;float total=0;
    for(int j=0;j<side*side;j++){
     float xx=x+(j%side+.5f)/side,yy=y+(j/side+.5f)/side;
     V d=norm(forward+right*((xx-width*.5f)/focalLength)+up*((height*.5f-yy)/focalLength));
     float angle=2.39996323f*j,r=lensOpening*std::sqrt((j+.5f)/(side*side));
     V lens=eye+right*(r*std::cos(angle))+up*(r*std::sin(angle));
     Ray ray(lens,norm(eye+d*(focusDistance/dot(d,forward))-lens));
     Hit h;trace(ray,h);float lo=.02f,hi=h.t;
     if(!clipToBeam(ray,lo,hi))continue;
     for(int k=0;k<steps;k++){
      V p=ray.o+ray.d*mix(lo,hi,(k+.5f)/steps);
      float depth=lensPos.z-p.z,t=depth/heightCm;
      float projection=lightInAir(p);
      if(projection<.001f)continue;
      V target=lensPos-V{0,0,.21f};
      if(blocked(p,target))continue;
      float a=dot(p-lensPos,projX),b=dot(p-lensPos,projY);
      float rho=.45f+.63f*noise(p.x*.095f+p.z*.040f,p.y*.082f-p.z*.025f,92);
      float envelope=step(.025f,.17f,t)*(1-.61f*step(.90f,1.f,t));
      float light=(hi-lo)*.0073f/(steps*side*side)*projection*rho*(.77f+.87f*(1-t))*envelope;
      // Curved layers with different orientations break up the density field
      // across the negative. Their motion never changes the bulb's intensity.
      std::array<float,3> phase={{
       .171f*a+.138f*depth+.055f*b+.93f*std::sin(.113f*depth-.074f*b),
       -.164f*a+.263f*depth-.041f*b+.74f*std::sin(.128f*a+.053f*depth+.81f),
       .244f*a-.273f*depth+.077f*b+.61f*std::sin(.163f*depth-.096f*a)
      }};
      for(int n=0;n<3;n++){m.sine[n]+=light*std::sin(phase[n]);m.cosine[n]+=light*std::cos(phase[n]);}
      total+=light;
     }
    }
    if(total>.00012f)pixels[uint32_t(y*width+x)]=m;
   }
 }
 void expose(LightPlate& plate,float cycle)const{
  float wave=2*PI*cycle,air=draft::pressure(cycle*draft::seconds-.34f);
  std::array<float,3> phase{{wave+.29f*std::sin(wave-.31f)+.27f*air,
                             2*wave-.27f*std::sin(wave+1.1f)+.12f*air,
                             -wave+.52f*std::sin(wave+.65f)-.21f*air}};
  const std::array<float,3> strength{{.53f,.31f,.14f}};
  std::array<float,3> c{},s{};
  for(int j=0;j<3;j++){c[j]=strength[j]*std::cos(phase[j]);s[j]=strength[j]*std::sin(phase[j]);}
  for(auto const& [id,m]:pixels){
   float delta=0;for(int j=0;j<3;j++)delta+=m.sine[j]*c[j]-m.cosine[j]*s[j];
   plate[id]+=V{.78f,.88f,.82f}*delta;
  }
 }
} illuminatedAir;
