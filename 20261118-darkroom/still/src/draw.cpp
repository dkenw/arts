#include "engine.hpp"
#include "materials.hpp"
#include "objects.hpp"
#include "room.hpp"
#include "details.hpp"
#include "muffler.hpp"

struct Lamp{V p,rx,ry,n,color;float power;bool cast;};
std::vector<Lamp> lights;
void setLights(){
 // Soft, weak return from the painted wall on the camera side opens the
 // apron of the sink without introducing another lamp.
 lights.push_back({{141,94,131},{0,38,0},{0,0,31},norm(V{-.94f,.21f,-.16f}),{.86f,.37f,.37f},1120,true});
 lights.push_back({safeOrigin,safeHorizontal*8.2f,safeVertical*8.2f,safeDirection,{1,.139f,.074f},33900,true});
 // Diffuse spill reflected from the plaster and from the illuminated paper.
 lights.push_back({{-129,151,168},{0,15,0},{0,0,15},norm(V{1,.05f,-.32f}),{1,.24f,.13f},1780,false});
 lights.push_back({{-99,63,151},{0,26,0},{0,0,20},norm(V{.51f,.76f,-.30f}),{1,.23f,.15f},1720,true});
 // Low luminous spill from the red glass back onto its mounting wall.
 lights.push_back({{-119,151,161},{0,8,0},{0,0,7},norm(V{-.94f,-.18f,-.23f}),{1,.115f,.045f},630,false});
 lights.push_back({{15,159,92.7f},{12.5f,0,0},{0,9.4f,0},{0,0,1},{.72f,.96f,1.08f},930,true});
 // Low, broad secondary reflection from the illuminated tiles beside the wash.
 lights.push_back({{-118,82,124},{0,25,0},{0,0,18},norm(V{.91f,-.10f,.20f}),{1,.22f,.13f},1180,true});
 lights.push_back({{-57,202,135},{34,0,0},{0,0,21},{0,-1,0},{1,.16f,.11f},580,false});
}
float filmTransmission(float u,float v){
 float along=fract(u*4.3f);
 if(v<=.12f||v>=.88f||along<=.04f||along>=.95f)return .23f;
 float positive=plates[filmFrames[int(u*4.3f)%4]].get(along,(v-.12f)/.76f);
 return .14f+.75f*std::pow(1-positive,1.36f);
}
bool transparentToLight(Pattern kind){return washerBoundary(kind)||kind==Water||kind==ClearWater||kind==Film||kind==BubbleFilm;}
V transmission(V p,V to){
 V delta=to-p;float remaining=len(delta)-.075f;V dir=norm(delta);
 if(remaining<=0)return {1,1,1};
 Hit any;any.t=remaining;
 if(!trace(Ray(p,dir),any,true))return {1,1,1};
 if(!transparentToLight(mats[tris[any.id].mat].kind))return {};
 // The fast any-hit traversal can return glass before another occluder.
 // Resolve transparent crossings in distance order and keep opaque shadows.
 V passed{1,1,1};
 for(int layer=0;layer<12&&remaining>.016f;layer++){
  Hit h;h.t=remaining;if(!trace(Ray(p,dir),h))break;
  const Tri& tri=tris[h.id];Pattern k=mats[tri.mat].kind;
  if(!transparentToLight(k))return {};
  float w=1-h.u-h.v;
  if(k==Film){
   float u=tri.a.u*w+tri.b.u*h.u+tri.c.u*h.v,v=tri.a.v*w+tri.b.v*h.u+tri.c.v*h.v;
   passed=passed*V{.83f,.60f,.48f}*filmTransmission(u,v);
  }else{
   V n=norm(tri.na*w+tri.nb*h.u+tri.nc*h.v);
   float cosine=std::min(1.f,std::abs(dot(n,dir)));
   float fres=.0204f+.9796f*std::pow(1-cosine,5.f);
   passed=passed*(1-fres)*V{.99f,.994f,.995f};
  }
  float stepSize=h.t+.023f;p+=dir*stepSize;remaining-=stepSize;
 }
 return passed;
}
bool blocked(V p,V to){return transmission(p,to).x<.016f;}
float safeDistribution(V incoming){
 float elevation=dot(-incoming,safeVertical),lateral=dot(-incoming,safeHorizontal);
 float distribution=(1-.48f*step(.40f,.88f,elevation))*(1-.39f*step(.58f,.95f,lateral));
 return distribution*(1-.30f*step(.06f,.35f,lateral)*(1-step(.14f,.46f,elevation)));
}
#include "basinlight.hpp"
#include "waterlight.hpp"
float negativeTransmission(float u,float v){
 if(u<0||u>1||v<0||v>1)return 0;
 float positive=plates[0].get(.5f+(v-.5f)*.907f,1-u);
 float clear=.013f+.975f*std::pow(1-positive,2.12f);
 return clear*step(0,.009f,std::min({u,1-u,v,1-v}));
}
float coneLight(V p){
 float z=lensPos.z-p.z;if(z<=0)return 0;
 float t=z/(lensPos.z-paperLevel);
 return negativeTransmission(.5f+dot(p-lensPos,projX)/(projWidth*t),
                             .5f-dot(p-lensPos,projY)/(projDepth*t));
}
// Rays from different parts of the lens coincide on the easel. Suspended
// dust above it sees a mixture of those rays, especially close to the lens.
constexpr float lensRadius=2.42f;
float lightInAir(V p){
 static const std::array<UV,16> aperture=[](){
  std::array<UV,16> points{};
  for(int k=0;k<int(points.size());k++){
   float theta=2.39996323f*k, radius=lensRadius*std::sqrt((k+.5f)/points.size());
   points[k]={radius*std::cos(theta),radius*std::sin(theta)};
  }
  return points;
 }();
 float t=(lensPos.z-p.z)/(lensPos.z-paperLevel);
 if(t<=0||t>=1)return 0;
 float x=dot(p-lensPos,projX),y=dot(p-lensPos,projY),sum=0;
 for(UV q:aperture){
  float u=.5f+(x-(1-t)*q.u)/(projWidth*t);
  float v=.5f-(y-(1-t)*q.v)/(projDepth*t);
  if(u<0||v<0||u>1||v>1)continue;
  sum+=.068f+.932f*negativeTransmission(u,v);
 }
 return sum/aperture.size();
}
float beam(const Ray&r,float end){
 float lo=.02f,hi=end,h=lensPos.z-paperLevel;
 auto clip=[&](float a,float slope){if(std::abs(slope)<1e-8)return a>=0;
  float x=-a/slope;if(slope>0)lo=std::max(lo,x);else hi=std::min(hi,x);return hi>lo;};
 if(!clip(r.o.z-paperLevel,r.d.z)||!clip(lensPos.z-.10f-r.o.z,-r.d.z))return 0;
 for(int k=0;k<2;k++)for(int s:{-1,1}){
  float width=((k?projDepth:projWidth)*.5f-lensRadius)/h;
  V axis=k?projY:projX;
  if(!clip(lensRadius+(lensPos.z-r.o.z)*width+s*dot(r.o-lensPos,axis),-r.d.z*width+s*dot(r.d,axis)))return 0;
 }
 float sum=0;
 for(int i=0;i<10;i++){V p=r.o+r.d*mix(lo,hi,(i+.5f)/10);
  float rise=sat((p.z-paperLevel)/h),rho=.45f+.63f*noise(p.x*.095f+p.z*.040f,p.y*.082f-p.z*.025f,92);
  sum+=lightInAir(p)*rho*(.77f+.87f*rise);
 }
 return (hi-lo)*sum/10*.0073f;
}
V background(V d){return {.013f+.007f*std::max(0.f,d.z),.012f,.024f};}
struct Radiance{V color;float depth;int mat;};
Radiance renderRay(const Ray&r,RNG&rng,int bounce,int samples){
 Hit h;if(!trace(r,h))return{background(r.d),9999,-1};const Tri&t=tris[h.id];float w=1-h.u-h.v;
 V p=r.o+r.d*h.t,n=norm(t.na*w+t.nb*h.u+t.nc*h.v);if(dot(n,r.d)>0)n=-n;
 float u=t.a.u*w+t.b.u*h.u+t.c.u*h.v,v=t.a.v*w+t.b.v*h.u+t.c.v*h.v;
 Surface s=surface(t.mat,p,n,u,v);n=s.n;if(dot(n,r.d)>0)n=-n;
 V output=s.emit,base=s.base,origin=p+n*.045f;
 float ao=1;
 if(bounce==0){
  V a=norm(cross(std::abs(n.z)>.89f?V{0,1,0}:V{0,0,1},n)),b=cross(n,a);float openness=0;
  int rays=samples>3?2:1;
  for(int j=0;j<rays;j++){float phi=2*PI*rng.next(),co=std::sqrt(.15f+.85f*rng.next()),si=std::sqrt(1-co*co);
   V direction=norm(n*co+(a*std::cos(phi)+b*std::sin(phi))*si);Hit occ;occ.t=30;
   if(trace(Ray(origin,direction),occ))openness+=.24f+.76f*step(0,30,occ.t);else openness+=1;
  }ao=.40f+.60f*openness/rays;
 }
 float hemi=.54f+.46f*(n.z*.5f+.5f);
 V ambient=V{.014f,.0165f,.029f}*(ao*hemi);
 // Indirect, cool paper light lifts the bellows. Its rectangular source also
 // appears in nearby metal because mirror rays see the same illuminated board.
 output+=base*ambient;
 if(p.y>215.0f&&p.z>98.f&&n.y<-.50f){
  Pattern m=mats[t.mat].kind;
  if(m==Plaster||m==Tile||m==Porcelain){
   float flux=waterLight.lookup(p);
   output+=base*V{1.0f,.149f,.071f}*flux;
  }
 }
 V view=-r.d;float ndv=std::max(.001f,dot(n,view));
 int iLight=0;
 for(const Lamp&L:lights){
  V center=L.p-p;float dist2=dot(center,center);
  if(dist2>260000){iLight++;continue;}
  float ndc=dot(n,norm(center));if(ndc<-.19f){iLight++;continue;}
  int count=bounce==0&&iLight==1?(samples>2?3:2):1;V acc{};
  for(int j=0;j<count;j++){
   float a=(j+rng.next())/count,b=rng.next();V target=L.p+L.rx*(a*2-1)+L.ry*(b*2-1);
   V delta=target-p;float d2=dot(delta,delta);V l=delta/std::sqrt(d2);
   float nl=std::max(0.f,dot(n,l)),emit=std::max(0.f,dot(L.n,-l));if(nl<=0||emit<=0)continue;
   V filter=L.cast?transmission(origin,target):V{1,1,1};if(filter.x<.008f)continue;
   // The sheet-metal visor and ribbed glass direct the safelight down the wet side.
   float distribution=1;
   if(iLight==1){
    distribution=safeDistribution(l);
   }
   float power=L.power*emit*distribution/(d2+90);
   V half=norm(view+l);float exponent=4+270*std::pow(1-s.rough,3.4f);
   bool alloy=mats[t.mat].kind==Brushed;
   float sheen=std::pow(std::max(0.f,dot(n,half)),exponent*(alloy?.77f:1.f))*(.025f+(alloy?3.10f:1.90f)*s.mirror+.052f*(1-s.rough))*std::min(1.f,nl*3.0f);
   if(mats[t.mat].kind==Picture)sheen*=.43f;
   if(mats[t.mat].kind==Flock)sheen*=.012f;
   if(mats[t.mat].kind==MufflerWool||mats[t.mat].kind==Yarn)sheen*=.095f;
   if(mats[t.mat].kind==BlackoutCotton)sheen*=.13f;
   acc+=(base*nl+V{sheen,sheen,sheen})*filter*L.color*power;
  }
  output+=acc*(1.f/count);iLight++;
 }
 if(p.z>68.9f && p.z<81.81f && p.y>16.f && p.y<76.f
    && p.x>-123.f && p.x<15.f && n.z>.06f && mats[t.mat].kind==Brushed){
  float correction=.85f*basinLight.lookup(p)*n.z;
  output+=base*lights[1].color*correction;
  output=max3(output,{0,0,0});
 }
 float proj=coneLight(p);
 if(proj>.001f){V d=lensPos-p,l=norm(d);if(dot(n,l)>0&&!blocked(origin,lensPos-V{0,0,.13f})){
  float E=2.20f*proj*std::pow((lensPos.z-paperLevel)/std::max(6.f,len(d)),2)*dot(n,l);
  output+=base*V{.79f,1.01f,1.02f}*E;
 }}
 bool water=t.mat==liquid;
 bool tank=washerBoundary(mats[t.mat].kind);
 bool clear=tank||mats[t.mat].kind==ClearWater;
 if(bounce<2&&(water||clear||(s.mirror>.050f&&bounce==0))){
  V mirror=norm(r.d-n*(2*dot(r.d,n)));V a=norm(cross(std::abs(mirror.z)>.89f?V{0,1,0}:V{0,0,1},mirror)),b=cross(mirror,a);
  float fuzz=water?.006f:s.rough*s.rough*.32f;
  V reflected=norm(mirror+a*((rng.next()-.5f)*fuzz)+b*((rng.next()-.5f)*fuzz));
  if(dot(reflected,n)<=0)reflected=mirror;
  float fres=std::pow(1-ndv,4.f);
  float refl=water?.045f+.78f*fres:std::min(.83f,s.mirror*(.71f+.57f*fres));
  V reflectedLight=renderRay(Ray(origin,reflected),rng,bounce+1,samples).color;
  if(water){
   float eta=1/1.333f,cosi=-dot(n,r.d),k=1-eta*eta*(1-cosi*cosi);
   V refr=norm(r.d*eta+n*(eta*cosi-std::sqrt(std::max(0.f,k))));
   V below=renderRay(Ray(p-n*.024f,refr),rng,bounce+1,samples).color;
   // The open sink reflects the visible safelight in its actual direction.
   // Between crests the eye sees the dark steel and the submerged print.
   float fwater=.0204f+.9796f*std::pow(1-ndv,5.f);
   output=output*.14f+(below*V{.86f,.86f,.85f})*(1-fwater)+reflectedLight*fwater;
  }else if(clear){
   // Resolve the entry and exit through a dielectric volume. The wash tank
   // can contain submerged wirework between its two boundary crossings.
   const float index=tank?1.338f:1.333f;
   float ci=-dot(n,r.d),eta=1/index;
   V inside=norm(r.d*eta+n*(eta*ci-std::sqrt(std::max(0.f,1-eta*eta*(1-ci*ci)))));
   V enter=p-n*.007f; Hit back; back.t=tank?86.0f:3.7f;
   V through=reflectedLight;
   bool hitFar=trace(Ray(enter,inside),back);
   if(hitFar&&(tris[back.id].mat==t.mat||(tank&&washerBoundary(mats[tris[back.id].mat].kind)))){
    const auto& far=tris[back.id]; V pos=enter+inside*back.t;
    V exitNormal=norm(far.na*(1-back.u-back.v)+far.nb*back.u+far.nc*back.v);
    if(dot(exitNormal,inside)>0)exitNormal=-exitNormal;
    float ce=-dot(exitNormal,inside),q=1-index*index*(1-ce*ce);
    if(q>=0){V out=norm(inside*index+exitNormal*(index*ce-std::sqrt(q)));
     through=renderRay(Ray(pos-exitNormal*.018f,out),rng,bounce+1,samples).color;}
   }
   if(tank&&hitFar){
    // Interior wires shade as wet metal. Slight attenuation depends on the
    // distance the ray actually travelled through the tank.
    if(!washerBoundary(mats[tris[back.id].mat].kind))
     through=renderRay(Ray(enter,inside),rng,bounce+1,samples).color;
    through=through*V{std::exp(-.0036f*back.t),std::exp(-.0022f*back.t),std::exp(-.0019f*back.t)};
   }
   float f=.022f+.978f*std::pow(1-ndv,5.f);
   output=output*.36f+through*(1-f)+reflectedLight*f;
  }else output=output*(1-.28f*refl)+reflectedLight*refl;
 }
 if(mats[t.mat].kind==BubbleFilm && bounce<2){
  // A water film around air has two reflecting interfaces. The direction
  // through this thin layer is effectively straight.
  float fresnel=.0204f+.9796f*std::pow(1-ndv,5.f);
  float filmReflection=2*fresnel/(1+fresnel);
  V reflected=norm(r.d-n*(2*dot(r.d,n)));
  V sky=renderRay(Ray(origin,reflected),rng,bounce+1,samples).color;
  V waterUnder=renderRay(Ray(p+r.d*.026f,r.d),rng,bounce+1,samples).color;
  output=mix(waterUnder,sky,filmReflection)+.031f*output;
 }
 if(mats[t.mat].kind==Film && bounce<2){
  float dye=filmTransmission(u,v);
  V daylight=renderRay(Ray(p+r.d*.029f,r.d),rng,bounce+1,samples).color;
  output=output*.40f+daylight*V{.83f,.60f,.48f}*dye;
 }
 if(bounce==0){float dust=beam(r,h.t);output+=V{.78f,.88f,.82f}*dust;}
 return {output,h.t,t.mat};
}
#include "atmosphere.hpp"

