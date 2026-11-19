#pragma once
// A forward light pass. A small parcel of the wash water reflects a share of
// the safelight's flux onto the wall. Its footprint is determined by the
// law of reflection and by actual obstacles between source, water and wall.
struct ReflectedWashLight{
 static constexpr float cell=.90f,xMin=-140,zMin=98.0f;
 static constexpr int nx=200,nz=145;
 std::vector<float> map=std::vector<float>(nx*nz,0);
 void splat(float x,float z,float energy){
  float u=(x-xMin)/cell,v=(z-zMin)/cell;
  int i=std::floor(u),j=std::floor(v);
  if(i<0||i>=nx-1||j<0||j>=nz-1)return;
  for(int b=0;b<=1;b++)for(int a=0;a<=1;a++)
   map[(j+b)*nx+i+a]+=energy*(a?u-i:1.f-u+i)*(b?v-j:1.f-v+j);
 }
 float lookup(V p) const{
  float u=(p.x-xMin)/cell,v=(p.z-zMin)/cell;
  int i=std::floor(u),j=std::floor(v);
  if(i<0||i>=nx-1||j<0||j>=nz-1)return 0;
  return mix(mix(map[j*nx+i],map[j*nx+i+1],u-i),
             mix(map[(j+1)*nx+i],map[(j+1)*nx+i+1],u-i),v-j);
 }
 void bake(){
  constexpr float X=23.8f,Y=10.5f,ds=.38f;
  // The ribbed lamp has an extended luminous disk and a smaller, hotter
  // filament. Sampling both gives a soft envelope and sharper little folds.
  constexpr int grains=24;
  for(float x=-X+.48f;x<X-.35f;x+=ds)for(float y=-Y+.46f;y<Y-.35f;y+=ds){
   V p=washerPose.pos({x,y,washerLevel+washerWave(x,y)});
   float dx=(washerWave(x+.04f,y)-washerWave(x-.04f,y))/.08f;
   float dy=(washerWave(x,y+.04f)-washerWave(x,y-.04f))/.08f;
   V n=norm(washerPose.dir({-dx,-dy,1}));
   RNG seed(hash32((unsigned)std::lround((x+X)*100)*1021u+(unsigned)std::lround((y+Y)*100)*2053u));
   for(int k=0;k<grains;k++){
    float phi=2*PI*(k+seed.next())/grains;
    float radius=std::sqrt(seed.next())*(k%3?6.65f:1.61f);
    V bulb=safeOrigin+safeHorizontal*(radius*std::cos(phi))+safeVertical*(radius*std::sin(phi));
    V incident=p-bulb;float d2=dot(incident,incident);incident=norm(incident);
    float incidence=-dot(incident,n),sourceCos=dot(incident,safeDirection);
    if(incidence<=0||sourceCos<=0)continue;
    V outgoing=incident+n*(2*incidence);
    if(outgoing.y<=.06f||outgoing.z<=0)continue;
    V start=p+n*.11f;
    V path=transmission(start,bulb);if(path.x<.01f)continue;
    Hit hit;hit.t=260.f;
    if(!trace(Ray(start,outgoing),hit))continue;
    V target=start+outgoing*hit.t;
    if(target.y<215.1f||target.z<zMin||target.z>229.f)continue;
    auto material=mats[tris[hit.id].mat].kind;
    if(material!=Plaster&&material!=Tile&&material!=Porcelain)continue;
    float cosWater=.0206f+.9794f*std::pow(1-incidence,5.f);
    float flux=33900.f*sourceCos*incidence*cosWater*path.x/(d2+90.f);
    splat(target.x,target.z,flux*ds*ds/(cell*cell*grains));
   }
  }
  float total=0,peak=0;for(float v:map){peak=std::max(peak,v);total+=v;}
  std::cerr<<"Reflected wash light: wall energy "<<total*cell*cell<<", peak "<<peak<<"\n";
 }
} waterLight;
