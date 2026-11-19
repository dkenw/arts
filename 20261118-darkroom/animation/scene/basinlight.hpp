#pragma once
// Conservative photon splats from four parts of the safelight aperture.
// The receiving bath is a heightfield sampled from the actual steel mesh.
struct BasinLight {
 static constexpr float left=-124.f,front=15.5f,pitch=.50f;
 static constexpr int cols=282,rows=125,size=cols*rows,areaSamples=4;
 struct Entry {V l{};float flux=0;};
 std::vector<Entry> incident;
 std::vector<float> receiver,heights,difference;
 std::vector<unsigned char> wet;
 float sample(const std::vector<float>& grid,float x,float y,float outside) const {
  float fx=(x-left)/pitch,fy=(y-front)/pitch;int i=std::floor(fx),j=std::floor(fy);
  if(i<0||j<0||i>=cols-1||j>=rows-1)return outside;
  int k=j*cols+i;
  return mix(mix(grid[k],grid[k+1],fx-i),mix(grid[k+cols],grid[k+cols+1],fx-i),fy-j);
 }
 void prepare(){
  incident.resize(size*areaSamples);receiver.assign(size,84.f);heights.assign(size,rinse::level);
  wet.assign(size,0);difference.assign(size,0);
  for(int j=0;j<rows;j++)for(int i=0;i<cols;i++){
   int k=j*cols+i;float x=left+i*pitch,y=front+j*pitch;
   Hit steelHit;steelHit.t=25;
   if(trace(Ray({x,y,82.65f},{0,0,-1}),steelHit))receiver[k]=82.65f-steelHit.t;
   float qx=std::max(0.f,std::abs(x+53.5f)-62.75f),qy=std::max(0.f,std::abs(y-46)-22.95f);
   if(qx*qx+qy*qy>5.2f*5.2f)continue;
   wet[k]=1;const Lamp &lamp=lights[1];V p{x,y,rinse::level+.08f};
   for(int a=0;a<areaSamples;a++){
    float u=(a%2+.5f)/2,v=(a/2+.5f)/2;
    V target=lamp.p+lamp.rx*(2*u-1)+lamp.ry*(2*v-1),delta=target-p;
    V l=norm(delta);
    float visible=transmission(p,target).x;
    incident[k*areaSamples+a]={l,lamp.power*std::max(0.f,dot(lamp.n,-l))*safeDistribution(l)*visible/
                               ((dot(delta,delta)+90)*areaSamples)};
   }
  }
 }
 void transport(V p,V l,V n,float flux){
  const float eta=1/1.333f,c=dot(l,n);
  if(c<.05f)return;
  V d=-l*eta+n*(eta*c-std::sqrt(1-eta*eta*(1-c*c)));
  float z=sample(receiver,p.x,p.y,84);
  V at=p;
  for(int iteration=0;iteration<3;iteration++){
   float dist=(z-p.z)/d.z;
   if(dist<0)return;
   at=p+d*dist;z=sample(receiver,at.x,at.y,84);
  }
  if(z>81.73f)return;
  // Stop light which meets the print on its way down to the steel.
  float dist=std::clamp((rinse::level-p.z)/d.z,0.f,2.f);
  V cross=p+d*dist;
  float dx=cross.x-rinse::paperX,dy=cross.y-rinse::paperY;
  float u=.5f+(dx*rinse::paperCos+dy*rinse::paperSin)/rinse::paperW;
  float v=.5f-(-dx*rinse::paperSin+dy*rinse::paperCos)/rinse::paperH;
  if(u>=0&&u<=1&&v>=0&&v<=1)return;
  float x=(at.x-left)/pitch,y=(at.y-front)/pitch;int i=std::floor(x),j=std::floor(y);
  if(i<0||j<0||i>=cols-1||j>=rows-1)return;
  float a=x-i,b=y-j,schlick=.0204f+.9796f*std::pow(1-c,5.f);
  float amount=flux*c*(1-schlick)/n.z;int k=j*cols+i;
  difference[k]+=amount*(1-a)*(1-b);difference[k+1]+=amount*a*(1-b);
  difference[k+cols]+=amount*(1-a)*b;difference[k+cols+1]+=amount*a*b;
 }
 void bake(){
  if(incident.empty())prepare();
  std::fill(difference.begin(),difference.end(),0);
  for(int j=0;j<rows;j++)for(int i=0;i<cols;i++)
   heights[j*cols+i]=rinse::height(left+i*pitch,front+j*pitch);
  for(int j=1;j<rows-1;j++)for(int i=1;i<cols-1;i++){
   int k=j*cols+i;if(!wet[k])continue;
   V p{left+i*pitch,front+j*pitch,heights[k]};
   V n=norm(V{heights[k-1]-heights[k+1],heights[k-cols]-heights[k+cols],2*pitch});
   for(int a=0;a<areaSamples;a++){
    const auto &e=incident[k*areaSamples+a];if(e.flux<.002f)continue;
    transport(p,e.l,n,e.flux);transport(p,e.l,{0,0,1},-e.flux);
   }
  }
  auto raw=difference;
  for(int j=1;j<rows-1;j++)for(int i=1;i<cols-1;i++){
   int k=j*cols+i;difference[k]=(4*raw[k]+2*(raw[k-1]+raw[k+1]+raw[k-cols]+raw[k+cols])+
                         raw[k-cols-1]+raw[k-cols+1]+raw[k+cols-1]+raw[k+cols+1])/16;
  }
 }
 float lookup(V p)const{return sample(difference,p.x,p.y,0);}
} basinLight;
