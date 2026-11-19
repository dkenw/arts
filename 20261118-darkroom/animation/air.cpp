#include "scene/draw.cpp"
#include "scene/camera.hpp"
#include "scene/draft.hpp"
#include <map>
#include <stdexcept>

// All paths and luminous apertures use the room's centimetre coordinates.
using LightPlate=std::map<uint32_t,V>;
std::vector<float> firstSurface;
V lampAxis,lampAcross,lampThin;

void writeLightPlate(std::ofstream& out,const LightPlate& values){
 uint32_t count=values.size();out.write(reinterpret_cast<const char*>(&count),sizeof(count));
 for(const auto& [index,value]:values){
  out.write(reinterpret_cast<const char*>(&index),sizeof(index));
  out.write(reinterpret_cast<const char*>(&value),sizeof(value));
 }
}

struct Projected{float x,y,axial,range;};
Projected project(V p){
 V d=p-eye;float z=dot(d,forward);
 return {width*.5f+focalLength*dot(d,right)/z-.5f,
         height*.5f-focalLength*dot(d,up)/z-.5f,z,len(d)};
}

#include "scene/airvolume.hpp"

// Recover the sparse dust points in the still so the animation can replace
// them with moving dust. The smooth shaft and lamp haze are in the base plate.
void depositStillGrain(LightPlate& plate,V p,float light,V tint,float brush){
 Projected q=project(p);if(q.axial<=0)return;
 float radius=std::max(.31f,brush+.09f*std::abs(q.axial-218)/150);
 int reach=std::ceil(2.8f*radius);
 for(int y=std::max(0,int(q.y)-reach);y<=std::min(height-1,int(q.y)+reach);y++)
  for(int x=std::max(0,int(q.x)-reach);x<=std::min(width-1,int(q.x)+reach);x++){
   int k=y*width+x;if(firstSurface[k]+.02f<q.range)continue;
   float dx=x-q.x,dy=y-q.y,amount=light*std::exp(-.5f*(dx*dx+dy*dy)/(radius*radius));
   plate[k]+=tint*amount;
  }
}
LightPlate recoverStillGrains(){
 LightPlate plate;RNG seed(1964);
 for(int i=0;i<116;i++){
  float t=std::cbrt(.005f+.985f*seed.next()),hgt=lensPos.z-paperLevel;
  float u=seed.next()-.5f,v=seed.next()-.5f,aperture=.29f+.13f*seed.next();
  V p=lensPos+projX*(u*projWidth*t)+projY*(v*projDepth*t)-V{0,0,hgt*t};
  float light=lightInAir(p);
  if(light<.35f||blocked(p,lensPos-V{0,0,.21f}))continue;
  float brightness=.017f+.19f*std::pow(seed.next(),3.f);
  depositStillGrain(plate,p,light*brightness/(.50f+t*t),{.78f,1.0f,.91f},aperture);
 }
 for(int i=0;i<90;i++){
  float t=10+98*seed.next(),x=(seed.next()-.5f)*1.66f,y=(seed.next()-.5f)*1.62f;
  V p=safeOrigin+lampAxis*t+lampAcross*(x*(9.4f+t*.245f))+lampThin*(y*(5.5f+t*.151f));
  float val=.035f+.18f*std::pow(seed.next(),4.f);
  if(blocked(p,safeOrigin))continue;
  depositStillGrain(plate,p,val*std::exp(-.92f*(x*x+y*y))/(1+.0004f*t*t),
           {1,.19f,.10f},.25f+.11f*seed.next());
 }
 return plate;
}

// Integrate the optical spot over each pixel. A grain moves continuously
// through a pixel boundary before the common 68-colour exposure is applied.
void pointSpread(LightPlate& plate,V p,V energy,float physicalRadius){
 Projected at=project(p);
 if(at.axial<1)return;
 float blurRadius=lensOpening*focalLength*std::abs(1/at.axial-1/focusDistance);
 float projectedRadius=focalLength*physicalRadius/at.axial;
 float sigma=std::sqrt(.33f*.33f+.25f*blurRadius*blurRadius+projectedRadius*projectedRadius);
 float inv=1/(1.41421356f*sigma);
 int x0=int(std::floor(at.x-3.2f*sigma)),x1=int(std::ceil(at.x+3.2f*sigma));
 int y0=int(std::floor(at.y-3.2f*sigma)),y1=int(std::ceil(at.y+3.2f*sigma));
 for(int y=std::max(0,y0);y<=std::min(height-1,y1);y++){
  float wy=.5f*(std::erf((y+.5f-at.y)*inv)-std::erf((y-.5f-at.y)*inv));
  for(int x=std::max(0,x0);x<=std::min(width-1,x1);x++){
   int k=y*width+x;if(firstSurface[k]+.026f<at.range)continue;
   float wx=.5f*(std::erf((x+.5f-at.x)*inv)-std::erf((x-.5f-at.x)*inv));
   float weight=wx*wy;if(weight>.0015f)plate[k]+=energy*weight;
  }
 }
}
void suspendedFiber(LightPlate& plate,V p,V tangent,V flux,float radius,float fiberLength){
 if(blocked(eye,p))return;
 tangent=norm(tangent)*(fiberLength*.38f);
 pointSpread(plate,p-tangent,flux*.24f,radius);
 pointSpread(plate,p,flux*.52f,radius);
 pointSpread(plate,p+tangent,flux*.24f,radius);
}