int main(int argc,char**argv){
 if(argc<4){std::cerr<<"usage: draw work-directory width samples [stem]\n";return 2;}
 std::string root=argv[1],stem=argc>4?argv[4]:"render";
 int W=std::atoi(argv[2]),H=std::round(W*304.f/528),spp=std::atoi(argv[3]);
 for(int i=0;i<int(plates.size());i++)plates[i].load(root+"/plate"+std::to_string(i)+".pgm");
 materials();makeRoom();details();woolScarf();setLights();
 if(mats.size()>256){std::cerr<<"Too many materials for the material index buffer.\n";return 2;}
 buildTree();waterLight.bake();basinLight.bake();
 std::cerr<<tris.size()<<" triangles, "<<W<<" x "<<H<<" at "<<spp<<" samples\n";
 std::vector<float> rgb(W*H*3),depth(W*H);std::vector<unsigned char> id(W*H);
 V eye{91,-63,146},target{-18,158,113.7f};float focalScale=404;
 V forward=norm(target-eye),right=norm(cross(forward,{0,0,1})),up=cross(right,forward);
 float focal=W*focalScale/528;std::atomic<int> scan{0};
 auto draw=[&](){
  for(;;){int y=scan.fetch_add(1);if(y>=H)break;
   for(int x=0;x<W;x++){int idx=y*W+x;V col{};uint32_t seed=hash32(idx+401);
    int side=std::ceil(std::sqrt(float(spp)));
    for(int j=0;j<spp;j++){RNG rng(hash32(seed+0x9e3779b9u*(j+1)));
     float ax=spp==1?.5f:(j%side+.16f+.68f*rng.next())/side;
     float ay=spp==1?.5f:(j/side+.16f+.68f*rng.next())/side;
     V d=norm(forward+right*((x+ax-W*.5f)/focal)+up*((H*.5f-y-ay)/focal));
     V lensEye=eye;
     if(spp>=4){float ang=2*PI*rng.next(),rr=.43f*std::sqrt(rng.next());
      lensEye+=right*(rr*std::cos(ang))+up*(rr*std::sin(ang));
      V focus=eye+d*(218.f/dot(d,forward));d=norm(focus-lensEye);}
     auto answer=renderRay(Ray(lensEye,d),rng,0,spp);col+=answer.color;
     if(j==0){id[idx]=std::max(0,answer.mat);depth[idx]=answer.depth;}
    }col=col/spp;rgb[idx*3]=col.x;rgb[idx*3+1]=col.y;rgb[idx*3+2]=col.z;
   }
  }
 };
 std::vector<std::thread> jobs;for(int i=0;i<5;i++)jobs.emplace_back(draw);draw();for(auto&j:jobs)j.join();
 airInTheLight(rgb,depth,W,H,eye,forward,right,up,focal);
 auto save=[&](std::string ext,const void*p,size_t n){std::ofstream o(root+"/"+stem+ext,std::ios::binary);o.write((const char*)p,n);};
 std::vector<unsigned char> role(mats.size(),0);
 for(size_t i=0;i<mats.size();i++){
  auto k=mats[i].kind;
  if(k==Picture||k==Sticker||k==FullImage||k==Paper||k==Dial||k==Porcelain||i==size_t(cream)||i==size_t(offwhite))role[i]=1;
  if(k==Brushed||k==Water||k==ClearWater||k==BubbleFilm||washerBoundary(k))role[i]=2;
  if(k==Picture)role[i]=3;
  if(k==Tile||k==Plaster)role[i]=4;
  if(k==MufflerWool||k==Yarn)role[i]=5;
  if(k==BlackoutCotton)role[i]=6;
  if(mats[i].hanging)role[i]=7;
 }
 save(".roles",role.data(),role.size());
 save(".rgb",rgb.data(),rgb.size()*sizeof(float));save(".depth",depth.data(),depth.size()*sizeof(float));save(".id",id.data(),id.size());
 std::ofstream meta(root+"/"+stem+".txt");meta<<W<<" "<<H<<" "<<safelens<<" "<<whiteLight<<" "<<liquid<<"\n";
 return 0;
}