struct Crossing{float height,offset,heading,phase,rise,power,length;};
// Heights and offsets are fractions of the projected cone. The tracks approach
// through unlit air and leave it before the position wraps.
const std::array<Crossing,10> coolMotes={{
 {.26f,-.10f,  24,.038f, .074f,.15f,.14f},
 {.37f, .21f, 132,.412f,-.059f,.24f,.28f},
 {.43f,-.25f, -32,.714f, .066f,.15f,.12f},
 {.51f, .08f,  68,.228f,-.092f,.29f,.60f},
 {.59f,-.14f, 158,.836f, .056f,.20f,.19f},
 {.72f, .17f, -76,.549f, .102f,.20f,.12f},
 {.63f, .32f,  18,.091f,-.054f,.145f,.19f},
 {.79f,-.19f, 112,.325f,-.095f,.21f,.30f},
 {.83f, .07f, 194,.652f, .076f,.20f,.21f},
 {.69f, .04f,  38,.965f, .080f,.16f,.22f}
}};
void inEnlargerBeam(LightPlate& plate,float cycle){
 for(int i=0;i<int(coolMotes.size());i++){
  auto m=coolMotes[i];
  float slow=2*PI*cycle+.83f*i;
  float age=fract(2*cycle+m.phase+.022f*std::sin(slow));
  float s=2*age-1,angle=rad(m.heading);
  float eddy=2*PI*age+.73f*i,t=m.height+m.rise*s+.024f*std::sin(eddy)+.011f*std::sin(slow-.43f);
  float along=.93f*s,across=m.offset+.068f*std::sin(eddy)+.018f*std::sin(2*eddy+.31f);
  across+=.029f*std::sin(slow+.22f);
  float x=(along*std::cos(angle)-across*std::sin(angle))*projWidth*t;
  float y=(along*std::sin(angle)+across*std::cos(angle))*projDepth*t;
  V p=lensPos+projX*x+projY*y-V{0,0,(lensPos.z-paperLevel)*t};
  // The wake reaches the easel a little after the cloth. The air is visible
  // only while a fibre passes through the projected light of the negative.
  p+=V{1.42f,-.38f,.46f}*draft::pressure(cycle*draft::seconds-.38f-.14f*t);
  float field=.64f*lightInAir(p)+.18f*(lightInAir(p+projX*.32f)+lightInAir(p-projX*.32f));
  if(field<.008f)continue;
  // The finite lens opens into the same volume that illuminates the easel.
  float visible=0;
  V source=lensPos-V{0,0,.20f};
  for(V shift:{V{},projX*.84f,projY*.77f})visible+=transmission(p,source+shift).x/3;
  float roll=.82f+.18f*std::sin(eddy+.46f*std::sin(eddy-.68f));
  float edge=1-step(.84f,.99f,std::abs(s));
  float flux=m.power*field*visible*roll*edge/(.77f+.48f*t*t);
  if(flux<.0012f)continue;
  V tangent=projX*std::cos(angle+.42f*std::sin(eddy))+
            projY*std::sin(angle+.42f*std::sin(eddy))+V{0,0,.50f*std::sin(eddy-.45f)};
  bool longFibre=i==1||i==3||i==7;
  float radius=longFibre?.13f:.075f;
  float length=longFibre?m.length+.56f:m.length+.10f;
  suspendedFiber(plate,p,tangent,V{.82f,.97f,.90f}*(flux*(longFibre?3.05f:1.50f)),radius,length);
 }
}

struct WarmDrift{float axial,across,thin,phase,power,fiber;};
const std::array<WarmDrift,6> warmMotes={{
 {25.f,-.24f,.48f,.06f,1.58f,.87f}, {38.f,.49f,-.48f,.42f,1.46f,.70f},
 {44.f,-.22f,.48f,.72f,3.85f,1.40f}, {20.f,.66f,-.38f,.23f,.88f,.50f},
 {49.f,-.06f,-.11f,.85f,4.15f,1.56f}, {35.f,-.89f,.42f,.52f,1.12f,.58f}
}};
void inSafelight(LightPlate& plate,float cycle){
 for(int i=0;i<int(warmMotes.size());i++){
  auto m=warmMotes[i];float turn=2*PI*cycle+.91f*i;
  float age=fract((i==4?1.f:2.f)*cycle+m.phase+.025f*std::sin(turn));
  float s=2*age-1,eddy=2*PI*age+.68f*i;
  float d=m.axial+2.8f*std::sin(eddy+.31f*std::cos(turn));
  float across=(m.across+.87f*s+.09f*std::sin(eddy+turn))*(9.4f+.245f*d);
  float vertical=(m.thin+.12f*std::sin(eddy-.20f*i))*(5.5f+.151f*d);
  V p=safeOrigin+lampAxis*d+lampAcross*across+lampThin*vertical+V{0,0,s*(9.2f+.6f*i)};
  p+=lampAcross*(1.15f*std::sin(turn))+V{1.22f,-.38f,.56f}*draft::pressure(cycle*draft::seconds+.27f);
  V fromLamp=p-safeOrigin;
  float distance=dot(fromLamp,lampAxis);
  float u=dot(fromLamp,lampAcross)/(9.4f+distance*.245f);
  float v=dot(fromLamp,lampThin)/(5.5f+distance*.151f);
  float field=std::exp(-1.66f*(u*u+1.14f*v*v))/(1+.00042f*distance*distance);
  float visible=0;
  for(V delta:{V{},safeHorizontal*4.4f,-safeVertical*3.6f})visible+=transmission(p,safeOrigin+delta).x/3;
  float rotation=.76f+.24f*std::sin(eddy+.43f*std::sin(turn));
  float flux=m.power*field*visible*rotation*step(0.f,.13f,age)*(1-step(.84f,1.f,age));
  if(flux<.0012f)continue;
  V tangent=lampAcross*(.65f+.32f*std::sin(eddy))+lampThin*(.42f*std::cos(eddy))+V{0,0,.50f};
  bool nearFibre=i==2||i==4;
  suspendedFiber(plate,p,tangent,V{1,.248f,.115f}*flux,nearFibre?.22f:.115f+.025f*(i%3),m.fiber);
 }
}
LightPlate movingAir(int frame){
 LightPlate result;
 // The shutter spans the same interval as the water exposure.
 for(float offset:{-.0061f,.0061f}){
  float phase=(frame%loopFrames)/float(loopFrames)+offset/draft::seconds;
  LightPlate sample;
  inEnlargerBeam(sample,phase);inSafelight(sample,phase);
  for(auto const& [index,rgb]:sample)result[index]+=rgb*.5f;
 }
 illuminatedAir.expose(result,(frame%loopFrames)/float(loopFrames));
 return result;
}
int main(int argc,char**argv){
 if(argc!=3){std::cerr<<"air WORK MASTER\n";return 2;}
 std::string work=argv[1],master=argv[2];
 firstSurface.resize(width*height);
 std::ifstream depth(master+"/final.depth",std::ios::binary);
 depth.read(reinterpret_cast<char*>(firstSurface.data()),firstSurface.size()*sizeof(float));
 if(!depth)return 2;
 for(int i=0;i<int(plates.size());i++)plates[i].load(work+"/plate"+std::to_string(i)+".pgm");
 rinse::setTime(0);materials();makeRoom();details();woolScarf();setLights();rinse::movingGeometry();buildTree();
 lampAxis=norm(safeDirection*.78f-safeVertical*.61f-safeHorizontal*.08f);
 lampAcross=norm(cross(V{0,0,1},lampAxis));lampThin=norm(cross(lampAxis,lampAcross));
 illuminatedAir.prepare();
 std::cerr<<illuminatedAir.pixels.size()<<" pixels integrated through the open beam.\n";
 std::ofstream out(work+"/air.bin",std::ios::binary);
 out.write("AIR_SE01",8);uint32_t meta[3]={width,height,loopFrames+1};
 out.write(reinterpret_cast<char*>(meta),sizeof(meta));
 auto stillGrains=recoverStillGrains();writeLightPlate(out,stillGrains);
 for(int f=0;f<=loopFrames;f++)writeLightPlate(out,movingAir(f));
 if(!out)return 2;
 std::cerr<<"Exposed "<<loopFrames<<" moving-air frames and the return to frame zero.\n";
}
